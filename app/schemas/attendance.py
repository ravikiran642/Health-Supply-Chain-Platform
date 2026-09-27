"""Pydantic v2 schemas for Staff Attendance tracking."""
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.attendance import AttendanceStatusEnum


class AttendanceMarkEntry(BaseModel):
    user_id: UUID = Field(..., description="ID of staff member")
    status: AttendanceStatusEnum = Field(..., description="Attendance status")
    check_in_time: Optional[datetime] = Field(None, description="Check-in timestamp (UTC)")
    check_out_time: Optional[datetime] = Field(None, description="Check-out timestamp (UTC)")
    remarks: Optional[str] = Field(None, max_length=500, description="Optional notes or remarks")

    @model_validator(mode="after")
    def validate_times_and_status(self) -> "AttendanceMarkEntry":
        # Rule: status=absent or status=leave -> check_in_time and check_out_time must be null
        if self.status in (AttendanceStatusEnum.ABSENT, AttendanceStatusEnum.LEAVE):
            if self.check_in_time is not None or self.check_out_time is not None:
                raise ValueError("check_in_time and check_out_time must be null for absent or leave status")

        # Rule: if check_in_time and check_out_time both provided -> check_out > check_in
        if self.check_in_time is not None and self.check_out_time is not None:
            if self.check_out_time <= self.check_in_time:
                raise ValueError("check_out_time must be strictly after check_in_time")

        return self


class AttendanceMarkRequest(AttendanceMarkEntry):
    attendance_date: date = Field(..., description="Date of attendance")


class AttendanceBulkMarkRequest(BaseModel):
    attendance_date: date = Field(..., description="Date of attendance for all entries")
    entries: List[AttendanceMarkEntry] = Field(..., min_length=1, description="List of staff attendance entries")


class AttendanceCorrectionRequest(BaseModel):
    status: AttendanceStatusEnum = Field(..., description="Corrected attendance status")
    check_in_time: Optional[datetime] = Field(None, description="Corrected check-in timestamp")
    check_out_time: Optional[datetime] = Field(None, description="Corrected check-out timestamp")
    remarks: Optional[str] = Field(None, max_length=500, description="Optional notes or remarks")
    reason: str = Field(..., min_length=10, max_length=500, description="Mandatory correction reason (min 10 chars)")

    @model_validator(mode="after")
    def validate_times_and_status(self) -> "AttendanceCorrectionRequest":
        if self.status in (AttendanceStatusEnum.ABSENT, AttendanceStatusEnum.LEAVE):
            if self.check_in_time is not None or self.check_out_time is not None:
                raise ValueError("check_in_time and check_out_time must be null for absent or leave status")

        if self.check_in_time is not None and self.check_out_time is not None:
            if self.check_out_time <= self.check_in_time:
                raise ValueError("check_out_time must be strictly after check_in_time")

        return self


class AttendanceResponse(BaseModel):
    id: UUID
    facility_id: UUID
    user_id: UUID
    attendance_date: date
    status: AttendanceStatusEnum
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    remarks: Optional[str] = None
    recorded_by: UUID
    recorded_at: datetime
    last_modified_by: Optional[UUID] = None
    last_modified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RosterItemResponse(BaseModel):
    user_id: UUID
    full_name: str
    user_email: str
    status: Optional[AttendanceStatusEnum] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    remarks: Optional[str] = None
    attendance_id: Optional[UUID] = None


class AttendanceHistoryListResponse(BaseModel):
    items: List[AttendanceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AttendanceSummaryResponse(BaseModel):
    total_marked: int
    present_count: int
    absent_count: int
    leave_count: int
    half_day_count: int
    on_duty_count: int
    attendance_rate: float
