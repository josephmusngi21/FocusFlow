from sqlalchemy.orm import Session
from app.models.task import Task, Schedule
from app.schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional
import uuid

def get_task(db: Session, task_id: str) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()

def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[Task]:
    return db.query(Task).offset(skip).limit(limit).all()

def get_pending_tasks(db: Session) -> List[Task]:
    return db.query(Task).filter(Task.status == "pending").all()

def create_task(db: Session, task: TaskCreate) -> Task:
    db_task = Task(
        id=str(uuid.uuid4()),
        **task.model_dump()
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: str, task_update: TaskUpdate) -> Optional[Task]:
    db_task = get_task(db, task_id)
    if db_task:
        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: str) -> bool:
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False

def create_schedule_item(db: Session, task_id: str, date: str, start_time: str, end_time: str, energy_cost: float) -> Schedule:
    schedule_item = Schedule(
        id=str(uuid.uuid4()),
        task_id=task_id,
        date=date,
        scheduled_start=start_time,
        scheduled_end=end_time,
        energy_cost=energy_cost
    )
    db.add(schedule_item)
    db.commit()
    db.refresh(schedule_item)
    return schedule_item

def get_schedule_by_date(db: Session, date: str) -> List[Schedule]:
    return db.query(Schedule).filter(Schedule.date == date).all()

def clear_schedule_by_date(db: Session, date: str):
    db.query(Schedule).filter(Schedule.date == date).delete()
    db.commit()