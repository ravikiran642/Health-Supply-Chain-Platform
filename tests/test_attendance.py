"""Comprehensive test suite for Staff Attendance module:
Tests roster listing, scope enforcement, single marking, future date rejection,
deactivated user rejection, non-PHC user rejection, cross-facility user rejection,
duplicate marking conflict, atomic bulk marking and rollback on validation failure,
attendance corrections with mandatory reasons, pagination/filters, summary calculations,
and role/permission enforcement (District Approver read-only vs mark forbidden).
"""
import uuid
from datetime import date, timedelta, datetime, timezone
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.audit import AuditLog, AuditActionEnum, AuditResultEnum
from app.models.geography import Facility
from app.models.user import User
from app.models.attendance import StaffAttendance, AttendanceStatusEnum

API_PREFIX = settings.API_V1_STR


def get_auth_header(client: TestClient, email: str, password: str = "Test@123") -> dict:
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Roster for own facility → 200 with all PHC users listed
def test_roster_own_facility(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    assert patratu is not None

    response = client.get(f"{API_PREFIX}/attendance/facility/{patratu.id}/roster", headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

    emails = [item["user_email"] for item in data]
    assert "phc.operator.pat@hsc.gov.in" in emails
    assert "phc.approver.pat@hsc.gov.in" in emails

    # Today attendance was seeded as PRESENT for both
    for item in data:
        assert item["status"] == "present"
        assert item["attendance_id"] is not None


# 2. Roster for other facility → 403
def test_roster_other_facility_forbidden(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    kanke = seeded_db.query(Facility).filter_by(code="KAN_PHC").first()
    assert kanke is not None

    response = client.get(f"{API_PREFIX}/attendance/facility/{kanke.id}/roster", headers=op_headers)
    assert response.status_code == 403
    assert "Forbidden: facility outside your scope" in response.json()["detail"]


# 3. Mark single attendance → 201 + audit log
def test_mark_single_attendance(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    pat_op = seeded_db.query(User).filter_by(email="phc.operator.pat@hsc.gov.in").first()

    # Target date: 10 days ago (no existing record)
    past_date = date.today() - timedelta(days=10)

    payload = {
        "user_id": str(pat_op.id),
        "attendance_date": past_date.isoformat(),
        "status": "present",
        "check_in_time": datetime.now(timezone.utc).isoformat(),
        "remarks": "On-time arrival",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/mark",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "present"
    assert data["user_id"] == str(pat_op.id)
    assert data["attendance_date"] == past_date.isoformat()

    # Verify audit log
    audit = (
        seeded_db.query(AuditLog)
        .filter_by(action="attendance_marked", resource_type="staff_attendance")
        .order_by(AuditLog.timestamp.desc())
        .first()
    )
    assert audit is not None
    assert audit.result == AuditResultEnum.SUCCESS
    assert audit.metadata_["target_user_id"] == str(pat_op.id)
    assert "Operator" not in str(audit.metadata_)  # No PII


# 4. Mark for future date → 400
def test_mark_future_date_rejected(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    pat_op = seeded_db.query(User).filter_by(email="phc.operator.pat@hsc.gov.in").first()

    future_date = date.today() + timedelta(days=1)
    payload = {
        "user_id": str(pat_op.id),
        "attendance_date": future_date.isoformat(),
        "status": "present",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/mark",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 400
    assert "future date" in response.json()["detail"].lower()


# 5. Mark for deactivated user → 400
def test_mark_deactivated_user_rejected(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    pat_appr = seeded_db.query(User).filter_by(email="phc.approver.pat@hsc.gov.in").first()

    # Temporarily deactivate approver
    pat_appr.is_active = False
    seeded_db.commit()

    past_date = date.today() - timedelta(days=12)
    payload = {
        "user_id": str(pat_appr.id),
        "attendance_date": past_date.isoformat(),
        "status": "present",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/mark",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 400
    assert "deactivated" in response.json()["detail"].lower()

    # Restore approver active status
    pat_appr.is_active = True
    seeded_db.commit()


# 6. Mark for non-PHC user (district approver) → 400
def test_mark_non_phc_user_rejected(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    dist_user = seeded_db.query(User).filter_by(email="district.approver.ram@hsc.gov.in").first()

    past_date = date.today() - timedelta(days=13)
    payload = {
        "user_id": str(dist_user.id),
        "attendance_date": past_date.isoformat(),
        "status": "present",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/mark",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 400
    assert "does not have phc scope" in response.json()["detail"].lower()


# 7. Mark for user in different facility → 400
def test_mark_user_in_different_facility_rejected(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    kanke_op = seeded_db.query(User).filter_by(email="phc.operator.kan@hsc.gov.in").first()

    past_date = date.today() - timedelta(days=14)
    payload = {
        "user_id": str(kanke_op.id),
        "attendance_date": past_date.isoformat(),
        "status": "present",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/mark",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 400
    assert "belongs to facility" in response.json()["detail"].lower()


# 8. Duplicate mark same user+date → 409
def test_duplicate_mark_same_user_and_date_conflict(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    pat_op = seeded_db.query(User).filter_by(email="phc.operator.pat@hsc.gov.in").first()

    # Today's attendance is already seeded
    payload = {
        "user_id": str(pat_op.id),
        "attendance_date": date.today().isoformat(),
        "status": "present",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/mark",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 409
    assert "already recorded" in response.json()["detail"].lower()


# 9. Bulk mark all users → 201, all rows created
def test_bulk_mark_all_users_success(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    pat_op = seeded_db.query(User).filter_by(email="phc.operator.pat@hsc.gov.in").first()
    pat_appr = seeded_db.query(User).filter_by(email="phc.approver.pat@hsc.gov.in").first()

    target_date = date.today() - timedelta(days=20)
    payload = {
        "attendance_date": target_date.isoformat(),
        "entries": [
            {"user_id": str(pat_op.id), "status": "present", "remarks": "Shift A"},
            {"user_id": str(pat_appr.id), "status": "on_duty", "remarks": "Camp duty"},
        ],
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/bulk-mark",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2

    # Verify rows in DB
    records = seeded_db.query(StaffAttendance).filter_by(
        facility_id=patratu.id, attendance_date=target_date
    ).all()
    assert len(records) == 2


# 10. Bulk mark with one invalid entry → all rejected (atomic)
def test_bulk_mark_atomic_rollback_on_invalid_entry(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    pat_op = seeded_db.query(User).filter_by(email="phc.operator.pat@hsc.gov.in").first()
    kanke_op = seeded_db.query(User).filter_by(email="phc.operator.kan@hsc.gov.in").first()

    target_date = date.today() - timedelta(days=21)
    payload = {
        "attendance_date": target_date.isoformat(),
        "entries": [
            {"user_id": str(pat_op.id), "status": "present"},
            {"user_id": str(kanke_op.id), "status": "present"},  # Invalid: belongs to Kanke!
        ],
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/bulk-mark",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 400

    # Ensure pat_op was NOT saved (atomic rollback)
    record = seeded_db.query(StaffAttendance).filter_by(
        user_id=pat_op.id, attendance_date=target_date
    ).first()
    assert record is None


# 11. Correct attendance with reason → 200 + audit log with old→new
def test_correct_attendance_with_reason(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    pat_appr = seeded_db.query(User).filter_by(email="phc.approver.pat@hsc.gov.in").first()

    # Day-2 approver was seeded as LEAVE
    day_2_date = date.today() - timedelta(days=2)
    att_record = seeded_db.query(StaffAttendance).filter_by(
        user_id=pat_appr.id, attendance_date=day_2_date
    ).first()
    assert att_record is not None
    assert att_record.status == AttendanceStatusEnum.LEAVE

    correction_payload = {
        "status": "on_duty",
        "reason": "Attended pulse polio immunization drive at district HQ",
        "remarks": "Verified by Medical Superintendent",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/{att_record.id}/correct",
        json=correction_payload,
        headers=op_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "on_duty"
    assert data["remarks"] == "Verified by Medical Superintendent"
    assert data["last_modified_by"] is not None

    # Verify audit log diff
    audit = (
        seeded_db.query(AuditLog)
        .filter_by(action="attendance_corrected", resource_id=str(att_record.id))
        .first()
    )
    assert audit is not None
    assert audit.metadata_["old_status"] == "leave"
    assert audit.metadata_["new_status"] == "on_duty"
    assert audit.metadata_["reason"] == "Attended pulse polio immunization drive at district HQ"


# 12. Correct without reason → 422
def test_correct_attendance_without_reason_rejected(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    today_att = seeded_db.query(StaffAttendance).filter_by(
        facility_id=patratu.id, attendance_date=date.today()
    ).first()

    payload = {
        "status": "half_day",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/{today_att.id}/correct",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 422


# 13. Correct with reason shorter than 10 chars → 422
def test_correct_attendance_short_reason_rejected(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    today_att = seeded_db.query(StaffAttendance).filter_by(
        facility_id=patratu.id, attendance_date=date.today()
    ).first()

    payload = {
        "status": "half_day",
        "reason": "too short",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/{today_att.id}/correct",
        json=payload,
        headers=op_headers,
    )
    assert response.status_code == 422


# 14. History endpoint with date range filter → 200
def test_history_endpoint_with_filters(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    from_d = date.today() - timedelta(days=5)
    to_d = date.today()

    response = client.get(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/history?from_date={from_d}&to_date={to_d}",
        headers=op_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "pagination" in data
    assert data["pagination"]["total_items"] >= 10  # 5 days x 2 staff


# 15. Summary endpoint returns correct counts
def test_summary_endpoint_counts(client: TestClient, seeded_db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    from_d = date.today() - timedelta(days=4)
    to_d = date.today()

    response = client.get(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/summary?from_date={from_d}&to_date={to_d}",
        headers=op_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_marked"] >= 10
    assert data["present_count"] >= 8
    assert data["attendance_rate"] > 0


# 16. District Approver can view roster (read-only) → 200
def test_district_approver_views_roster(client: TestClient, seeded_db: Session):
    dist_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    response = client.get(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/roster",
        headers=dist_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


# 17. District Approver cannot mark → 403
def test_district_approver_cannot_mark_attendance(client: TestClient, seeded_db: Session):
    dist_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    pat_op = seeded_db.query(User).filter_by(email="phc.operator.pat@hsc.gov.in").first()

    payload = {
        "user_id": str(pat_op.id),
        "attendance_date": (date.today() - timedelta(days=25)).isoformat(),
        "status": "present",
    }
    response = client.post(
        f"{API_PREFIX}/attendance/facility/{patratu.id}/mark",
        json=payload,
        headers=dist_headers,
    )
    assert response.status_code == 403
    assert "missing 'mark_attendance'" in response.json()["detail"].lower()


# 18. State Approver Attendance My-Scope -> 2 facilities, correct counts for today
def test_state_approver_attendance_my_scope(client: TestClient, seeded_db: Session):
    state_headers = get_auth_header(client, "state.approver.jh@hsc.gov.in")

    response = client.get(f"{API_PREFIX}/attendance/my-scope", headers=state_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["scope_level"] == "state"
    assert data["scope_name"] == "Jharkhand"
    assert data["pagination"]["total_items"] == 2
    assert len(data["items"]) == 2

    # Patratu has 2 staff marked present today
    pat_item = next(item for item in data["items"] if item["facility_code"] == "PAT_PHC")
    assert pat_item["total_staff"] == 2
    assert pat_item["present_count"] == 2
    assert pat_item["marked_count"] == 2
    assert pat_item["attendance_rate"] == 100.0


# 19. District Approver Attendance My-Scope -> 1 facility (Patratu only)
def test_district_approver_attendance_my_scope(client: TestClient, seeded_db: Session):
    dist_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in")

    response = client.get(f"{API_PREFIX}/attendance/my-scope", headers=dist_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["scope_level"] == "district"
    assert data["scope_name"] == "Ramgarh"
    assert data["pagination"]["total_items"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["facility_code"] == "PAT_PHC"
    assert data["aggregate"]["total_facilities"] == 1


# 20. Attendance My-Scope Pagination -> page_size=1 -> 1 item, total_items=2
def test_attendance_my_scope_pagination(client: TestClient, seeded_db: Session):
    state_headers = get_auth_header(client, "state.approver.jh@hsc.gov.in")

    response = client.get(f"{API_PREFIX}/attendance/my-scope?page=1&page_size=1", headers=state_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 1
    assert data["pagination"]["total_items"] == 2
    assert data["pagination"]["total_pages"] == 2
    assert data["aggregate"]["total_facilities"] == 2


# 21. Attendance My-Scope Date Filter -> date = 2 days ago -> approver shows leave_count=1 for Patratu
def test_my_scope_date_filter(client: TestClient, seeded_db: Session):
    state_headers = get_auth_header(client, "state.approver.jh@hsc.gov.in")
    day_2_date = date.today() - timedelta(days=2)

    response = client.get(f"{API_PREFIX}/attendance/my-scope?date={day_2_date.isoformat()}", headers=state_headers)
    assert response.status_code == 200
    data = response.json()
    pat_item = next(item for item in data["items"] if item["facility_code"] == "PAT_PHC")
    assert pat_item["leave_count"] == 1
    assert pat_item["present_count"] == 1
    assert pat_item["marked_count"] == 2


# 22. District ID Filter out of scope rejected -> district user passes different district_id -> 400
def test_district_id_filter_out_of_scope_rejected(client: TestClient, seeded_db: Session):
    dist_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in")
    other_district = seeded_db.query(Facility).filter_by(code="KAN_PHC").first().district_id

    response = client.get(f"{API_PREFIX}/attendance/my-scope?district_id={other_district}", headers=dist_headers)
    assert response.status_code == 400
    assert "cannot filter by another district" in response.json()["detail"].lower()

