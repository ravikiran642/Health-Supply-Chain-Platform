from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.audit import AuditLog, AuditActionEnum, AuditResultEnum
from app.models.geography import District


# Helper function to obtain auth header
def get_auth_header(client: TestClient, email: str, password: str = "Test@123") -> dict:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Login with valid credentials → 200 + tokens returned
def test_login_valid_credentials(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"email": "superadmin@hsc.gov.in", "password": "Test@123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "superadmin@hsc.gov.in"
    assert "manage_users" in data["user"]["permissions"]


# 2. Login with invalid credentials → 401
def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"email": "superadmin@hsc.gov.in", "password": "WrongPassword!99"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


# 3. Access protected endpoint without token → 401
def test_access_protected_without_token(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code == 401


# 4. Access protected endpoint with expired token → 401
def test_access_protected_with_expired_token(client: TestClient, seeded_db: Session):
    expired_token = create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        expires_delta=timedelta(minutes=-10)
    )
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401


# 5. PHC Operator tries to approve request → 403
def test_phc_operator_approve_forbidden(client: TestClient):
    operator_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    response = client.post(
        "/auth/test/approve-phc-request",
        headers=operator_headers
    )
    assert response.status_code == 403
    assert "missing 'approve_phc_request' permission" in response.json()["detail"]

    # Conversely, PHC Approver succeeds (200)
    approver_headers = get_auth_header(client, "phc.approver.pat@hsc.gov.in")
    appr_resp = client.post(
        "/auth/test/approve-phc-request",
        headers=approver_headers
    )
    assert appr_resp.status_code == 200


# 6. District Approver from Ramgarh tries to access Ranchi data → 403
def test_cross_district_access_forbidden(client: TestClient, seeded_db: Session):
    ranchi_dist = seeded_db.query(District).filter_by(name="Ranchi").first()
    assert ranchi_dist is not None

    ramgarh_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in")
    response = client.get(
        f"/auth/test/district-data/{ranchi_dist.id}",
        headers=ramgarh_headers
    )
    assert response.status_code == 403
    assert "Cannot access data from a different district" in response.json()["detail"]


# 7. Super Admin can access all endpoints → 200
def test_super_admin_bypass_all_endpoints(client: TestClient, seeded_db: Session):
    ranchi_dist = seeded_db.query(District).filter_by(name="Ranchi").first()
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")

    # Accesses PHC approval endpoint
    resp1 = client.post(
        "/auth/test/approve-phc-request",
        headers=admin_headers
    )
    assert resp1.status_code == 200

    # Accesses any district's data regardless of scope
    resp2 = client.get(
        f"/auth/test/district-data/{ranchi_dist.id}",
        headers=admin_headers
    )
    assert resp2.status_code == 200
    assert resp2.json()["bypassed"] is True


# 8. Refresh token flow → new access token issued
def test_refresh_token_flow(client: TestClient):
    login_resp = client.post(
        "/auth/login",
        json={"email": "superadmin@hsc.gov.in", "password": "Test@123"}
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()
    assert "access_token" in new_data

    # Use new access token to query /auth/me
    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {new_data['access_token']}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "superadmin@hsc.gov.in"


# 9. Logout revokes refresh token → refresh fails after logout
def test_logout_revokes_token(client: TestClient):
    login_resp = client.post(
        "/auth/login",
        json={"email": "superadmin@hsc.gov.in", "password": "Test@123"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Logout
    logout_resp = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True

    # Attempting to refresh with revoked token fails with 401
    refresh_retry = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_retry.status_code == 401
    assert "Refresh token is invalid, revoked, or expired" in refresh_retry.json()["detail"]


# 10. Permission denied event is written to audit_logs
def test_permission_denied_audit_logging(client: TestClient, seeded_db: Session):
    # Trigger permission denial with operator
    operator_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    denied_resp = client.post(
        "/auth/test/approve-phc-request",
        headers=operator_headers
    )
    assert denied_resp.status_code == 403

    # Inspect audit_logs table
    audit_entry = (
        seeded_db.query(AuditLog)
        .filter_by(
            action=AuditActionEnum.PERMISSION_DENIED.value,
            result=AuditResultEnum.DENIED
        )
        .order_by(AuditLog.timestamp.desc())
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.resource_id == "approve_phc_request"
