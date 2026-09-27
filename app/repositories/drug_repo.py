"""Repository for Drug catalog queries and mutations."""
from uuid import UUID
from typing import Optional, List
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.drug import Drug, DrugCategoryEnum, DrugUnitEnum
from app.schemas.drug import DrugCreate


class DrugRepository:
    @staticmethod
    def get_by_id(db: Session, drug_id: UUID) -> Optional[Drug]:
        return db.query(Drug).filter(Drug.id == drug_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Drug]:
        return db.query(Drug).filter(func.lower(Drug.name) == name.strip().lower()).first()

    @staticmethod
    def list_drugs(
        db: Session,
        category: Optional[DrugCategoryEnum] = None,
        unit: Optional[DrugUnitEnum] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[Drug]:
        query = db.query(Drug)

        if category is not None:
            query = query.filter(Drug.category == category)
        if unit is not None:
            query = query.filter(Drug.unit == unit)
        if is_active is not None:
            query = query.filter(Drug.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(Drug.name.ilike(term))

        return query.order_by(Drug.name.asc()).all()

    @staticmethod
    def create(db: Session, drug_data: DrugCreate) -> Drug:
        drug = Drug(
            name=drug_data.name.strip(),
            category=drug_data.category,
            unit=drug_data.unit,
            is_active=True,
        )
        db.add(drug)
        db.flush()
        return drug
