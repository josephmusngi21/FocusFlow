from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.task import ScheduleRequest, ScheduleResponse, ScheduleItemResponse
from app.services.task_service import (
    get_pending_tasks, create_schedule_item, get_schedule_by_date, 
    clear_schedule_by_date, get_task
)
from app.services.scheduler import TaskScheduler

router = APIRouter()

@router.post("/generate", response_model=ScheduleResponse)
def generate_schedule(schedule_request: ScheduleRequest, db: Session = Depends(get_db)):
    """Generate an optimized schedule for the given date"""
    
    # Get all pending tasks
    pending_tasks = get_pending_tasks(db)
    
    if not pending_tasks:
        return ScheduleResponse(
            date=schedule_request.date,
            schedule_items=[],
            total_tasks=0,
            total_duration=0,
            energy_efficiency=0.0
        )
    
    # Clear existing schedule for this date
    clear_schedule_by_date(db, schedule_request.date)
    
    # Initialize scheduler
    scheduler = TaskScheduler(
        max_energy=schedule_request.max_energy,
        break_duration=schedule_request.break_duration
    )
    
    # Generate schedule
    scheduled_tasks = scheduler.schedule_tasks(
        pending_tasks,
        schedule_request.work_start,
        schedule_request.work_end,
        schedule_request.date
    )
    
    # Save schedule to database
    schedule_items = []
    for task_data in scheduled_tasks:
        schedule_item = create_schedule_item(
            db,
            task_data['task_id'],
            task_data['date'],
            task_data['scheduled_start'],
            task_data['scheduled_end'],
            task_data['energy_cost']
        )
        
        schedule_items.append(ScheduleItemResponse(
            id=schedule_item.id,
            task_id=schedule_item.task_id,
            task_title=task_data['task_title'],
            scheduled_start=schedule_item.scheduled_start,
            scheduled_end=schedule_item.scheduled_end,
            energy_cost=schedule_item.energy_cost,
            created_at=schedule_item.created_at
        ))
        
        # Update task status to scheduled
        task = get_task(db, task_data['task_id'])
        if task:
            task.status = "scheduled"
            db.commit()
    
    # Calculate metrics
    total_duration = sum(
        scheduler.time_to_minutes(item.scheduled_end) - scheduler.time_to_minutes(item.scheduled_start)
        for item in schedule_items
    )
    energy_efficiency = scheduler.calculate_schedule_efficiency(scheduled_tasks)
    
    return ScheduleResponse(
        date=schedule_request.date,
        schedule_items=schedule_items,
        total_tasks=len(schedule_items),
        total_duration=total_duration,
        energy_efficiency=energy_efficiency
    )

@router.get("/{date}", response_model=ScheduleResponse)
def get_schedule(date: str, db: Session = Depends(get_db)):
    """Get the schedule for a specific date"""
    
    schedule_items_db = get_schedule_by_date(db, date)
    
    schedule_items = []
    for item in schedule_items_db:
        task = get_task(db, item.task_id)
        task_title = task.title if task else "Unknown Task"
        
        schedule_items.append(ScheduleItemResponse(
            id=item.id,
            task_id=item.task_id,
            task_title=task_title,
            scheduled_start=item.scheduled_start,
            scheduled_end=item.scheduled_end,
            energy_cost=item.energy_cost,
            created_at=item.created_at
        ))
    
    # Calculate metrics
    if schedule_items:
        scheduler = TaskScheduler()
        total_duration = sum(
            scheduler.time_to_minutes(item.scheduled_end) - scheduler.time_to_minutes(item.scheduled_start)
            for item in schedule_items
        )
        scheduled_tasks_data = [
            {
                'scheduled_start': item.scheduled_start,
                'scheduled_end': item.scheduled_end,
                'energy_cost': item.energy_cost
            }
            for item in schedule_items
        ]
        energy_efficiency = scheduler.calculate_schedule_efficiency(scheduled_tasks_data)
    else:
        total_duration = 0
        energy_efficiency = 0.0
    
    return ScheduleResponse(
        date=date,
        schedule_items=schedule_items,
        total_tasks=len(schedule_items),
        total_duration=total_duration,
        energy_efficiency=energy_efficiency
    )