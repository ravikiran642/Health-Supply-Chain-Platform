import pytest
from typing import Generator
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
    db.add(phc_patratu)
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

    db.add_all([super_admin, ramgarh_user, ranchi_user, phc_operator, phc_approver])
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
