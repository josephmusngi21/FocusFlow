from sqlalchemy import Column, Integer, String, DateTime, Float, Text
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())