from sqlalchemy.orm import Session
from app.models.task import Goal, ProductivityMetric, UserPreference
from app.schemas.task import GoalCreate, GoalUpdate, UserPreferencesUpdate
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid

def get_goal(db: Session, goal_id: str) -> Optional[Goal]:
    return db.query(Goal).filter(Goal.id == goal_id).first()

def get_goals(db: Session, skip: int = 0, limit: int = 100, is_active: bool = True) -> List[Goal]:
    query = db.query(Goal)
    if is_active is not None:
        query = query.filter(Goal.is_active == is_active)
    return query.offset(skip).limit(limit).all()

def create_goal(db: Session, goal: GoalCreate) -> Goal:
    db_goal = Goal(
        id=str(uuid.uuid4()),
        **goal.model_dump()
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def update_goal(db: Session, goal_id: str, goal_update: GoalUpdate) -> Optional[Goal]:
    db_goal = get_goal(db, goal_id)
    if db_goal:
        update_data = goal_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_goal, field, value)
        db.commit()
        db.refresh(db_goal)
    return db_goal

def update_goal_progress(db: Session, goal_id: str, progress_increment: float) -> Optional[Goal]:
    """Increment goal progress"""
    db_goal = get_goal(db, goal_id)
    if db_goal:
        db_goal.current_value += progress_increment
        # Ensure current_value doesn't exceed target
        if db_goal.current_value >= db_goal.target_value:
            db_goal.current_value = db_goal.target_value
        db.commit()
        db.refresh(db_goal)
    return db_goal

def delete_goal(db: Session, goal_id: str) -> bool:
    db_goal = get_goal(db, goal_id)
    if db_goal:
        db.delete(db_goal)
        db.commit()
        return True
    return False

def calculate_goal_progress(goal: Goal) -> float:
    """Calculate goal progress percentage"""
    if goal.target_value <= 0:
        return 0.0
    return min(100.0, (goal.current_value / goal.target_value) * 100)

def get_productivity_metric(db: Session, date: str) -> Optional[ProductivityMetric]:
    return db.query(ProductivityMetric).filter(ProductivityMetric.date == date).first()

def get_productivity_metrics(db: Session, start_date: str, end_date: str) -> List[ProductivityMetric]:
    return db.query(ProductivityMetric).filter(
        ProductivityMetric.date >= start_date,
        ProductivityMetric.date <= end_date
    ).order_by(ProductivityMetric.date).all()

def create_or_update_productivity_metric(
    db: Session, 
    date: str, 
    tasks_completed: int = 0,
    tasks_scheduled: int = 0,
    total_productive_time: float = 0.0,
    average_energy_usage: float = 0.0,
    schedule_adherence: float = 0.0,
    break_time: float = 0.0
) -> ProductivityMetric:
    """Create or update productivity metrics for a date"""
    
    metric = get_productivity_metric(db, date)
    
    if metric:
        # Update existing metric
        metric.tasks_completed = tasks_completed
        metric.tasks_scheduled = tasks_scheduled
        metric.total_productive_time = total_productive_time
        metric.average_energy_usage = average_energy_usage
        metric.schedule_adherence = schedule_adherence
        metric.break_time = break_time
        metric.productivity_score = calculate_productivity_score(
            tasks_completed, tasks_scheduled, schedule_adherence, total_productive_time
        )
    else:
        # Create new metric
        metric = ProductivityMetric(
            id=str(uuid.uuid4()),
            date=date,
            tasks_completed=tasks_completed,
            tasks_scheduled=tasks_scheduled,
            total_productive_time=total_productive_time,
            average_energy_usage=average_energy_usage,
            schedule_adherence=schedule_adherence,
            break_time=break_time,
            productivity_score=calculate_productivity_score(
                tasks_completed, tasks_scheduled, schedule_adherence, total_productive_time
            )
        )
        db.add(metric)
    
    db.commit()
    db.refresh(metric)
    return metric

def calculate_productivity_score(
    tasks_completed: int, 
    tasks_scheduled: int, 
    schedule_adherence: float, 
    total_productive_time: float
) -> float:
    """Calculate overall productivity score (1-10)"""
    
    # Base score from task completion rate
    completion_rate = tasks_completed / max(tasks_scheduled, 1)
    completion_score = min(10, completion_rate * 8)  # Max 8 points for completion
    
    # Bonus for schedule adherence
    adherence_bonus = (schedule_adherence / 100) * 1.5  # Max 1.5 points
    
    # Bonus for productive time (assuming 8 hours is excellent)
    time_bonus = min(0.5, (total_productive_time / 8) * 0.5)  # Max 0.5 points
    
    total_score = completion_score + adherence_bonus + time_bonus
    return round(min(10.0, max(1.0, total_score)), 1)

def get_user_preferences(db: Session, user_id: str = "default") -> Optional[UserPreference]:
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

def create_default_user_preferences(db: Session, user_id: str = "default") -> UserPreference:
    """Create default user preferences"""
    preferences = UserPreference(
        id=str(uuid.uuid4()),
        user_id=user_id
    )
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences

def update_user_preferences(
    db: Session, 
    preferences_update: UserPreferencesUpdate, 
    user_id: str = "default"
) -> UserPreference:
    """Update user preferences"""
    preferences = get_user_preferences(db, user_id)
    
    if not preferences:
        preferences = create_default_user_preferences(db, user_id)
    
    update_data = preferences_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    return preferences

def calculate_productivity_summary(
    metrics: List[ProductivityMetric], 
    period: str = "weekly"
) -> Dict:
    """Calculate productivity summary for a period"""
    
    if not metrics:
        return {
            "total_tasks_completed": 0,
            "total_productive_hours": 0.0,
            "average_productivity_score": 0.0,
            "streak_days": 0,
            "best_day": None,
            "improvement_suggestions": ["Start tracking your productivity to see insights!"]
        }
    
    total_tasks = sum(m.tasks_completed for m in metrics)
    total_hours = sum(m.total_productive_time for m in metrics)
    avg_score = sum(m.productivity_score for m in metrics) / len(metrics)
    
    # Find best day
    best_metric = max(metrics, key=lambda m: m.productivity_score)
    best_day = best_metric.date
    
    # Calculate streak (consecutive days with productivity_score >= 6)
    streak = 0
    for metric in reversed(metrics):
        if metric.productivity_score >= 6.0:
            streak += 1
        else:
            break
    
    # Generate improvement suggestions
    suggestions = []
    if avg_score < 6.0:
        suggestions.append("Try breaking large tasks into smaller, manageable pieces")
    if total_hours / len(metrics) < 4:
        suggestions.append("Consider increasing your daily productive time goals")
    if any(m.schedule_adherence < 70 for m in metrics):
        suggestions.append("Focus on improving schedule adherence - start with realistic time estimates")
    
    return {
        "total_tasks_completed": total_tasks,
        "total_productive_hours": round(total_hours, 1),
        "average_productivity_score": round(avg_score, 1),
        "streak_days": streak,
        "best_day": best_day,
        "improvement_suggestions": suggestions or ["Great work! Keep maintaining your productivity momentum!"]
    }