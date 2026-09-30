"""Comprehensive test suite for Federated Learning & Demand Forecasting module.
Contains 25 tests:
- Data setup (2)
- Model layer (4)
- Round orchestration (10)
- Storage layer (4)
- API layer (5)
"""
from uuid import UUID
from datetime import date, timedelta
import os
import shutil
import tempfile
import pytest
import torch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.fl import (
    DrugConsumptionHistory,
    FlRound,
    FlModel,
    FlForecast,
    FlRoundStatusEnum,
    FlNodeLevelEnum,
)
from app.models.geography import Facility, District, State
from app.models.drug import Drug
from app.models.inventory import StockTransaction, TransactionTypeEnum, InventoryBatch, BatchStatusEnum
from app.ml.model import RegionalDemandNet, ARCHITECTURE_HASH
from app.ml.features import build_feature_tensors
from app.ml.aggregator import federated_average
from app.ml.storage import LocalFileStorage
from app.services.fl_service import FlService, cleanup_old_archives
from app.core.config import settings

API_PREFIX = settings.API_V1_STR


def get_auth_header(client: TestClient, email: str, password: str = "Test@123") -> dict:
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fl_round_triggered(client: TestClient, seeded_db: Session) -> FlRound:
    """Triggers one FL round via the API and returns the resulting FlRound row."""
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    resp = client.post(f"{API_PREFIX}/fl/trigger-round", headers=admin_headers)
    assert resp.status_code == 201, f"Round trigger failed: {resp.text}"
    round_rec = seeded_db.query(FlRound).order_by(FlRound.round_number.desc()).first()
    assert round_rec is not None
    return round_rec


# ==============================================================================
# 1. DATA SETUP (2 tests)
# ==============================================================================

def test_rollup_creates_daily_history(seeded_db: Session):
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    drug = seeded_db.query(Drug).first()
    assert patratu is not None
    assert drug is not None

    today = date.today()
    tx1 = StockTransaction(
        facility_id=patratu.id,
        drug_id=drug.id,
        transaction_type=TransactionTypeEnum.DISPENSE,
        quantity=30,
        performed_by=patratu.id,
    )
    tx2 = StockTransaction(
        facility_id=patratu.id,
        drug_id=drug.id,
        transaction_type=TransactionTypeEnum.DISPENSE,
        quantity=20,
        performed_by=patratu.id,
    )
    seeded_db.add_all([tx1, tx2])
    seeded_db.flush()

    count = FlService.rollup_consumption_history(seeded_db, today, today)
    assert count >= 1

    rec = (
        seeded_db.query(DrugConsumptionHistory)
        .filter_by(facility_id=patratu.id, drug_id=drug.id, consumption_date=today)
        .first()
    )
    assert rec is not None
    assert rec.quantity_consumed == 50


def test_rollup_is_idempotent(seeded_db: Session):
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()
    drug = seeded_db.query(Drug).first()
    today = date.today()

    c1 = FlService.rollup_consumption_history(seeded_db, today, today)
    c2 = FlService.rollup_consumption_history(seeded_db, today, today)

    records = (
        seeded_db.query(DrugConsumptionHistory)
        .filter_by(facility_id=patratu.id, drug_id=drug.id, consumption_date=today)
        .all()
    )
    assert len(records) <= 1


# ==============================================================================
# 2. MODEL LAYER (4 tests)
# ==============================================================================

def test_model_forward_shape():
    model = RegionalDemandNet(n_features=32, hidden_dim=64)
    model.eval()
    x = torch.randn(4, 7, 32)
    out = model(x)
    assert out.shape == (4, 1)


def test_save_load_roundtrip():
    model = RegionalDemandNet(n_features=32, hidden_dim=64)
    model.eval()
    x = torch.randn(2, 7, 32)
    with torch.no_grad():
        orig_pred = model(x)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pt")
    os.close(tmp_fd)
    try:
        torch.save(model.state_dict(), tmp_path)
        loaded_model = RegionalDemandNet(n_features=32, hidden_dim=64)
        loaded_model.load_state_dict(torch.load(tmp_path, map_location="cpu"))
        loaded_model.eval()
        with torch.no_grad():
            loaded_pred = loaded_model(x)
        assert torch.allclose(orig_pred, loaded_pred, atol=1e-5)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_federated_average_simple():
    m1 = RegionalDemandNet()
    m2 = RegionalDemandNet()
    m2.load_state_dict(m1.state_dict())

    avg_state = federated_average([m1.state_dict(), m2.state_dict()], [10, 10])
    for k, v in m1.state_dict().items():
        assert torch.allclose(v, avg_state[k], atol=1e-5)


def test_federated_average_weighted():
    m1 = RegionalDemandNet()
    m2 = RegionalDemandNet()

    with torch.no_grad():
        for p in m1.parameters():
            p.fill_(1.0)
        for p in m2.parameters():
            p.fill_(5.0)

    avg_state = federated_average([m1.state_dict(), m2.state_dict()], [3, 1])
    for k, v in avg_state.items():
        if v.is_floating_point():
            assert torch.allclose(v, torch.full_like(v, 2.0), atol=1e-5)


# ==============================================================================
# 3. ROUND ORCHESTRATION (10 tests)
# ==============================================================================

def test_trigger_round_super_admin_only(client: TestClient, seeded_db: Session):
    phc_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    resp = client.post(f"{API_PREFIX}/fl/trigger-round", headers=phc_headers)
    assert resp.status_code == 403


def test_trigger_round_creates_round(client: TestClient, seeded_db: Session):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    resp = client.post(f"{API_PREFIX}/fl/trigger-round", headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "completed"
    assert data["round_number"] >= 1
    assert data["participating_districts"] >= 2


def test_district_models_saved(client: TestClient, seeded_db: Session, fl_round_triggered: FlRound):
    round_rec = fl_round_triggered
    dist_models = (
        seeded_db.query(FlModel)
        .filter_by(round_id=round_rec.id, node_level=FlNodeLevelEnum.DISTRICT)
        .all()
    )
    assert len(dist_models) == 2
    for m in dist_models:
        assert m.is_serving is True
        assert m.architecture_hash == ARCHITECTURE_HASH
        assert os.path.exists(os.path.join(settings.MODELS_DIR, m.archive_path))
        assert os.path.exists(os.path.join(settings.MODELS_DIR, m.serving_path))


def test_state_model_saved(client: TestClient, seeded_db: Session, fl_round_triggered: FlRound):
    round_rec = fl_round_triggered
    state_models = (
        seeded_db.query(FlModel)
        .filter_by(round_id=round_rec.id, node_level=FlNodeLevelEnum.STATE)
        .all()
    )
    assert len(state_models) == 1
    assert state_models[0].is_serving is True
    assert os.path.exists(os.path.join(settings.MODELS_DIR, state_models[0].serving_path))


def test_nation_model_saved(client: TestClient, seeded_db: Session, fl_round_triggered: FlRound):
    round_rec = fl_round_triggered
    nation_models = (
        seeded_db.query(FlModel)
        .filter_by(round_id=round_rec.id, node_level=FlNodeLevelEnum.NATION)
        .all()
    )
    assert len(nation_models) == 1
    assert nation_models[0].node_id is None
    assert nation_models[0].is_serving is True


def test_warm_start_lineage(client: TestClient, seeded_db: Session, fl_round_triggered: FlRound):
    r1 = fl_round_triggered

    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    resp = client.post(f"{API_PREFIX}/fl/trigger-round", headers=admin_headers)
    assert resp.status_code == 201

    r2 = seeded_db.query(FlRound).order_by(FlRound.round_number.desc()).first()
    assert r2.round_number == r1.round_number + 1
    assert r2.parent_round_id == r1.id


def test_forecasts_persisted(seeded_db: Session, fl_round_triggered: FlRound):
    round_rec = fl_round_triggered
    forecasts = seeded_db.query(FlForecast).filter_by(round_id=round_rec.id).all()
    assert len(forecasts) >= 7 * 2 * 1


def test_different_districts_have_different_models(seeded_db: Session, fl_round_triggered: FlRound):
    round_rec = fl_round_triggered
    dist_models = (
        seeded_db.query(FlModel)
        .filter_by(round_id=round_rec.id, node_level=FlNodeLevelEnum.DISTRICT)
        .all()
    )
    assert len(dist_models) == 2

    p1 = os.path.join(settings.MODELS_DIR, dist_models[0].serving_path)
    p2 = os.path.join(settings.MODELS_DIR, dist_models[1].serving_path)
    sd1 = torch.load(p1, map_location="cpu")
    sd2 = torch.load(p2, map_location="cpu")

    differences = 0
    for k in sd1:
        if not torch.allclose(sd1[k], sd2[k], atol=1e-5):
            differences += 1
    assert differences > 0


def test_advisory_lock_prevents_concurrent_rounds(seeded_db: Session):
    dummy_round = FlRound(
        round_number=9999,
        status=FlRoundStatusEnum.RUNNING,
        started_at=date.today(),
    )
    seeded_db.add(dummy_round)
    seeded_db.commit()

    admin = seeded_db.query(User).filter_by(email="superadmin@hsc.gov.in").first()
    with pytest.raises(Exception) as exc_info:
        FlService.trigger_round(seeded_db, admin, "127.0.0.1")
    assert "in progress" in str(exc_info.value).lower()

    seeded_db.delete(dummy_round)
    seeded_db.commit()


def test_round_status_updates(seeded_db: Session, fl_round_triggered: FlRound):
    round_rec = fl_round_triggered
    assert round_rec.status == FlRoundStatusEnum.COMPLETED
    assert round_rec.duration_seconds is not None
    assert round_rec.completed_at is not None


# ==============================================================================
# 4. STORAGE LAYER (4 tests)
# ==============================================================================

def test_local_storage_save_and_load_roundtrip():
    test_dir = os.path.join(tempfile.gettempdir(), "test_models_storage")
    storage = LocalFileStorage(base_dir=test_dir)

    tmp_fd, tmp_file = tempfile.mkstemp()
    with open(tmp_file, "w") as f:
        f.write("hello model")
    os.close(tmp_fd)

    try:
        remote_key = "fl/test/model.pt"
        bytes_written = storage.save(tmp_file, remote_key)
        assert bytes_written > 0
        assert storage.exists(remote_key) is True

        download_fd, download_file = tempfile.mkstemp()
        os.close(download_fd)
        storage.load(remote_key, download_file)
        with open(download_file, "r") as f:
            assert f.read() == "hello model"
        os.remove(download_file)
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        shutil.rmtree(test_dir, ignore_errors=True)


def test_local_storage_copy_and_delete():
    test_dir = os.path.join(tempfile.gettempdir(), "test_models_storage_copy")
    storage = LocalFileStorage(base_dir=test_dir)

    tmp_fd, tmp_file = tempfile.mkstemp()
    with open(tmp_file, "w") as f:
        f.write("copy test")
    os.close(tmp_fd)

    try:
        k1 = "fl/src/m.pt"
        k2 = "fl/dst/m.pt"
        storage.save(tmp_file, k1)
        storage.copy(k1, k2)
        assert storage.exists(k2) is True

        storage.delete(k1)
        assert storage.exists(k1) is False
        assert storage.exists(k2) is True
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        shutil.rmtree(test_dir, ignore_errors=True)

def test_serving_flag_is_unique_per_node(seeded_db: Session):
    """
    The partial unique index on (node_level, node_id) WHERE is_serving = true
    prevents two serving models for the same district at the same time.
    Uses a fresh round to avoid colliding with the serving model that
    fl_round_triggered would have created.
    Uses a district UUID because SQL treats NULL (nation node_id) as distinct.
    """
    # Create a fresh round so no other test's models interfere
    fresh_round = FlRound(
        round_number=9998,
        status=FlRoundStatusEnum.COMPLETED,
        started_at=date.today(),
    )
    seeded_db.add(fresh_round)
    seeded_db.flush()

    ramgarh = seeded_db.query(District).filter_by(code="RAM").first()
    assert ramgarh is not None

    # Ensure no existing serving model for this (district, ramgarh) exists yet
    seeded_db.query(FlModel).filter(
        FlModel.node_level == FlNodeLevelEnum.DISTRICT,
        FlModel.node_id == ramgarh.id,
        FlModel.is_serving == True,
    ).delete(synchronize_session=False)
    seeded_db.flush()

    m1 = FlModel(
        round_id=fresh_round.id,
        node_level=FlNodeLevelEnum.DISTRICT,
        node_id=ramgarh.id,
        archive_path="a1.pt",
        serving_path="s1.pt",
        is_serving=True,
        model_size_bytes=100,
        architecture_hash=ARCHITECTURE_HASH,
        sample_count=10,
    )
    m2 = FlModel(
        round_id=fresh_round.id,
        node_level=FlNodeLevelEnum.DISTRICT,
        node_id=ramgarh.id,
        archive_path="a2.pt",
        serving_path="s2.pt",
        is_serving=True,
        model_size_bytes=100,
        architecture_hash=ARCHITECTURE_HASH,
        sample_count=10,
    )

    seeded_db.add(m1)
    seeded_db.flush()

    seeded_db.add(m2)
    with pytest.raises(IntegrityError):
        seeded_db.flush()
    seeded_db.rollback()

def test_cleanup_keeps_last_n_rounds(seeded_db: Session):
    test_dir = os.path.join(tempfile.gettempdir(), "test_cleanup_rounds")
    storage = LocalFileStorage(base_dir=test_dir)

    for r in range(1, 8):
        rec = FlRound(
            round_number=r + 100,
            status=FlRoundStatusEnum.COMPLETED,
            started_at=date.today(),
        )
        seeded_db.add(rec)
        k = f"fl/archive/round_{r + 100}/test.pt"
        tmp_fd, tmp_file = tempfile.mkstemp()
        os.close(tmp_fd)
        storage.save(tmp_file, k)
        os.remove(tmp_file)

    seeded_db.commit()

    cleanup_old_archives(storage, seeded_db, keep_last_n=5)

    assert storage.exists("fl/archive/round_101/test.pt") is False
    assert storage.exists("fl/archive/round_102/test.pt") is False
    assert storage.exists("fl/archive/round_107/test.pt") is True

    shutil.rmtree(test_dir, ignore_errors=True)


# ==============================================================================
# 5. API LAYER (5 tests)
# ==============================================================================

def test_fl_status_returns_latest_round(client: TestClient, seeded_db: Session, fl_round_triggered: FlRound):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    resp = client.get(f"{API_PREFIX}/fl/status", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["latest_round"] is not None
    assert "serving_model_paths" in data
    assert data["last_forecast_count"] > 0


def test_fl_rounds_pagination(client: TestClient, seeded_db: Session, fl_round_triggered: FlRound):
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    resp = client.get(f"{API_PREFIX}/fl/rounds?page=1&page_size=1", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 1
    assert data["pagination"]["total_items"] >= 1


def test_forecast_facility_returns_7_days(client: TestClient, seeded_db: Session, fl_round_triggered: FlRound):
    pat_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    resp = client.get(f"{API_PREFIX}/forecast/facility/{patratu.id}?days=7", headers=pat_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["facility_id"] == str(patratu.id)
    assert len(data["drugs"]) > 0
    assert len(data["drugs"][0]["forecasts"]) == 7


def test_forecast_scope_enforced(client: TestClient, seeded_db: Session):
    pat_headers = get_auth_header(client, "phc.operator.pat@hsc.gov.in")
    ranchi_headers = get_auth_header(client, "district.approver.ran@hsc.gov.in")
    patratu = seeded_db.query(Facility).filter_by(code="PAT_PHC").first()

    r_pat = client.get(f"{API_PREFIX}/forecast/facility/{patratu.id}", headers=pat_headers)
    assert r_pat.status_code == 200

    r_ran = client.get(f"{API_PREFIX}/forecast/facility/{patratu.id}", headers=ranchi_headers)
    assert r_ran.status_code == 403


def test_forecast_values_are_in_plausible_range(client: TestClient, seeded_db: Session):
    """
    After a round, BCG vaccine forecasts (low-volume drug) should be
    significantly smaller than Paracetamol forecasts (high-volume).
    """
    admin_headers = get_auth_header(client, "superadmin@hsc.gov.in")
    client.post(f"{API_PREFIX}/fl/trigger-round", headers=admin_headers)

    kanke = seeded_db.query(Facility).filter_by(code="KAN_PHC").first()
    kanke_headers = get_auth_header(client, "phc.operator.kan@hsc.gov.in")

    resp = client.get(f"{API_PREFIX}/forecast/facility/{kanke.id}", headers=kanke_headers)
    assert resp.status_code == 200
    data = resp.json()

    bcg = next((d for d in data["drugs"] if "BCG" in d["drug_name"]), None)
    paracetamol = next((d for d in data["drugs"] if "Paracetamol" in d["drug_name"]), None)

    assert bcg is not None
    assert paracetamol is not None

    bcg_avg = sum(f["predicted_quantity"] for f in bcg["forecasts"]) / len(bcg["forecasts"])
    pcm_avg = sum(f["predicted_quantity"] for f in paracetamol["forecasts"]) / len(paracetamol["forecasts"])

    assert bcg_avg < pcm_avg
    assert bcg_avg < 50