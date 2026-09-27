"""Comprehensive test suite for Beds and Occupancy module:
Tests bed ward listing, aggregated summaries, adding bed types, updating occupancy
and total capacity, deactivation rules, reactivation, history audit logging,
facility scope boundaries, and database check constraints.
"""
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.audit import AuditLog, AuditActionEnum, AuditResultEnum
from app.models.geography import Facility
from app.models.bed import BedInventory, BedOccupancyLog, BedTypeEnum


def get_auth_header(client: TestClient, email: str, password: str = "Test@123") -> dict:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. List beds at own facility → 200
def test_list_beds_own_facility(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    assert patratu is not None

    response = client.get(f"/beds/facility/{patratu.id}", headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    bed_types = [b["bed_type"] for b in data]
    assert "general" in bed_types
    assert "oxygen" in bed_types
    assert "maternity" in bed_types

    # Verify computed available_beds
    for b in data:
        assert b["available_beds"] == b["total_beds"] - b["occupied_beds"]


# 2. List beds at other facility → 403
def test_list_beds_other_facility_forbidden(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    kanke = seeded_db.query(Facility).filter_by(code="KAN_PHC").first()
    assert kanke is not None

    response = client.get(f"/beds/facility/{kanke.id}", headers=op_headers)
    assert response.status_code == 403
    assert "Forbidden: facility outside your scope" in response.json()["detail"]

    # Verify audit denial logged
    audit = seeded_db.query(AuditLog).filter_by(
        action=AuditActionEnum.PERMISSION_DENIED.value,
        resource_type="facility",
        resource_id=str(kanke.id),
    ).first()
    assert audit is not None
    assert audit.result == AuditResultEnum.DENIED


# 3. Add bed type → 201
def test_add_bed_type(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    payload = {
        "bed_type": "icu",
        "total_beds": 5,
    }
    response = client.post(f"/beds/facility/{patratu.id}", json=payload, headers=op_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["bed_type"] == "icu"
    assert data["total_beds"] == 5
    assert data["occupied_beds"] == 0
    assert data["available_beds"] == 5
    assert data["is_active"] is True

    # Verify log entry in bed_occupancy_logs
    log = seeded_db.query(BedOccupancyLog).filter_by(
        facility_id=patratu.id, bed_type=BedTypeEnum.ICU
    ).first()
    assert log is not None
    assert log.occupied_beds == 0
    assert log.total_beds == 5

    # Verify audit log
    audit = seeded_db.query(AuditLog).filter_by(action="bed_type_added").first()
    assert audit is not None


# 4. Duplicate bed type → 409
def test_add_duplicate_bed_type_conflict(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    # 'general' is already seeded for Patratu
    payload = {
        "bed_type": "general",
        "total_beds": 10,
    }
    response = client.post(f"/beds/facility/{patratu.id}", json=payload, headers=op_headers)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


# 5. Update occupancy within total → 200 + log created
def test_update_occupancy_within_total(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    # Pre-condition: general has total_beds=20, occupied_beds=8
    payload = {
        "occupied_beds": 14,
    }
    response = client.patch(f"/beds/facility/{patratu.id}/general", json=payload, headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["occupied_beds"] == 14
    assert data["total_beds"] == 20
    assert data["available_beds"] == 6

    # Verify occupancy log
    log = seeded_db.query(BedOccupancyLog).filter_by(
        facility_id=patratu.id, bed_type=BedTypeEnum.GENERAL
    ).order_by(BedOccupancyLog.recorded_at.desc()).first()
    assert log is not None
    assert log.occupied_beds == 14
    assert log.total_beds == 20

    # Verify audit event
    audit = seeded_db.query(AuditLog).filter_by(action="bed_occupancy_updated").first()
    assert audit is not None


# 6. Update occupancy > total → 400 or 422
def test_update_occupancy_exceeding_total(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    # Oxygen ward has total_beds=10; attempt occupied_beds=15
    payload = {
        "occupied_beds": 15,
    }
    response = client.patch(f"/beds/facility/{patratu.id}/oxygen", json=payload, headers=op_headers)
    assert response.status_code in (400, 422)
    assert "cannot exceed total" in response.text.lower()


# 7. Update total below occupied → 400
def test_update_total_below_occupied(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    # Oxygen ward has occupied_beds=4; attempt total_beds=2
    payload = {
        "total_beds": 2,
    }
    response = client.patch(f"/beds/facility/{patratu.id}/oxygen", json=payload, headers=op_headers)
    assert response.status_code in (400, 422)
    assert "cannot be less than occupied" in response.text.lower() or "cannot exceed total" in response.text.lower()


# 8. Deactivate with occupied > 0 → 400
def test_deactivate_with_occupied_forbidden(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    # Maternity has occupied_beds=2 > 0
    response = client.post(f"/beds/facility/{patratu.id}/maternity/deactivate", headers=op_headers)
    assert response.status_code == 400
    assert "Discharge patients first" in response.json()["detail"]


# 9. Deactivate with occupied = 0 → 200
def test_deactivate_with_occupied_zero(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    # Discharge all patients first in maternity ward
    client.patch(f"/beds/facility/{patratu.id}/maternity", json={"occupied_beds": 0}, headers=op_headers)

    response = client.post(f"/beds/facility/{patratu.id}/maternity/deactivate", headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False

    # Verify audit log
    audit = seeded_db.query(AuditLog).filter_by(action="bed_deactivated").first()
    assert audit is not None


# 10. Reactivate → 200
def test_reactivate_bed_type(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    # Maternity was deactivated in previous test; reactivate it
    response = client.post(f"/beds/facility/{patratu.id}/maternity/activate", headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True

    # Verify audit log
    audit = seeded_db.query(AuditLog).filter_by(action="bed_activated").first()
    assert audit is not None


# 11. History endpoint returns log entries
def test_bed_history_endpoint(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    # Update oxygen occupancy to guarantee at least one history row
    client.patch(f"/beds/facility/{patratu.id}/oxygen", json={"occupied_beds": 5}, headers=op_headers)

    response = client.get(f"/beds/facility/{patratu.id}/history", headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(log["bed_type"] == "oxygen" for log in data["items"])


# 12. District Approver can view own district's beds → 200
def test_district_approver_views_district_beds(client: TestClient, seeded_db: Session):
    dist_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()  # In Ramgarh district

    response = client.get(f"/beds/facility/{patratu.id}", headers=dist_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Also test summary endpoint
    summary_resp = client.get(f"/beds/facility/{patratu.id}/summary", headers=dist_headers)
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["facility_id"] == str(patratu.id)
    assert summary_data["total_beds"] > 0
