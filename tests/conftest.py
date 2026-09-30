import pytest
from typing import Generator
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.geography import State, District, Facility, FacilityTypeEnum
from app.models.rbac import Role, Permission
from app.models.user import User, ScopeLevelEnum
from app.models.drug import Drug, DrugCategoryEnum, DrugUnitEnum
from app.models.inventory import (
    InventoryBatch,
    BatchStatusEnum,
    StockTransaction,
    TransactionTypeEnum,
)
from app.models.bed import (
    BedInventory,
    BedOccupancyLog,
    BedTypeEnum,
)
from app.models.attendance import (
    StaffAttendance,
    AttendanceStatusEnum,
)
from app.models.fl import (
    DrugConsumptionHistory,
    FlRound,
    FlModel,
    FlForecast,
)
from seed import ROLE_PERMISSIONS_MATRIX

# SQLite in-memory engine with static pool for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide clean database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def seeded_db(db: Session) -> Session:
    """Seeds RBAC permissions, roles, geography, and test users."""
    # 1. Seed Permissions
    all_perm_names = set()
    for perms in ROLE_PERMISSIONS_MATRIX.values():
        all_perm_names.update(perms)

    perm_objects = {}
    for perm_name in sorted(all_perm_names):
        p = db.query(Permission).filter_by(name=perm_name).first()
        if not p:
            p = Permission(name=perm_name, description=f"Allows {perm_name}")
            db.add(p)
            db.flush()
        perm_objects[perm_name] = p

    # 2. Seed Roles
    role_objects = {}
    for role_name, perm_list in ROLE_PERMISSIONS_MATRIX.items():
        r = db.query(Role).filter_by(name=role_name).first()
        if not r:
            r = Role(name=role_name, description=f"Role for {role_name}")
            db.add(r)
            db.flush()
        r.permissions = [perm_objects[p] for p in perm_list]
        db.flush()
        role_objects[role_name] = r

    # 3. Seed Geography: 1 State (JH), 2 Districts (Ramgarh, Ranchi), 2 PHCs
    state_jh = State(name="Jharkhand", code="JH")
    db.add(state_jh)
    db.flush()

    dist_ramgarh = District(state_id=state_jh.id, name="Ramgarh", code="RAM")
    dist_ranchi = District(state_id=state_jh.id, name="Ranchi", code="RAN")
    db.add_all([dist_ramgarh, dist_ranchi])
    db.flush()

    phc_patratu = Facility(
        district_id=dist_ramgarh.id,
        name="Patratu PHC",
        type=FacilityTypeEnum.PHC,
        code="PAT_PHC"
    )
    phc_kanke = Facility(
        district_id=dist_ranchi.id,
        name="Kanke PHC",
        type=FacilityTypeEnum.PHC,
        code="KAN_PHC"
    )
    db.add_all([phc_patratu, phc_kanke])
    db.flush()

    # 4. Seed Test Users
    pwd_hash = get_password_hash("Test@123")

    # Super Admin
    super_admin = User(
        email="superadmin@hsc.gov.in",
        password_hash=pwd_hash,
        full_name="Super Admin",
        is_active=True,
        scope_level=ScopeLevelEnum.PLATFORM,
        scope_id=None,
        roles=[role_objects["Super Admin"]]
    )

    # State Approver - Jharkhand
    state_approver = User(
        email="state.approver.jh@hsc.gov.in",
        password_hash=pwd_hash,
        full_name="Jharkhand State Approver",
        is_active=True,
        scope_level=ScopeLevelEnum.STATE,
        scope_id=state_jh.id,
        roles=[role_objects["State Approver"]]
    )

    # District Approver - Ramgarh
    ramgarh_user = User(
        email="district.approver.ram@hsc.gov.in",
        password_hash=pwd_hash,
        full_name="Ramgarh District Approver",
        is_active=True,
        scope_level=ScopeLevelEnum.DISTRICT,
        scope_id=dist_ramgarh.id,
        roles=[role_objects["District Approver"]]
    )

    # District Approver - Ranchi
    ranchi_user = User(
        email="district.approver.ran@hsc.gov.in",
        password_hash=pwd_hash,
        full_name="Ranchi District Approver",
        is_active=True,
        scope_level=ScopeLevelEnum.DISTRICT,
        scope_id=dist_ranchi.id,
        roles=[role_objects["District Approver"]]
    )

    # PHC Operator - Patratu
    phc_operator = User(
        email="phc.operator.pat@hsc.gov.in",
        password_hash=pwd_hash,
        full_name="Patratu PHC Operator",
        is_active=True,
        scope_level=ScopeLevelEnum.PHC,
        scope_id=phc_patratu.id,
        roles=[role_objects["PHC Operator"]]
    )

    # PHC Approver - Patratu
    phc_approver = User(
        email="phc.approver.pat@hsc.gov.in",
        password_hash=pwd_hash,
        full_name="Patratu PHC Approver",
        is_active=True,
        scope_level=ScopeLevelEnum.PHC,
        scope_id=phc_patratu.id,
        roles=[role_objects["PHC Approver"]]
    )

    # PHC Operator - Kanke (for cross-facility rejection tests)
    phc_operator_kan = User(
        email="phc.operator.kan@hsc.gov.in",
        password_hash=pwd_hash,
        full_name="Kanke PHC Operator",
        is_active=True,
        scope_level=ScopeLevelEnum.PHC,
        scope_id=phc_kanke.id,
        roles=[role_objects["PHC Operator"]]
    )

    db.add_all([
        super_admin, ramgarh_user, ranchi_user, state_approver,
        phc_operator, phc_approver, phc_operator_kan,
    ])
    db.flush()

    # 5. Seed 10 Drugs Master Catalog
    drugs_data = [
        ("Paracetamol 500mg", DrugCategoryEnum.ANALGESIC, DrugUnitEnum.TABLET),
        ("Amoxicillin 500mg", DrugCategoryEnum.ANTIBIOTIC, DrugUnitEnum.CAPSULE),
        ("Ciprofloxacin 500mg", DrugCategoryEnum.ANTIBIOTIC, DrugUnitEnum.TABLET),
        ("Artemether-Lumefantrine", DrugCategoryEnum.ANTIMALARIAL, DrugUnitEnum.TABLET),
        ("Chloroquine Phosphate", DrugCategoryEnum.ANTIMALARIAL, DrugUnitEnum.TABLET),
        ("Oral Rehydration Salts (ORS)", DrugCategoryEnum.ORS, DrugUnitEnum.SACHET),
        ("Hepatitis B Vaccine", DrugCategoryEnum.VACCINE, DrugUnitEnum.VIAL),
        ("BCG Vaccine", DrugCategoryEnum.VACCINE, DrugUnitEnum.VIAL),
        ("Ibuprofen 400mg", DrugCategoryEnum.ANALGESIC, DrugUnitEnum.TABLET),
        ("Zinc Sulfate 20mg", DrugCategoryEnum.OTHER, DrugUnitEnum.TABLET),
    ]
    drug_objects = {}
    for drug_name, cat, unit in drugs_data:
        d = Drug(name=drug_name, category=cat, unit=unit, is_active=True)
        db.add(d)
        db.flush()
        drug_objects[drug_name] = d

    # 6. Seed Sample Batches for 2 PHCs (Patratu + Kanke)
    today = date.today()
    sample_batches = [
        (phc_patratu.id, drug_objects["Paracetamol 500mg"].id, "PAT-PCM-001", 500, today + timedelta(days=180)),
        (phc_patratu.id, drug_objects["Paracetamol 500mg"].id, "PAT-PCM-002", 300, today + timedelta(days=30)),
        (phc_patratu.id, drug_objects["Amoxicillin 500mg"].id, "PAT-AMX-001", 200, today + timedelta(days=90)),
        (phc_patratu.id, drug_objects["Oral Rehydration Salts (ORS)"].id, "PAT-ORS-001", 1000, today + timedelta(days=365)),
        (phc_kanke.id, drug_objects["Paracetamol 500mg"].id, "KAN-PCM-001", 600, today + timedelta(days=120)),
        (phc_kanke.id, drug_objects["Artemether-Lumefantrine"].id, "KAN-ART-001", 150, today + timedelta(days=200)),
        (phc_kanke.id, drug_objects["BCG Vaccine"].id, "KAN-BCG-001", 50, today + timedelta(days=15)),
    ]
    for fac_id, d_id, b_num, qty, exp in sample_batches:
        b = InventoryBatch(
            facility_id=fac_id,
            drug_id=d_id,
            batch_number=b_num,
            quantity=qty,
            expiry_date=exp,
            status=BatchStatusEnum.ACTIVE,
        )
        db.add(b)

    # 7. Seed Sample Bed Inventories for 2 PHCs (Patratu + Kanke)
    sample_beds = [
        (phc_patratu.id, BedTypeEnum.GENERAL, 20, 8),
        (phc_patratu.id, BedTypeEnum.OXYGEN, 10, 4),
        (phc_patratu.id, BedTypeEnum.MATERNITY, 6, 2),
        (phc_kanke.id, BedTypeEnum.GENERAL, 25, 12),
        (phc_kanke.id, BedTypeEnum.ICU, 4, 1),
        (phc_kanke.id, BedTypeEnum.PEDIATRIC, 8, 3),
    ]
    for fac_id, b_type, total, occupied in sample_beds:
        bed_obj = BedInventory(
            facility_id=fac_id,
            bed_type=b_type,
            total_beds=total,
            occupied_beds=occupied,
            is_active=True,
        )
        db.add(bed_obj)

    # 8. Seed 5 Days of Staff Attendance for Patratu PHC (Operator + Approver)
    # Day-4: both present
    # Day-3: both present
    # Day-2: operator present, approver on leave
    # Day-1: both present
    # Today: both present
    attendance_schedule = [
        (today - timedelta(days=4), AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.PRESENT),
        (today - timedelta(days=3), AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.PRESENT),
        (today - timedelta(days=2), AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.LEAVE),
        (today - timedelta(days=1), AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.PRESENT),
        (today, AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.PRESENT),
    ]

    for att_date, op_status, appr_status in attendance_schedule:
        db.add(
            StaffAttendance(
                facility_id=phc_patratu.id,
                user_id=phc_operator.id,
                attendance_date=att_date,
                status=op_status,
                recorded_by=super_admin.id,
            )
        )
        db.add(
            StaffAttendance(
                facility_id=phc_patratu.id,
                user_id=phc_approver.id,
                attendance_date=att_date,
                status=appr_status,
                recorded_by=super_admin.id,
            )
        )

    # 9. Seed 90 Days of Synthetic Drug Consumption History
    import random
    from datetime import timedelta
    from app.models.fl import DrugConsumptionHistory
    from app.models.drug import DrugCategoryEnum

    rng = random.Random(42)
    today = date.today()

    base_rate_by_cat = {
        DrugCategoryEnum.ANALGESIC: 40,
        DrugCategoryEnum.ANTIBIOTIC: 25,
        DrugCategoryEnum.ANTIMALARIAL: 20,
        DrugCategoryEnum.ORS: 50,
        DrugCategoryEnum.VACCINE: 15,
        DrugCategoryEnum.OTHER: 20,
    }

    # Patratu PHC gets: Paracetamol, Amoxicillin, ORS (4 drugs with 3 unique)
    # Kanke PHC gets: Paracetamol, Artemether-Lumefantrine, BCG Vaccine
    fac_drug_map = [
        (phc_patratu, ["Paracetamol 500mg", "Amoxicillin 500mg", "Oral Rehydration Salts (ORS)"]),
        (phc_kanke, ["Paracetamol 500mg", "Artemether-Lumefantrine", "BCG Vaccine"]),
    ]

    for facility, drug_names in fac_drug_map:
        for drug_name in drug_names:
            drug = drug_objects[drug_name]
            base_rate = base_rate_by_cat.get(drug.category, 20)

            # District bias: Ramgarh 1.5x antimalarials; Ranchi 1.5x ORS
            dist_code = facility.district.code if facility.district else ""
            if dist_code == "RAM" and drug.category == DrugCategoryEnum.ANTIMALARIAL:
                base_rate = int(base_rate * 1.5)
            elif dist_code == "RAN" and drug.category == DrugCategoryEnum.ORS:
                base_rate = int(base_rate * 1.5)

            for day_offset in range(90, 0, -1):
                cons_date = today - timedelta(days=day_offset)
                is_weekend = cons_date.weekday() in (5, 6)
                day_factor = 0.7 if is_weekend else 1.0
                trend = (90 - day_offset) * 0.05
                noise = rng.uniform(0.8, 1.2)
                qty = max(1, int((base_rate + trend) * day_factor * noise))

                db.add(DrugConsumptionHistory(
                    facility_id=facility.id,
                    drug_id=drug.id,
                    consumption_date=cons_date,
                    quantity_consumed=qty,
                ))

    db.flush()

    db.commit()

    return db


@pytest.fixture
def client(seeded_db: Session) -> Generator[TestClient, None, None]:
    """TestClient wired with seeded database session."""
    def override_get_db():
        try:
            yield seeded_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
