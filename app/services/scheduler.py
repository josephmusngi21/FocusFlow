from typing import List, Tuple
from datetime import datetime, timedelta
from app.models.task import Task
import math

class TaskScheduler:
    def __init__(self, max_energy: float = 10.0, break_duration: int = 15):
        self.max_energy = max_energy
        self.break_duration = break_duration
        self.current_energy = max_energy
        
    def time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to HH:MM"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def calculate_fatigue_factor(self, current_time: int, start_time: int) -> float:
        """Calculate fatigue factor based on time elapsed"""
        elapsed_hours = (current_time - start_time) / 60
        # Exponential fatigue: energy decreases more rapidly over time
        fatigue = max(0.1, 1.0 - (elapsed_hours / 8) ** 1.5)
        return fatigue
    
    def calculate_task_priority_score(self, task: Task, current_time: int, start_time: int) -> float:
        """Calculate priority score for task scheduling"""
        base_priority = task.priority
        energy_requirement = task.energy_level
        
        # Fatigue factor reduces available energy over time
        fatigue_factor = self.calculate_fatigue_factor(current_time, start_time)
        available_energy = self.max_energy * fatigue_factor
        
        # Check if we have enough energy for this task
        if available_energy < energy_requirement:
            return 0  # Cannot do this task now
        
        # Time window preference bonus
        time_window_bonus = 0
        if task.time_window_start and task.time_window_end:
            window_start = self.time_to_minutes(task.time_window_start)
            window_end = self.time_to_minutes(task.time_window_end)
            if window_start <= current_time <= window_end:
                time_window_bonus = 2  # Bonus for scheduling in preferred window
        
        # Priority score: higher priority, time window bonus, energy efficiency
        energy_efficiency = 1.0 - (energy_requirement / self.max_energy)
        priority_score = base_priority + time_window_bonus + energy_efficiency
        
        return priority_score
    
    def needs_break(self, last_break_time: int, current_time: int, energy_spent: float) -> bool:
        """Determine if a break is needed"""
        time_since_break = current_time - last_break_time
        # Need break after 2 hours or when energy is too low
        return time_since_break >= 120 or energy_spent >= (self.max_energy * 0.7)
    
    def schedule_tasks(self, tasks: List[Task], work_start: str, work_end: str, date: str) -> List[dict]:
        """
        Greedy algorithm to schedule tasks optimally
        Returns list of scheduled tasks with timing and energy info
        """
        start_minutes = self.time_to_minutes(work_start)
        end_minutes = self.time_to_minutes(work_end)
        current_time = start_minutes
        last_break_time = start_minutes
        energy_spent = 0.0
        
        scheduled_tasks = []
        remaining_tasks = [task for task in tasks if task.status == "pending"]
        
        while current_time < end_minutes and remaining_tasks:
            # Check if we need a break
            if self.needs_break(last_break_time, current_time, energy_spent):
                # Schedule a break
                break_end = current_time + self.break_duration
                if break_end > end_minutes:
                    break  # No time for break
                
                current_time = break_end
                last_break_time = current_time
                energy_spent = max(0, energy_spent - 2.0)  # Restore some energy
                continue
            
            # Find the best task to schedule next
            best_task = None
            best_score = 0
            
            for task in remaining_tasks:
                score = self.calculate_task_priority_score(task, current_time, start_minutes)
                if score > best_score:
                    best_task = task
                    best_score = score
            
            if not best_task:
                # No suitable task found, advance time
                current_time += 30  # Try again in 30 minutes
                continue
            
            # Schedule the best task
            task_end = current_time + best_task.duration
            if task_end > end_minutes:
                # Task doesn't fit in remaining time
                remaining_tasks.remove(best_task)
                continue
            
            # Calculate energy cost
            fatigue_factor = self.calculate_fatigue_factor(current_time, start_minutes)
            energy_cost = best_task.energy_level / fatigue_factor
            
            scheduled_tasks.append({
                'task_id': best_task.id,
                'task_title': best_task.title,
                'scheduled_start': self.minutes_to_time(current_time),
                'scheduled_end': self.minutes_to_time(task_end),
                'energy_cost': round(energy_cost, 2),
                'date': date
            })
            
            # Update state
            current_time = task_end
            energy_spent += energy_cost
            remaining_tasks.remove(best_task)
        
        return scheduled_tasks
    
    def calculate_schedule_efficiency(self, scheduled_tasks: List[dict]) -> float:
        """Calculate overall efficiency of the schedule"""
        if not scheduled_tasks:
            return 0.0
        
        total_energy_cost = sum(task['energy_cost'] for task in scheduled_tasks)
        total_duration = sum(
            self.time_to_minutes(task['scheduled_end']) - self.time_to_minutes(task['scheduled_start']) 
            for task in scheduled_tasks
        )
        
        if total_duration == 0:
            return 0.0
        
        # Efficiency: lower energy cost per minute is better
        efficiency = max(0, 1.0 - (total_energy_cost / (total_duration / 60)))
        return round(efficiency, 2)