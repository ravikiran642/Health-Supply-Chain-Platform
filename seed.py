import sys
import uuid
from sqlalchemy import text
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.geography import State, District, Facility, FacilityTypeEnum
from app.models.rbac import Role, Permission
from app.models.user import User, ScopeLevelEnum


# Exact Permission Matrix Definition
ROLE_PERMISSIONS_MATRIX = {
    "PHC Operator": [
        # Medicines Inventory (CRUD, but delete = write-off)
        "view_inventory",
        "create_inventory",
        "update_inventory",
        "dispense_medicine",
        "write_off_stock",           # instead of delete
        "report_expiry",

        # Stock requests
        "request_stock",
        "report_stock_out",

        # Beds (CRUD, but delete = deactivate)
        "view_beds",
        "update_bed_occupancy",      # renamed from update_beds
        "add_bed",                   # for ward additions
        "deactivate_bed",            # for maintenance/removal

        # Staff Attendance (CRUD, but delete = correct)
        "view_attendance",
        "mark_attendance",
        "correct_attendance",        # instead of delete

        # Patient (CRUD, but delete = deactivate)
        "create_patient",
        "view_patient_limited",      # basic info only
        "update_patient",            # demographics
        "view_patient_history",
        "deactivate_patient",

        # Alerts
        "view_alerts",
        "acknowledge_alert",

        # Forecast
        "view_phc_forecast",
    ],
    "PHC Approver": [
        # all PHC Operator permissions
        "view_inventory",
        "create_inventory",
        "update_inventory",
        "dispense_medicine",
        "write_off_stock",           # instead of delete
        "report_expiry",

        # Stock requests
        "request_stock",
        "report_stock_out",

        # Beds (CRUD, but delete = deactivate)
        "view_beds",
        "update_bed_occupancy",      # renamed from update_beds
        "add_bed",                   # for ward additions
        "deactivate_bed",            # for maintenance/removal

        # Staff Attendance (CRUD, but delete = correct)
        "view_attendance",
        "mark_attendance",
        "correct_attendance",        # instead of delete

        # Patient (CRUD, but delete = deactivate)
        "create_patient",
        "view_patient_limited",      # basic info only
        "update_patient",            # demographics
        "view_patient_history",
        "deactivate_patient",

        # Alerts
        "view_alerts",
        "acknowledge_alert",

        # Forecast
        "view_phc_forecast",
        # approver-specific
        "update_patient_clinical",       # MO-specific
        "approve_phc_request",
        "approve_redistribution_to_phc",
        "request_redistribution",
        "cancel_redistribution",
        "dismiss_alert",
        "configure_alert_thresholds",
        "view_staff",                    # see full staff directory
        "correct_attendance",            # already in operator, keep
        "view_reports",
    ],
    "District Approver": [
        "view_district",
        "view_district_forecast",
        "view_redistribution",
        "approve_intra_district_transfer",
        "request_redistribution",
        "cancel_redistribution",
        "escalate_to_state",
        "view_alerts",
        "acknowledge_alert",
        "view_reports",
        "export_data",
        "view_scope_audit_logs",
    ],
    "State Approver": [
        "view_state",
        "view_state_forecast",
        "view_district",              # can drill down to districts
        "view_redistribution",
        "approve_inter_district_transfer",
        "escalate_to_national",
        "view_alerts",
        "acknowledge_alert",
        "view_fl_model_status",
        "view_fl_metrics",
        "view_reports",
        "export_data",
        "view_scope_audit_logs",
    ],
    "National Viewer": [
        "view_national",
        "view_national_forecast",
        "view_state",                 # can drill down to states
        "view_district",              # can drill down further
        "approve_inter_state_transfer",
        "view_alerts",
        "view_fl_model_status",
        "view_fl_metrics",
        "view_reports",
        "export_data",
        "view_scope_audit_logs",
    ],
    "Super Admin": [
        "manage_users",
        "manage_permissions",
        "manage_fl",
        "start_fl_round",
        "view_model_registry",
        "deploy_model",
        "rollback_model",
        "view_fl_metrics",
        "view_all",
        "view_audit_logs",
        "view_system_health",
        "view_reports",
        "export_data",
    ]
}


def reset_database(db):
    """Truncates all tables with cascade."""
    print("Resetting database...")
    db.execute(text("TRUNCATE TABLE audit_logs CASCADE;"))
    db.execute(text("TRUNCATE TABLE refresh_tokens CASCADE;"))
    db.execute(text("TRUNCATE TABLE user_roles CASCADE;"))
    db.execute(text("TRUNCATE TABLE users CASCADE;"))
    db.execute(text("TRUNCATE TABLE role_permissions CASCADE;"))
    db.execute(text("TRUNCATE TABLE permissions CASCADE;"))
    db.execute(text("TRUNCATE TABLE roles CASCADE;"))
    db.execute(text("TRUNCATE TABLE facilities CASCADE;"))
    db.execute(text("TRUNCATE TABLE districts CASCADE;"))
    db.execute(text("TRUNCATE TABLE states CASCADE;"))
    db.commit()
    print("Database reset complete.")


def seed_database(reset: bool = False):
    db = SessionLocal()
    try:
        if reset:
            reset_database(db)

        # 1. Seed Permissions
        print("Seeding permissions...")
        all_perm_names = set()
        for perms in ROLE_PERMISSIONS_MATRIX.values():
            all_perm_names.update(perms)

        perm_objects = {}
        for perm_name in sorted(all_perm_names):
            existing_perm = db.query(Permission).filter_by(name=perm_name).first()
            if not existing_perm:
                existing_perm = Permission(
                    name=perm_name,
                    description=f"Allows {perm_name.replace('_', ' ')}"
                )
                db.add(existing_perm)
                db.flush()
            perm_objects[perm_name] = existing_perm

        # 2. Seed Roles and Link Role Permissions
        print("Seeding roles and mapping permissions...")
        role_objects = {}
        for role_name, perm_list in ROLE_PERMISSIONS_MATRIX.items():
            existing_role = db.query(Role).filter_by(name=role_name).first()
            if not existing_role:
                existing_role = Role(
                    name=role_name,
                    description=f"Role for {role_name}"
                )
                db.add(existing_role)
                db.flush()

            # Assign permissions
            existing_role.permissions = [perm_objects[p] for p in perm_list]
            db.flush()
            role_objects[role_name] = existing_role

        # 3. Seed Geographic Hierarchy (2 States, 4 Districts, 8 PHCs)
        print("Seeding geographic hierarchy (States, Districts, PHCs)...")
        geo_data = {
            "JH": {
                "name": "Jharkhand",
                "districts": {
                    "RAM": {
                        "name": "Ramgarh",
                        "facilities": [
                            ("Patratu PHC", "PAT_PHC"),
                            ("Gola PHC", "GOL_PHC"),
                        ]
                    },
                    "RAN": {
                        "name": "Ranchi",
                        "facilities": [
                            ("Kanke PHC", "KAN_PHC"),
                            ("Ormanjhi PHC", "ORM_PHC"),
                        ]
                    }
                }
            },
            "MH": {
                "name": "Maharashtra",
                "districts": {
                    "PUN": {
                        "name": "Pune",
                        "facilities": [
                            ("Haveli PHC", "HAV_PHC"),
                            ("Mulshi PHC", "MUL_PHC"),
                        ]
                    },
                    "NAG": {
                        "name": "Nagpur",
                        "facilities": [
                            ("Hingna PHC", "HIN_PHC"),
                            ("Kamptee PHC", "KAM_PHC"),
                        ]
                    }
                }
            }
        }

        states_map = {}
        districts_map = {}
        facilities_map = {}

        for state_code, state_info in geo_data.items():
            state = db.query(State).filter_by(code=state_code).first()
            if not state:
                state = State(name=state_info["name"], code=state_code)
                db.add(state)
                db.flush()
            states_map[state_code] = state

            for dist_code, dist_info in state_info["districts"].items():
                district = db.query(District).filter_by(code=dist_code).first()
                if not district:
                    district = District(state_id=state.id, name=dist_info["name"], code=dist_code)
                    db.add(district)
                    db.flush()
                districts_map[dist_code] = district

                for fac_name, fac_code in dist_info["facilities"]:
                    facility = db.query(Facility).filter_by(code=fac_code).first()
                    if not facility:
                        facility = Facility(
                            district_id=district.id,
                            name=fac_name,
                            code=fac_code,
                            type=FacilityTypeEnum.PHC
                        )
                        db.add(facility)
                        db.flush()
                    facilities_map[fac_code] = facility

        # Common password hash
        default_pwd_hash = get_password_hash("Test@123")

        # 4. Seed Users
        print("Seeding Users (24 total)...")
        # 1x Super Admin
        if not db.query(User).filter_by(email="superadmin@hsc.gov.in").first():
            admin = User(
                email="superadmin@hsc.gov.in",
                password_hash=default_pwd_hash,
                full_name="National Super Admin",
                is_active=True,
                scope_level=ScopeLevelEnum.PLATFORM,
                scope_id=None,
                roles=[role_objects["Super Admin"]]
            )
            db.add(admin)

        # 1x National Viewer
        if not db.query(User).filter_by(email="national.viewer@hsc.gov.in").first():
            nat = User(
                email="national.viewer@hsc.gov.in",
                password_hash=default_pwd_hash,
                full_name="National Analytics Viewer",
                is_active=True,
                scope_level=ScopeLevelEnum.NATIONAL,
                scope_id=None,
                roles=[role_objects["National Viewer"]]
            )
            db.add(nat)

        # 2x State Approvers (one per state)
        for st_code, st_obj in states_map.items():
            email = f"state.approver.{st_code.lower()}@hsc.gov.in"
            if not db.query(User).filter_by(email=email).first():
                st_user = User(
                    email=email,
                    password_hash=default_pwd_hash,
                    full_name=f"{st_obj.name} State Approver",
                    is_active=True,
                    scope_level=ScopeLevelEnum.STATE,
                    scope_id=st_obj.id,
                    roles=[role_objects["State Approver"]]
                )
                db.add(st_user)

        # 4x District Approvers (one per district)
        for dist_code, dist_obj in districts_map.items():
            email = f"district.approver.{dist_code.lower()}@hsc.gov.in"
            if not db.query(User).filter_by(email=email).first():
                dist_user = User(
                    email=email,
                    password_hash=default_pwd_hash,
                    full_name=f"{dist_obj.name} District Approver",
                    is_active=True,
                    scope_level=ScopeLevelEnum.DISTRICT,
                    scope_id=dist_obj.id,
                    roles=[role_objects["District Approver"]]
                )
                db.add(dist_user)

        # 8x PHC Operators and 8x PHC Approvers (one per PHC each)
        for fac_code, fac_obj in facilities_map.items():
            # PHC Operator
            op_email = f"phc.operator.{fac_code.lower()}@hsc.gov.in"
            if not db.query(User).filter_by(email=op_email).first():
                op_user = User(
                    email=op_email,
                    password_hash=default_pwd_hash,
                    full_name=f"{fac_obj.name} Operator",
                    is_active=True,
                    scope_level=ScopeLevelEnum.PHC,
                    scope_id=fac_obj.id,
                    roles=[role_objects["PHC Operator"]]
                )
                db.add(op_user)

            # PHC Approver
            appr_email = f"phc.approver.{fac_code.lower()}@hsc.gov.in"
            if not db.query(User).filter_by(email=appr_email).first():
                appr_user = User(
                    email=appr_email,
                    password_hash=default_pwd_hash,
                    full_name=f"{fac_obj.name} Medical Officer",
                    is_active=True,
                    scope_level=ScopeLevelEnum.PHC,
                    scope_id=fac_obj.id,
                    roles=[role_objects["PHC Approver"]]
                )
                db.add(appr_user)

        db.commit()
        print("Seeding successfully finished! All 24 users, geography, and RBAC matrix loaded.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_database(reset=reset_flag)
