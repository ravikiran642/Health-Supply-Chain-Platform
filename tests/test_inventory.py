"""Comprehensive test suite for Medicine Inventory module:
Tests drug master catalog, facility stock management, FEFO dispensing,
write-offs, expiry tracking, transaction ledger, scope enforcement, and DB constraints.
"""
import uuid
from datetime import date, timedelta
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.audit import AuditLog, AuditActionEnum, AuditResultEnum
from app.models.geography import Facility
from app.models.drug import Drug, DrugCategoryEnum, DrugUnitEnum
from app.models.inventory import (
    InventoryBatch,
    BatchStatusEnum,
    StockTransaction,
    TransactionTypeEnum,
)
from app.core.config import settings

API_PREFIX = settings.API_V1_STR


def get_auth_header(client: TestClient, email: str, password: str = "Test@123") -> dict:
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. List drugs (authenticated user)
def test_list_drugs_authenticated(client: TestClient):
    user_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")

    response = client.get(f"{API_PREFIX}/inventory/drugs", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    names = [d["name"] for d in data]
    assert "Paracetamol 500mg" in names
    assert "Amoxicillin 500mg" in names

    # Filter by category
    resp_filtered = client.get(f"{API_PREFIX}/inventory/drugs?category=antibiotic", headers=user_headers)
    assert resp_filtered.status_code == 200
    for d in resp_filtered.json():
        assert d["category"] == "antibiotic"


# 2. Super Admin creates drug → 201
def test_super_admin_creates_drug(client: TestClient, db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")

    payload = {
        "name": "Metformin 500mg",
        "category": "other",
        "unit": "tablet",
    }
    response = client.post(f"{API_PREFIX}/inventory/drugs", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Metformin 500mg"
    assert data["category"] == "other"
    assert data["unit"] == "tablet"

    # Verify audit log
    audit_entry = db.query(AuditLog).filter_by(action="drug_created", resource_type="drug").first()
    assert audit_entry is not None
    assert audit_entry.result == AuditResultEnum.SUCCESS


# 3. PHC Operator tries to create drug → 403
def test_phc_operator_create_drug_forbidden(client: TestClient):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")

    payload = {
        "name": "Azithromycin 500mg",
        "category": "antibiotic",
        "unit": "tablet",
    }
    response = client.post(f"{API_PREFIX}/inventory/drugs", json=payload, headers=op_headers)
    assert response.status_code == 403


# 4. Receive stock at own facility → 201 + batch created + transaction logged
def test_receive_stock_own_facility(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()
    drug = db.query(Drug).filter_by(name="Ciprofloxacin 500mg").first()

    future_exp = (date.today() + timedelta(days=150)).isoformat()
    payload = {
        "drug_id": str(drug.id),
        "batch_number": "PAT-CIP-001",
        "quantity": 250,
        "expiry_date": future_exp,
    }
    response = client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/receive", json=payload, headers=op_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["batch_number"] == "PAT-CIP-001"
    assert data["quantity"] == 250
    assert data["status"] == "active"

    # Verify transaction logged
    tx = db.query(StockTransaction).filter_by(
        facility_id=patratu.id,
        drug_id=drug.id,
        transaction_type=TransactionTypeEnum.RECEIVE,
    ).first()
    assert tx is not None
    assert tx.quantity == 250

    # Verify audit log
    audit = db.query(AuditLog).filter_by(action="stock_received").first()
    assert audit is not None


# 5. Receive stock at other facility → 403 + audit log
def test_receive_stock_other_facility_forbidden(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    kanke = db.query(Facility).filter_by(code="KAN_PHC").first()
    drug = db.query(Drug).filter_by(name="Ciprofloxacin 500mg").first()

    payload = {
        "drug_id": str(drug.id),
        "batch_number": "KAN-CIP-ILLEGAL",
        "quantity": 100,
        "expiry_date": (date.today() + timedelta(days=90)).isoformat(),
    }
    response = client.post(f"{API_PREFIX}/inventory/facility/{kanke.id}/receive", json=payload, headers=op_headers)
    assert response.status_code == 403
    assert "Forbidden: facility outside your scope" in response.json()["detail"]

    # Verify audit denial logged
    audit = db.query(AuditLog).filter_by(
        action=AuditActionEnum.PERMISSION_DENIED.value,
        resource_type="facility",
        resource_id=str(kanke.id),
    ).first()
    assert audit is not None
    assert audit.result == AuditResultEnum.DENIED


# District Approver has view_inventory but NOT create_inventory — cannot receive
def test_district_approver_cannot_receive_stock(client: TestClient, db: Session):
    """District Approver has view_inventory but NOT create_inventory — cannot receive stock."""
    dist_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()
    drug = db.query(Drug).filter_by(name="Zinc Sulfate 20mg").first()

    payload = {
        "drug_id": str(drug.id),
        "batch_number": "PAT-ZNC-001",
        "quantity": 400,
        "expiry_date": (date.today() + timedelta(days=240)).isoformat(),
    }
    response = client.post(
        f"{API_PREFIX}/inventory/facility/{patratu.id}/receive",
        json=payload,
        headers=dist_headers,
    )
    assert response.status_code == 403
    assert "missing 'create_inventory'" in response.json()["detail"]



# Ramgarh DHO cannot VIEW Ranchi district's facility inventory (scope enforcement via read permission)
def test_district_approver_different_district_view_forbidden(client: TestClient, db: Session):
    """Ramgarh DHO cannot VIEW Ranchi district's facility inventory."""
    ramgarh_headers = get_auth_header(client, "district.approver.ram@hsc.gov.in")
    kanke = db.query(Facility).filter_by(code="KAN_PHC").first()  # Ranchi district

    response = client.get(
        f"{API_PREFIX}/inventory/facility/{kanke.id}",
        headers=ramgarh_headers,
    )
    assert response.status_code == 403
    assert "Forbidden: facility outside your scope" in response.json()["detail"]


# 8. Dispense with FEFO: two batches, earliest expiry used first
def test_dispense_fefo_earliest_expiry_first(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()
    pcm = db.query(Drug).filter_by(name="Paracetamol 500mg").first()

    # Pre-condition: PAT-PCM-002 has 300 qty (exp +30 days), PAT-PCM-001 has 500 qty (exp +180 days)
    # Dispense 400 units:
    # 300 should come from PAT-PCM-002 (depleting it), 100 from PAT-PCM-001 (leaving 400)
    payload = {
        "drug_id": str(pcm.id),
        "quantity": 400,
        "reason": "Outpatient department dispensing",
    }
    response = client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/dispense", json=payload, headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_dispensed"] == 400
    assert data["remaining_stock"] == 400  # Total 800 - 400 = 400

    # Verify batches in DB
    b_early = db.query(InventoryBatch).filter_by(facility_id=patratu.id, batch_number="PAT-PCM-002").first()
    b_later = db.query(InventoryBatch).filter_by(facility_id=patratu.id, batch_number="PAT-PCM-001").first()

    assert b_early.quantity == 0
    assert b_early.status == BatchStatusEnum.DEPLETED
    assert b_later.quantity == 400
    assert b_later.status == BatchStatusEnum.ACTIVE

    # Verify transaction
    tx = db.query(StockTransaction).filter_by(
        facility_id=patratu.id,
        transaction_type=TransactionTypeEnum.DISPENSE,
    ).first()
    assert tx is not None
    assert tx.quantity == -400


# 9. Dispense exceeding stock → 400
def test_dispense_exceeding_stock_bad_request(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()
    pcm = db.query(Drug).filter_by(name="Paracetamol 500mg").first()

    payload = {
        "drug_id": str(pcm.id),
        "quantity": 50000,
    }
    response = client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/dispense", json=payload, headers=op_headers)
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


# 10. Batch auto-depletes at 0 quantity
def test_batch_auto_depletes_at_zero(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()
    amx = db.query(Drug).filter_by(name="Amoxicillin 500mg").first()

    # Pre-condition: PAT-AMX-001 has 200 qty
    payload = {
        "drug_id": str(amx.id),
        "quantity": 200,
    }
    response = client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/dispense", json=payload, headers=op_headers)
    assert response.status_code == 200

    b = db.query(InventoryBatch).filter_by(facility_id=patratu.id, batch_number="PAT-AMX-001").first()
    assert b.quantity == 0
    assert b.status == BatchStatusEnum.DEPLETED


# 11. Write-off requires reason → 422 if missing or too short
def test_write_off_requires_reason(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()
    batch = db.query(InventoryBatch).filter_by(facility_id=patratu.id, batch_number="PAT-ORS-001").first()

    # Missing reason
    payload_missing = {
        "batch_id": str(batch.id),
        "quantity": 10,
        "reason_category": "damaged",
    }
    resp_missing = client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/write-off", json=payload_missing, headers=op_headers)
    assert resp_missing.status_code == 422

    # Reason shorter than 5 chars
    payload_short = {
        "batch_id": str(batch.id),
        "quantity": 10,
        "reason_category": "damaged",
        "reason": "bad",
    }
    resp_short = client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/write-off", json=payload_short, headers=op_headers)
    assert resp_short.status_code == 422

    # Missing reason_category
    payload_no_category = {
        "batch_id": str(batch.id),
        "quantity": 10,
        "reason": "Water damage occurred",
    }
    resp_no_category = client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/write-off", json=payload_no_category, headers=op_headers)
    assert resp_no_category.status_code == 422


# 12. Write-off deducts correctly
def test_write_off_deducts_correctly(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()
    batch = db.query(InventoryBatch).filter_by(facility_id=patratu.id, batch_number="PAT-ORS-001").first()
    init_qty = batch.quantity

    payload = {
        "batch_id": str(batch.id),
        "quantity": 50,
        "reason_category": "damaged",
        "reason": "Water damage during roof leakage in store room",
    }
    response = client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/write-off", json=payload, headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == init_qty - 50

    # Verify write-off transaction
    tx = db.query(StockTransaction).filter_by(
        batch_id=batch.id,
        transaction_type=TransactionTypeEnum.WRITE_OFF,
    ).first()
    assert tx is not None
    assert tx.quantity == -50
    assert tx.reason == "Water damage during roof leakage in store room"


# 13. Expiring endpoint returns correct batches
def test_expiring_batches_endpoint(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()

    # Query batches expiring in 35 days (PAT-PCM-002 expires in 30 days; others expire in 90+ days)
    response = client.get(f"{API_PREFIX}/inventory/facility/{patratu.id}/expiring?days=35", headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    batch_numbers = [b["batch_number"] for b in data]
    assert "PAT-PCM-002" in batch_numbers
    assert "PAT-PCM-001" not in batch_numbers

    # Verify computed field days_until_expiry is present
    for b in data:
        assert "days_until_expiry" in b
        assert b["days_until_expiry"] <= 35


# 14. Transaction ledger records every operation
def test_transaction_ledger(client: TestClient, db: Session):
    op_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = db.query(Facility).filter_by(code="PAT_PHC").first()

    # Perform a receive operation to guarantee a transaction entry
    drug = db.query(Drug).filter_by(name="BCG Vaccine").first()
    recv_payload = {
        "drug_id": str(drug.id),
        "batch_number": "PAT-BCG-LEDGER",
        "quantity": 120,
        "expiry_date": (date.today() + timedelta(days=60)).isoformat(),
    }
    client.post(f"{API_PREFIX}/inventory/facility/{patratu.id}/receive", json=recv_payload, headers=op_headers)

    response = client.get(f"{API_PREFIX}/inventory/facility/{patratu.id}/transactions", headers=op_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(tx["batch_number"] == "PAT-BCG-LEDGER" for tx in data["items"])


# 15. Quantity never goes negative (DB constraint enforced)
def test_quantity_never_negative_constraint(seeded_db: Session):
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    drug = seeded_db.query(Drug).first()
    assert patratu is not None
    assert drug is not None
    
    batch_neg = InventoryBatch(
        facility_id=patratu.id,
        drug_id=drug.id,
        batch_number="NEGATIVE-TEST-BATCH",
        quantity=-10,
        expiry_date=date.today() + timedelta(days=30),
        status=BatchStatusEnum.ACTIVE,
    )
    seeded_db.add(batch_neg)
    with pytest.raises(IntegrityError):
        seeded_db.flush()
    seeded_db.rollback()