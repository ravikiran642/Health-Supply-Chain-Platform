import uuid
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.audit import AuditLog, AuditActionEnum, AuditResultEnum
from app.models.geography import State, District, Facility
from app.models.user import User, ScopeLevelEnum


def get_auth_header(client: TestClient, email: str, password: str = "Test@123") -> dict:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Super Admin lists users with pagination and filters
def test_super_admin_list_users(client: TestClient):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")

    # List all users
    response = client.get("/users?page=1&page_size=10", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 5
    assert len(data["items"]) >= 5

    # Filter by scope_level=district
    resp_scope = client.get("/users?scope_level=district", headers=admin_headers)
    assert resp_scope.status_code == 200
    for u in resp_scope.json()["items"]:
        assert u["scope_level"] == "district"

    # Filter by role="PHC Operator"
    resp_role = client.get("/users?role=PHC Operator", headers=admin_headers)
    assert resp_role.status_code == 200
    for u in resp_role.json()["items"]:
        role_names = [r["name"] for r in u["roles"]]
        assert "PHC Operator" in role_names

    # Filter by search
    resp_search = client.get("/users?search=Ramgarh", headers=admin_headers)
    assert resp_search.status_code == 200
    assert any("Ramgarh" in u["full_name"] for u in resp_search.json()["items"])


# 2. Non-super admin cannot list or view users → 403
def test_non_admin_cannot_access_users(client: TestClient):
    operator_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")

    resp_list = client.get("/users", headers=operator_headers)
    assert resp_list.status_code == 403
    assert "missing 'view_users' permission" in resp_list.json()["detail"]


# 3. Super Admin creates a new user successfully
def test_super_admin_create_user_success(client: TestClient, seeded_db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    dist = seeded_db.query(District).filter_by(name="Ramgarh").first()
    assert dist is not None

    payload = {
        "email": "new.district.user@hsc.gov.in",
        "full_name": "New District Officer",
        "password": "SecurePassword1!",
        "phone": "+919876543210",
        "scope_level": "district",
        "scope_id": str(dist.id),
        "role_names": ["District Approver"]
        "role_names": ["District Approver"]
    }
    response = client.post("/users", json=payload, headers=admin_headers)
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["email"] == "new.district.user@hsc.gov.in"
    assert created_user["phone"] == "+919876543210"
    assert created_user["scope_level"] == "district"
    assert created_user["scope_id"] == str(dist.id)
    assert any(r["name"] == "District Approver" for r in created_user["roles"])

    # Audit log created without PII
    audit = (
        seeded_db.query(AuditLog)
        .filter_by(action="create_user")
        .order_by(AuditLog.timestamp.desc())
        .first()
    )
    assert audit is not None
    assert audit.resource_id == created_user["id"]
    if audit.metadata_:
        assert "email" not in str(audit.metadata_)
        assert "phone" not in str(audit.metadata_)


# 4. User creation validations: duplicate email, weak password, invalid scope
def test_create_user_validations(client: TestClient, seeded_db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    dist = seeded_db.query(District).filter_by(name="Ramgarh").first()
    assert dist is not None

    # Duplicate email
    dup_payload = {
        "email": "superadmin@hsc.gov.in",
        "full_name": "Duplicate Admin",
        "password": "SecurePassword1!",
        "scope_level": "platform",
        "role_names": ["Super Admin"]
    }
    resp_dup = client.post("/users", json=dup_payload, headers=admin_headers)
    assert resp_dup.status_code == 400
    assert "already registered" in resp_dup.json()["detail"]

    # Weak password (no digits)
    weak_payload = {
        "email": "weak.user@hsc.gov.in",
        "full_name": "Weak User",
        "password": "passwordonly",
        "scope_level": "platform",
        "role_names": ["Super Admin"]
    }
    resp_weak = client.post("/users", json=weak_payload, headers=admin_headers)
    assert resp_weak.status_code == 422

    # District scope missing scope_id
    missing_scope_payload = {
        "email": "missing.scope@hsc.gov.in",
        "full_name": "Missing Scope",
        "password": "SecurePassword1!",
        "scope_level": "district",
        "role_names": ["District Approver"]
    }
    resp_missing = client.post("/users", json=missing_scope_payload, headers=admin_headers)
    assert resp_missing.status_code == 400
    assert "scope_id is required" in resp_missing.json()["detail"]

    # Platform scope with non-null scope_id
    invalid_platform_payload = {
        "email": "invalid.platform@hsc.gov.in",
        "full_name": "Invalid Platform",
        "password": "SecurePassword1!",
        "scope_level": "platform",
        "scope_id": str(dist.id),
        "role_names": ["Super Admin"]
    }
    resp_invalid_platform = client.post("/users", json=invalid_platform_payload, headers=admin_headers)
    assert resp_invalid_platform.status_code == 400
    assert "scope_id must be None" in resp_invalid_platform.json()["detail"]

        # Multi-role assignment rejected (exactly one enforced) → 422
    multi_role_payload = {
        "email": "multi.role@hsc.gov.in",
        "full_name": "Multi Role User",
        "password": "SecurePassword1!",
        "scope_level": "phc",
        "role_names": ["PHC Operator", "District Approver"]
    }
    resp_multi = client.post("/users", json=multi_role_payload, headers=admin_headers)
    assert resp_multi.status_code == 422

    # Empty role_names rejected (min_length=1 enforced) → 422
    empty_role_payload = {
        "email": "empty.role@hsc.gov.in",
        "full_name": "Empty Role User",
        "password": "SecurePassword1!",
        "scope_level": "platform",
        "role_names": []
    }
    resp_empty = client.post("/users", json=empty_role_payload, headers=admin_headers)
    assert resp_empty.status_code == 422


# 5. Super Admin updates user details
def test_super_admin_update_user(client: TestClient, seeded_db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    user = seeded_db.query(User).filter_by(email="phc.operator.pat@hsc.gov.in").first()
    assert user is not None

    update_payload = {
        "full_name": "Updated Patratu Operator Name",
        "phone": "+911122334455"
    }
    response = client.patch(f"/users/{user.id}", json=update_payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Patratu Operator Name"
    assert data["phone"] == "+911122334455"


# 6. Deactivate and reactivate user lifecycle
def test_user_deactivation_and_reactivation(client: TestClient, seeded_db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    target_user = seeded_db.query(User).filter_by(email="district.approver.ran@hsc.gov.in").first()
    assert target_user is not None

    # 1. Deactivate
    resp_deact = client.post(f"/users/{target_user.id}/deactivate", headers=admin_headers)
    assert resp_deact.status_code == 200
    assert resp_deact.json()["is_active"] is False

    # 2. Deactivated user cannot login
    resp_login = client.post(
        "/auth/login",
        json={"email": "district.approver.ran@hsc.gov.in", "password": "Test@123"}
    )
    assert resp_login.status_code == 401
    assert "deactivated" in resp_login.json()["detail"]

    # 3. Reactivate
    resp_act = client.post(f"/users/{target_user.id}/activate", headers=admin_headers)
    assert resp_act.status_code == 200
    assert resp_act.json()["is_active"] is True

    # 4. Reactivated user can login again
    resp_relogin = client.post(
        "/auth/login",
        json={"email": "district.approver.ran@hsc.gov.in", "password": "Test@123"}
    )
    assert resp_relogin.status_code == 200


# 7. Admin cannot deactivate own account
def test_admin_cannot_deactivate_self(client: TestClient, seeded_db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    super_admin = seeded_db.query(User).filter_by(email="superadmin@hsc.gov.in").first()
    assert super_admin is not None

    response = client.post(f"/users/{super_admin.id}/deactivate", headers=admin_headers)
    assert response.status_code == 400
    assert "Cannot deactivate own account" in response.json()["detail"]


# 8. Admin reset password
def test_admin_reset_user_password(client: TestClient, seeded_db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    target_user = seeded_db.query(User).filter_by(email="phc.approver.pat@hsc.gov.in").first()
    assert target_user is not None

    response = client.post(f"/users/{target_user.id}/reset-password", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "temporary_password" in data
    temp_pwd = data["temporary_password"]

    # Login with old password fails
    resp_old = client.post(
        "/auth/login",
        json={"email": "phc.approver.pat@hsc.gov.in", "password": "Test@123"}
    )
    assert resp_old.status_code == 401

    # Login with new temporary password succeeds
    resp_new = client.post(
        "/auth/login",
        json={"email": "phc.approver.pat@hsc.gov.in", "password": temp_pwd}
    )
    assert resp_new.status_code == 200


# 9. Get user roles and permissions
def test_get_user_roles_and_permissions(client: TestClient, seeded_db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    user = seeded_db.query(User).filter_by(email="district.approver.ram@hsc.gov.in").first()
    assert user is not None

    # Roles
    resp_roles = client.get(f"/users/{user.id}/roles", headers=admin_headers)
    assert resp_roles.status_code == 200
    roles = resp_roles.json()
    assert any(r["name"] == "District Approver" for r in roles)

    # Permissions
    resp_perms = client.get(f"/users/{user.id}/permissions", headers=admin_headers)
    assert resp_perms.status_code == 200
    perms = resp_perms.json()
    assert "view_district" in perms
    assert "approve_intra_district_transfer" in perms


# 10. Self-profile update and change password
def test_self_profile_update_and_change_password(client: TestClient):
    user_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in", "Test@123")

    # 1. GET /auth/me
    resp_me = client.get("/auth/me", headers=user_headers)
    assert resp_me.status_code == 200
    assert resp_me.json()["email"] == "district.approver.ram@hsc.gov.in"

    # 2. PATCH /auth/me (update full_name and phone)
    patch_resp = client.patch(
        "/auth/me",
        json={"full_name": "Ramgarh Officer Updated", "phone": "+919988776655"},
        headers=user_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["full_name"] == "Ramgarh Officer Updated"
    assert patch_resp.json()["phone"] == "+919988776655"

    # 3. POST /auth/me/change-password
    # Wrong current password fails
    resp_bad_pwd = client.post(
        "/auth/me/change-password",
        json={"current_password": "WrongPassword1!", "new_password": "NewValidPassword123!"},
        headers=user_headers
    )
    assert resp_bad_pwd.status_code == 400
    assert "Current password is incorrect" in resp_bad_pwd.json()["detail"]

    # Same password fails
    resp_same_pwd = client.post(
        "/auth/me/change-password",
        json={"current_password": "Test@123", "new_password": "Test@123"},
        headers=user_headers
    )
    assert resp_same_pwd.status_code == 400
    assert "must be different" in resp_same_pwd.json()["detail"]

    # Valid change password succeeds
    resp_change = client.post(
        "/auth/me/change-password",
        json={"current_password": "Test@123", "new_password": "NewValidPassword123!"},
        headers=user_headers
    )
    assert resp_change.status_code == 200
    assert resp_change.json()["success"] is True

    # Login with new password succeeds
    resp_relogin = client.post(
        "/auth/login",
        json={"email": "district.approver.ram@hsc.gov.in", "password": "NewValidPassword123!"}
    )
    assert resp_relogin.status_code == 200
