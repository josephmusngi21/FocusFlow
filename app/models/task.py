from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=False)  # Duration in minutes
    priority = Column(Integer, nullable=False)  # Priority level 1-10
    energy_level = Column(Integer, nullable=False)  # Required energy level 1-10
    time_window_start = Column(String, nullable=True)  # Preferred start time (HH:MM)
    time_window_end = Column(String, nullable=True)  # Preferred end time (HH:MM)
    status = Column(String, default="pending")  # pending, scheduled, completed, cancelled
    calendar_event_id = Column(String, nullable=True)  # Google Calendar event ID
    completed_at = Column(DateTime(timezone=True), nullable=True)
    actual_duration = Column(Integer, nullable=True)  # Actual time spent in minutes
    goal_id = Column(String, nullable=True)  # Associated goal ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String, nullable=False)  # Date in YYYY-MM-DD format
    task_id = Column(String, nullable=False)
    scheduled_start = Column(String, nullable=False)  # Scheduled start time (HH:MM)
    scheduled_end = Column(String, nullable=False)  # Scheduled end time (HH:MM)
    energy_cost = Column(Float, default=0.0)  # Energy consumed by this task
    calendar_event_id = Column(String, nullable=True)  # Google Calendar event ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_value = Column(Float, nullable=False)  # Target value (hours, tasks, etc.)
    current_value = Column(Float, default=0.0)  # Current progress
    unit = Column(String, default="tasks")  # Unit of measurement: tasks, hours, points
    deadline = Column(String, nullable=True)  # Deadline in YYYY-MM-DD format
    category = Column(String, nullable=True)  # Goal category
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ProductivityMetric(Base):
    __tablename__ = "productivity_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String, nullable=False)  # Date in YYYY-MM-DD format
    tasks_completed = Column(Integer, default=0)
    tasks_scheduled = Column(Integer, default=0)
    total_productive_time = Column(Float, default=0.0)  # In hours
    average_energy_usage = Column(Float, default=0.0)
    schedule_adherence = Column(Float, default=0.0)  # Percentage
    productivity_score = Column(Float, default=0.0)  # Overall score 1-10
    break_time = Column(Float, default=0.0)  # Break time in hours
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="default")  # For future multi-user support
    work_start_time = Column(String, default="08:00")
    work_end_time = Column(String, default="17:00")
    preferred_break_duration = Column(Integer, default=15)
    max_energy_level = Column(Float, default=10.0)
    notification_enabled = Column(Boolean, default=True)
    calendar_sync_enabled = Column(Boolean, default=False)
    energy_decay_rate = Column(Float, default=1.5)  # How quickly energy depletes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())