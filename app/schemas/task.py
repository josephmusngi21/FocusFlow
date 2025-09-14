from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    duration: int = Field(..., gt=0, description="Duration in minutes")
    priority: int = Field(..., ge=1, le=10, description="Priority level 1-10")
    energy_level: int = Field(..., ge=1, le=10, description="Required energy level 1-10")
    time_window_start: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    time_window_end: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    duration: Optional[int] = Field(None, gt=0)
    priority: Optional[int] = Field(None, ge=1, le=10)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    time_window_start: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    time_window_end: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    status: Optional[str] = Field(None, pattern=r'^(pending|scheduled|completed|cancelled)$')

class TaskResponse(TaskBase):
    id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ScheduleItemResponse(BaseModel):
    id: str
    task_id: str
    task_title: str
    scheduled_start: str
    scheduled_end: str
    energy_cost: float
    created_at: datetime

    class Config:
        from_attributes = True

class ScheduleRequest(BaseModel):
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    work_start: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    work_end: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    max_energy: float = Field(default=10.0, ge=1.0, le=10.0)
    break_duration: int = Field(default=15, ge=5, le=60, description="Break duration in minutes")

class ScheduleResponse(BaseModel):
    date: str
    schedule_items: List[ScheduleItemResponse]
    total_tasks: int
    total_duration: int
    energy_efficiency: float