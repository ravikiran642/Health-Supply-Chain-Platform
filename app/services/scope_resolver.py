"""Helper module for resolving user geographic scope, facility queries,
scope names, and validating district filter permissions.
"""
from uuid import UUID
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, Query
from app.models.user import User, ScopeLevelEnum
from app.models.geography import Facility, District, State


def resolve_scoped_facility_query(db: Session, user: User) -> Query:
    """
    Returns a SQLAlchemy query of Facility objects scoped to this user's visibility.
    Does not execute the query.
    Auto-filters by caller's scope:
      - platform / national  -> all facilities
      - state                -> all facilities whose district.state_id == user.scope_id
      - district             -> all facilities whose district_id == user.scope_id
      - phc                  -> the single facility with id == user.scope_id
    """
    query = db.query(Facility).join(District, Facility.district_id == District.id)

    if user.scope_level in (ScopeLevelEnum.PLATFORM, ScopeLevelEnum.NATIONAL):
        return query
    elif user.scope_level == ScopeLevelEnum.STATE:
        return query.filter(District.state_id == user.scope_id)
    elif user.scope_level == ScopeLevelEnum.DISTRICT:
        return query.filter(Facility.district_id == user.scope_id)
    elif user.scope_level == ScopeLevelEnum.PHC:
        return query.filter(Facility.id == user.scope_id)

    # Fallback to no facilities if scope_level unrecognized
    return query.filter(Facility.id == None)


def resolve_scope_name(db: Session, user: User) -> str:
    """Returns 'All India' / State.name / District.name / Facility.name."""
    if user.scope_level in (ScopeLevelEnum.PLATFORM, ScopeLevelEnum.NATIONAL):
        return "All India"
    elif user.scope_level == ScopeLevelEnum.STATE:
        state = db.query(State).filter(State.id == user.scope_id).first()
        return state.name if state else "Unknown State"
    elif user.scope_level == ScopeLevelEnum.DISTRICT:
        district = db.query(District).filter(District.id == user.scope_id).first()
        return district.name if district else "Unknown District"
    elif user.scope_level == ScopeLevelEnum.PHC:
        facility = db.query(Facility).filter(Facility.id == user.scope_id).first()
        return facility.name if facility else "Unknown Facility"
    return "Unknown Scope"


def validate_district_filter(db: Session, user: User, district_id: Optional[UUID]) -> None:
    """
    Raises HTTPException(400) if district_id is out of scope for the caller.
    - district user: IGNORE any district_id param (always their own); return 400 if a district_id != their own is passed
    - state user: allow filtering to any district within their state; reject other states' districts with 400
    - national/platform: allow any district_id
    - phc user: reject if district_id is passed (they only have 1 facility)
    """
    if district_id is None:
        return

    if user.scope_level == ScopeLevelEnum.PHC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PHC users cannot filter by district_id",
        )
    elif user.scope_level == ScopeLevelEnum.DISTRICT:
        if user.scope_id != district_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"District user cannot filter by another district '{district_id}'",
            )
    elif user.scope_level == ScopeLevelEnum.STATE:
        target_district = db.query(District).filter(District.id == district_id).first()
        if not target_district or target_district.state_id != user.scope_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"District '{district_id}' is not within state scope '{user.scope_id}'",
            )
    elif user.scope_level in (ScopeLevelEnum.PLATFORM, ScopeLevelEnum.NATIONAL):
        # Allow any existing district
        target_district = db.query(District).filter(District.id == district_id).first()
        if not target_district:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"District '{district_id}' does not exist",
            )
