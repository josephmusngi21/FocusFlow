from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas.task import (
    GoalCreate, GoalUpdate, GoalResponse, 
    ProductivityMetricResponse, ProductivitySummaryResponse,
    UserPreferencesUpdate, UserPreferencesResponse
)
from app.services.goal_service import (
    get_goal, get_goals, create_goal, update_goal, delete_goal,
    calculate_goal_progress, get_productivity_metrics, 
    get_user_preferences, update_user_preferences,
    calculate_productivity_summary
)

router = APIRouter()

# User preferences endpoints (must come before /{goal_id} route)
@router.get("/preferences", response_model=UserPreferencesResponse)
def get_preferences(db: Session = Depends(get_db)):
    """Get user preferences"""
    preferences = get_user_preferences(db)
    if not preferences:
        # Create default preferences if none exist
        from app.services.goal_service import create_default_user_preferences
        preferences = create_default_user_preferences(db)
    
    return preferences

@router.put("/preferences", response_model=UserPreferencesResponse)
def update_preferences(
    preferences_update: UserPreferencesUpdate, 
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    preferences = update_user_preferences(db, preferences_update)
    return preferences

# Productivity metrics endpoints
@router.get("/metrics/daily", response_model=List[ProductivityMetricResponse])
def get_daily_metrics(
    start_date: str = None, 
    end_date: str = None, 
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get daily productivity metrics"""
    
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    if not start_date:
        start_datetime = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days-1)
        start_date = start_datetime.strftime("%Y-%m-%d")
    
    metrics = get_productivity_metrics(db, start_date, end_date)
    return metrics

@router.get("/metrics/summary", response_model=ProductivitySummaryResponse)
def get_productivity_summary(
    period: str = "weekly",
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """Get productivity summary for a period"""
    
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    if period == "weekly":
        days = 7
    elif period == "monthly":
        days = 30
    else:  # daily
        days = 1
    
    if not start_date:
        start_datetime = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days-1)
        start_date = start_datetime.strftime("%Y-%m-%d")
    
    metrics = get_productivity_metrics(db, start_date, end_date)
    summary_data = calculate_productivity_summary(metrics, period)
    
    return ProductivitySummaryResponse(
        period=period,
        start_date=start_date,
        end_date=end_date,
        **summary_data
    )

# Goal endpoints
@router.get("/", response_model=List[GoalResponse])
def list_goals(skip: int = 0, limit: int = 100, is_active: bool = True, db: Session = Depends(get_db)):
    """List all goals"""
    goals = get_goals(db, skip=skip, limit=limit, is_active=is_active)
    
    # Add progress percentage to each goal
    goal_responses = []
    for goal in goals:
        goal_dict = goal.__dict__.copy()
        goal_dict['progress_percentage'] = calculate_goal_progress(goal)
        goal_responses.append(GoalResponse(**goal_dict))
    
    return goal_responses

@router.post("/", response_model=GoalResponse)
def create_new_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal"""
    db_goal = create_goal(db, goal)
    goal_dict = db_goal.__dict__.copy()
    goal_dict['progress_percentage'] = calculate_goal_progress(db_goal)
    return GoalResponse(**goal_dict)

@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal_by_id(goal_id: str, db: Session = Depends(get_db)):
    """Get a specific goal by ID"""
    goal = get_goal(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    goal_dict = goal.__dict__.copy()
    goal_dict['progress_percentage'] = calculate_goal_progress(goal)
    return GoalResponse(**goal_dict)

@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal_by_id(goal_id: str, goal_update: GoalUpdate, db: Session = Depends(get_db)):
    """Update a specific goal"""
    goal = update_goal(db, goal_id, goal_update)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    goal_dict = goal.__dict__.copy()
    goal_dict['progress_percentage'] = calculate_goal_progress(goal)
    return GoalResponse(**goal_dict)

@router.delete("/{goal_id}")
def delete_goal_by_id(goal_id: str, db: Session = Depends(get_db)):
    """Delete a specific goal"""
    if not delete_goal(db, goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal deleted successfully"}