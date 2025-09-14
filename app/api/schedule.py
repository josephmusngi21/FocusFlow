from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.task import ScheduleRequest, ScheduleResponse, ScheduleItemResponse
from app.services.task_service import (
    get_pending_tasks, create_schedule_item, get_schedule_by_date, 
    clear_schedule_by_date, get_task, update_task
)
from app.services.scheduler import TaskScheduler
from app.services.google_calendar import GoogleCalendarIntegration
from app.services.twilio_notifications import TwilioNotificationService
from app.services.goal_service import (
    get_user_preferences, create_or_update_productivity_metric
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=ScheduleResponse)
def generate_schedule(schedule_request: ScheduleRequest, db: Session = Depends(get_db)):
    """Generate an optimized schedule for the given date with optional integrations"""
    
    # Get all pending tasks
    pending_tasks = get_pending_tasks(db)
    
    if not pending_tasks:
        return ScheduleResponse(
            date=schedule_request.date,
            schedule_items=[],
            total_tasks=0,
            total_duration=0,
            energy_efficiency=0.0,
            calendar_synced=False,
            notifications_sent=False
        )
    
    # Get user preferences
    user_prefs = get_user_preferences(db)
    if user_prefs:
        # Use user preferences if available
        max_energy = user_prefs.max_energy_level
        break_duration = user_prefs.preferred_break_duration
    else:
        # Use request defaults
        max_energy = schedule_request.max_energy
        break_duration = schedule_request.break_duration
    
    # Clear existing schedule for this date
    clear_schedule_by_date(db, schedule_request.date)
    
    # Initialize scheduler
    scheduler = TaskScheduler(
        max_energy=max_energy,
        break_duration=break_duration
    )
    
    # Initialize integrations
    calendar_integration = GoogleCalendarIntegration()
    notification_service = TwilioNotificationService()
    
    # Check for existing calendar events if calendar sync is enabled
    busy_times = []
    if schedule_request.sync_to_calendar and calendar_integration.is_available():
        busy_times = calendar_integration.get_busy_times(
            schedule_request.date,
            schedule_request.work_start,
            schedule_request.work_end
        )
        logger.info(f"Found {len(busy_times)} busy times from calendar")
    
    # Generate schedule
    scheduled_tasks = scheduler.schedule_tasks(
        pending_tasks,
        schedule_request.work_start,
        schedule_request.work_end,
        schedule_request.date
    )
    
    # Save schedule to database and sync to calendar
    schedule_items = []
    calendar_synced = False
    
    for task_data in scheduled_tasks:
        # Create schedule item in database
        schedule_item = create_schedule_item(
            db,
            task_data['task_id'],
            task_data['date'],
            task_data['scheduled_start'],
            task_data['scheduled_end'],
            task_data['energy_cost']
        )
        
        # Sync to Google Calendar if requested
        calendar_event_id = None
        if schedule_request.sync_to_calendar and calendar_integration.is_available():
            try:
                task = get_task(db, task_data['task_id'])
                if task:
                    calendar_event_id = calendar_integration.create_event(
                        title=task.title,
                        start_time=task_data['scheduled_start'],
                        end_time=task_data['scheduled_end'],
                        date=task_data['date'],
                        description=task.description or f"Scheduled by FocusFlow\nPriority: {task.priority}\nEnergy: {task.energy_level}"
                    )
                    if calendar_event_id:
                        # Update schedule item with calendar event ID
                        schedule_item.calendar_event_id = calendar_event_id
                        # Update task with calendar event ID
                        task.calendar_event_id = calendar_event_id
                        db.commit()
                        calendar_synced = True
            except Exception as e:
                logger.error(f"Failed to sync task to calendar: {e}")
        
        schedule_items.append(ScheduleItemResponse(
            id=schedule_item.id,
            task_id=schedule_item.task_id,
            task_title=task_data['task_title'],
            scheduled_start=schedule_item.scheduled_start,
            scheduled_end=schedule_item.scheduled_end,
            energy_cost=schedule_item.energy_cost,
            calendar_event_id=calendar_event_id,
            created_at=schedule_item.created_at
        ))
        
        # Update task status to scheduled
        task = get_task(db, task_data['task_id'])
        if task:
            task.status = "scheduled"
            db.commit()
    
    # Send notifications if requested
    notifications_sent = False
    if schedule_request.send_notifications and notification_service.is_available():
        try:
            message_id = notification_service.send_daily_schedule_reminder(
                scheduled_tasks, schedule_request.date
            )
            if message_id:
                notifications_sent = True
                logger.info(f"Schedule reminder sent: {message_id}")
        except Exception as e:
            logger.error(f"Failed to send schedule notification: {e}")
    
    # Calculate metrics
    total_duration = sum(
        scheduler.time_to_minutes(item.scheduled_end) - scheduler.time_to_minutes(item.scheduled_start)
        for item in schedule_items
    )
    energy_efficiency = scheduler.calculate_schedule_efficiency(scheduled_tasks)
    
    # Update productivity metrics
    try:
        create_or_update_productivity_metric(
            db,
            date=schedule_request.date,
            tasks_scheduled=len(schedule_items),
            total_productive_time=total_duration / 60.0,  # Convert to hours
            average_energy_usage=sum(item.energy_cost for item in schedule_items) / max(len(schedule_items), 1)
        )
    except Exception as e:
        logger.error(f"Failed to update productivity metrics: {e}")
    
    return ScheduleResponse(
        date=schedule_request.date,
        schedule_items=schedule_items,
        total_tasks=len(schedule_items),
        total_duration=total_duration,
        energy_efficiency=energy_efficiency,
        calendar_synced=calendar_synced,
        notifications_sent=notifications_sent
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
            calendar_event_id=item.calendar_event_id,
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
        energy_efficiency=energy_efficiency,
        calendar_synced=any(item.calendar_event_id for item in schedule_items),
        notifications_sent=False  # We don't track notification history yet
    )

@router.post("/{date}/notify")
def send_schedule_notification(date: str, db: Session = Depends(get_db)):
    """Send notification for schedule"""
    
    # Get schedule for the date
    schedule_items_db = get_schedule_by_date(db, date)
    
    if not schedule_items_db:
        raise HTTPException(status_code=404, detail="No schedule found for this date")
    
    # Prepare schedule data for notification
    scheduled_tasks = []
    for item in schedule_items_db:
        task = get_task(db, item.task_id)
        if task:
            scheduled_tasks.append({
                'task_title': task.title,
                'scheduled_start': item.scheduled_start,
                'scheduled_end': item.scheduled_end,
                'energy_cost': item.energy_cost,
                'date': date
            })
    
    # Send notification
    notification_service = TwilioNotificationService()
    if not notification_service.is_available():
        raise HTTPException(status_code=503, detail="Notification service not available")
    
    try:
        message_id = notification_service.send_daily_schedule_reminder(scheduled_tasks, date)
        if message_id:
            return {"message": "Schedule notification sent successfully", "message_id": message_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")
    except Exception as e:
        logger.error(f"Failed to send schedule notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))