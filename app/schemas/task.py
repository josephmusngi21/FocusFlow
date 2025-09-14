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
    goal_id: Optional[str] = None

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
    actual_duration: Optional[int] = Field(None, gt=0)
    goal_id: Optional[str] = None

class TaskResponse(TaskBase):
    id: str
    status: str
    calendar_event_id: Optional[str]
    completed_at: Optional[datetime]
    actual_duration: Optional[int]
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
    calendar_event_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ScheduleRequest(BaseModel):
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    work_start: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    work_end: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    max_energy: float = Field(default=10.0, ge=1.0, le=10.0)
    break_duration: int = Field(default=15, ge=5, le=60, description="Break duration in minutes")
    sync_to_calendar: bool = Field(default=False, description="Sync schedule to Google Calendar")
    send_notifications: bool = Field(default=False, description="Send notifications via Twilio")

class ScheduleResponse(BaseModel):
    date: str
    schedule_items: List[ScheduleItemResponse]
    total_tasks: int
    total_duration: int
    energy_efficiency: float
    calendar_synced: bool = False
    notifications_sent: bool = False

# Goal schemas
class GoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_value: float = Field(..., gt=0)
    unit: str = Field(default="tasks", pattern=r'^(tasks|hours|points)$')
    deadline: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    category: Optional[str] = None

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_value: Optional[float] = Field(None, gt=0)
    current_value: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, pattern=r'^(tasks|hours|points)$')
    deadline: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    category: Optional[str] = None
    is_active: Optional[bool] = None

class GoalResponse(GoalBase):
    id: str
    current_value: float
    is_active: bool
    progress_percentage: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Productivity metrics schemas
class ProductivityMetricResponse(BaseModel):
    id: str
    date: str
    tasks_completed: int
    tasks_scheduled: int
    total_productive_time: float
    average_energy_usage: float
    schedule_adherence: float
    productivity_score: float
    break_time: float
    created_at: datetime

    class Config:
        from_attributes = True

class ProductivitySummaryResponse(BaseModel):
    period: str  # daily, weekly, monthly
    start_date: str
    end_date: str
    total_tasks_completed: int
    total_productive_hours: float
    average_productivity_score: float
    streak_days: int
    best_day: Optional[str]
    improvement_suggestions: List[str]

# User preferences schemas
class UserPreferencesUpdate(BaseModel):
    work_start_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    work_end_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    preferred_break_duration: Optional[int] = Field(None, ge=5, le=60)
    max_energy_level: Optional[float] = Field(None, ge=1.0, le=10.0)
    notification_enabled: Optional[bool] = None
    calendar_sync_enabled: Optional[bool] = None
    energy_decay_rate: Optional[float] = Field(None, ge=0.1, le=5.0)

class UserPreferencesResponse(BaseModel):
    id: str
    user_id: str
    work_start_time: str
    work_end_time: str
    preferred_break_duration: int
    max_energy_level: float
    notification_enabled: bool
    calendar_sync_enabled: bool
    energy_decay_rate: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True