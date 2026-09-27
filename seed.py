import sys
import uuid
from datetime import date, timedelta
from sqlalchemy import text
from app.core.database import SessionLocal, Base, engine
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

        # Self-Profile
        "view_own_profile",
        "update_own_profile",
        "change_own_password",
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

        # Self-Profile
        "view_own_profile",
        "update_own_profile",
        "change_own_password",

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
        "view_beds",
        "view_inventory",
        "view_attendance",
        "report_expiry",
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
        "view_own_profile",
        "update_own_profile",
        "change_own_password",
    ],
    "State Approver": [
        "view_inventory",
        "view_beds",
        "view_attendance",
        "report_expiry",
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
        "view_own_profile",
        "update_own_profile",
        "change_own_password",
    ],
    "National Viewer": [
        "view_inventory",
        "view_beds",
        "view_attendance",
        "report_expiry",
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
        "view_own_profile",
        "update_own_profile",
        "change_own_password",
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
        "view_users",
        "create_user",
        "update_user",
        "deactivate_user",
        "activate_user",
        "reset_user_password",
        "view_own_profile",
        "update_own_profile",
        "change_own_password",
        "view_inventory",
        "create_inventory",
        "update_inventory",
        "dispense_medicine",
        "write_off_stock",
        "report_expiry",
        "view_beds",
        "update_bed_occupancy",
        "add_bed",
        "deactivate_bed",
        "view_attendance",
        "mark_attendance",
        "correct_attendance",
    ]
}


def reset_database(db):
    """Truncates all tables with cascade."""
    print("Resetting database...")
    db.execute(text("TRUNCATE TABLE staff_attendance CASCADE;"))
    db.execute(text("TRUNCATE TABLE bed_occupancy_logs CASCADE;"))
    db.execute(text("TRUNCATE TABLE bed_inventories CASCADE;"))
    db.execute(text("TRUNCATE TABLE stock_transactions CASCADE;"))
    db.execute(text("TRUNCATE TABLE inventory_batches CASCADE;"))
    db.execute(text("TRUNCATE TABLE drugs CASCADE;"))
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

        # 5. Seed 10 Drugs Master Catalog
        print("Seeding 10 drugs master catalog...")
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
            d = db.query(Drug).filter_by(name=drug_name).first()
            if not d:
                d = Drug(name=drug_name, category=cat, unit=unit, is_active=True)
                db.add(d)
                db.flush()
            drug_objects[drug_name] = d

        # 6. Seed Sample Batches for 2 PHCs (Patratu + Kanke)
        print("Seeding sample batches for Patratu PHC and Kanke PHC...")
        patratu_fac = facilities_map.get("PAT_PHC")
        kanke_fac = facilities_map.get("KAN_PHC")
        today = date.today()

        sample_batches = []
        if patratu_fac:
            sample_batches.extend([
                (patratu_fac.id, drug_objects["Paracetamol 500mg"].id, "PAT-PCM-001", 500, today + timedelta(days=180)),
                (patratu_fac.id, drug_objects["Paracetamol 500mg"].id, "PAT-PCM-002", 300, today + timedelta(days=30)),
                (patratu_fac.id, drug_objects["Amoxicillin 500mg"].id, "PAT-AMX-001", 200, today + timedelta(days=90)),
                (patratu_fac.id, drug_objects["Oral Rehydration Salts (ORS)"].id, "PAT-ORS-001", 1000, today + timedelta(days=365)),
            ])
        if kanke_fac:
            sample_batches.extend([
                (kanke_fac.id, drug_objects["Paracetamol 500mg"].id, "KAN-PCM-001", 600, today + timedelta(days=120)),
                (kanke_fac.id, drug_objects["Artemether-Lumefantrine"].id, "KAN-ART-001", 150, today + timedelta(days=200)),
                (kanke_fac.id, drug_objects["BCG Vaccine"].id, "KAN-BCG-001", 50, today + timedelta(days=15)),
            ])

        for fac_id, d_id, b_num, qty, exp in sample_batches:
            existing_b = db.query(InventoryBatch).filter_by(
                facility_id=fac_id, drug_id=d_id, batch_number=b_num
            ).first()
            if not existing_b:
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
        print("Seeding sample bed inventories for Patratu PHC and Kanke PHC...")
        sample_beds = []
        if patratu_fac:
            sample_beds.extend([
                (patratu_fac.id, BedTypeEnum.GENERAL, 20, 8),
                (patratu_fac.id, BedTypeEnum.OXYGEN, 10, 4),
                (patratu_fac.id, BedTypeEnum.MATERNITY, 6, 2),
            ])
        if kanke_fac:
            sample_beds.extend([
                (kanke_fac.id, BedTypeEnum.GENERAL, 25, 12),
                (kanke_fac.id, BedTypeEnum.ICU, 4, 1),
                (kanke_fac.id, BedTypeEnum.PEDIATRIC, 8, 3),
            ])

        for fac_id, b_type, total, occupied in sample_beds:
            existing_bed = db.query(BedInventory).filter_by(
                facility_id=fac_id, bed_type=b_type
            ).first()
            if not existing_bed:
                bed_obj = BedInventory(
                    facility_id=fac_id,
                    bed_type=b_type,
                    total_beds=total,
                    occupied_beds=occupied,
                    is_active=True,
                )
                db.add(bed_obj)

        # 8. Seed 5 Days of Staff Attendance for Patratu PHC (Operator + Approver)
        print("Seeding 5 days of staff attendance for Patratu PHC...")
        pat_op = db.query(User).filter_by(email="phc.operator.pat_phc@hsc.gov.in").first()
        pat_appr = db.query(User).filter_by(email="phc.approver.pat_phc@hsc.gov.in").first()
        superadmin = db.query(User).filter_by(email="superadmin@hsc.gov.in").first()

        if patratu_fac and pat_op and pat_appr and superadmin:
            today = date.today()
            # 5 days: Day-4, Day-3, Day-2, Day-1, Today
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
                # Operator
                existing_op_att = db.query(StaffAttendance).filter_by(
                    user_id=pat_op.id, attendance_date=att_date
                ).first()
                if not existing_op_att:
                    db.add(
                        StaffAttendance(
                            facility_id=patratu_fac.id,
                            user_id=pat_op.id,
                            attendance_date=att_date,
                            status=op_status,
                            recorded_by=superadmin.id,
                        )
                    )

                # Approver
                existing_appr_att = db.query(StaffAttendance).filter_by(
                    user_id=pat_appr.id, attendance_date=att_date
                ).first()
                if not existing_appr_att:
                    db.add(
                        StaffAttendance(
                            facility_id=patratu_fac.id,
                            user_id=pat_appr.id,
                            attendance_date=att_date,
                            status=appr_status,
                            recorded_by=superadmin.id,
                        )
                    )

        db.commit()
        print("Seeding successfully finished! All 24 users, geography, RBAC matrix, 10 drugs, sample batches, bed inventories, and staff attendance loaded.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_database(reset=reset_flag)
