import pytest
from app.services.scheduler import TaskScheduler
from app.models.task import Task

class MockTask:
    def __init__(self, id, title, duration, priority, energy_level, time_window_start=None, time_window_end=None, status="pending"):
        self.id = id
        self.title = title
        self.duration = duration
        self.priority = priority
        self.energy_level = energy_level
        self.time_window_start = time_window_start
        self.time_window_end = time_window_end
        self.status = status

def test_time_conversion():
    scheduler = TaskScheduler()
    
    # Test time_to_minutes
    assert scheduler.time_to_minutes("08:00") == 480
    assert scheduler.time_to_minutes("12:30") == 750
    assert scheduler.time_to_minutes("17:45") == 1065
    
    # Test minutes_to_time
    assert scheduler.minutes_to_time(480) == "08:00"
    assert scheduler.minutes_to_time(750) == "12:30"
    assert scheduler.minutes_to_time(1065) == "17:45"

def test_fatigue_factor():
    scheduler = TaskScheduler()
    start_time = 480  # 08:00
    
    # At start of day
    assert scheduler.calculate_fatigue_factor(480, start_time) == 1.0
    
    # After 4 hours
    fatigue_4h = scheduler.calculate_fatigue_factor(720, start_time)  # 12:00
    assert 0.1 <= fatigue_4h < 1.0
    
    # After 8 hours
    fatigue_8h = scheduler.calculate_fatigue_factor(960, start_time)  # 16:00
    assert fatigue_8h < fatigue_4h

def test_task_priority_score():
    scheduler = TaskScheduler(max_energy=10.0)
    start_time = 480  # 08:00
    current_time = 540  # 09:00
    
    # High priority task
    high_priority_task = MockTask("1", "High Priority", 60, 9, 5)
    score_high = scheduler.calculate_task_priority_score(high_priority_task, current_time, start_time)
    
    # Low priority task
    low_priority_task = MockTask("2", "Low Priority", 60, 3, 5)
    score_low = scheduler.calculate_task_priority_score(low_priority_task, current_time, start_time)
    
    assert score_high > score_low

def test_time_window_bonus():
    scheduler = TaskScheduler(max_energy=10.0)
    start_time = 480  # 08:00
    current_time = 540  # 09:00
    
    # Task with time window that includes current time
    task_in_window = MockTask("1", "In Window", 60, 5, 3, "08:30", "10:00")
    score_in_window = scheduler.calculate_task_priority_score(task_in_window, current_time, start_time)
    
    # Task with time window that doesn't include current time
    task_out_window = MockTask("2", "Out Window", 60, 5, 3, "14:00", "16:00")
    score_out_window = scheduler.calculate_task_priority_score(task_out_window, current_time, start_time)
    
    assert score_in_window > score_out_window

def test_insufficient_energy():
    scheduler = TaskScheduler(max_energy=5.0)
    start_time = 480  # 08:00
    current_time = 960  # 16:00 (very tired)
    
    # High energy task when tired
    high_energy_task = MockTask("1", "High Energy", 60, 5, 8)
    score = scheduler.calculate_task_priority_score(high_energy_task, current_time, start_time)
    
    # Should return 0 because not enough energy
    assert score == 0

def test_basic_scheduling():
    scheduler = TaskScheduler(max_energy=10.0, break_duration=15)
    
    tasks = [
        MockTask("1", "Morning Task", 60, 8, 5, "08:00", "12:00"),
        MockTask("2", "Afternoon Task", 45, 6, 4, "13:00", "17:00"),
        MockTask("3", "Low Energy Task", 30, 4, 2)
    ]
    
    schedule = scheduler.schedule_tasks(tasks, "08:00", "17:00", "2025-09-15")
    
    assert len(schedule) > 0
    assert all(item['date'] == "2025-09-15" for item in schedule)
    
    # Check that tasks are properly ordered by time
    start_times = [scheduler.time_to_minutes(item['scheduled_start']) for item in schedule]
    assert start_times == sorted(start_times)

def test_break_scheduling():
    scheduler = TaskScheduler(max_energy=10.0, break_duration=30)
    
    # Create tasks that would require a break
    tasks = [
        MockTask("1", "Energy Intensive 1", 120, 9, 8),
        MockTask("2", "Energy Intensive 2", 120, 8, 7),
        MockTask("3", "Energy Intensive 3", 60, 7, 6)
    ]
    
    schedule = scheduler.schedule_tasks(tasks, "08:00", "16:00", "2025-09-15")
    
    # Should schedule some tasks but account for breaks
    assert len(schedule) > 0
    
    # Check that there are gaps for breaks
    if len(schedule) > 1:
        first_end = scheduler.time_to_minutes(schedule[0]['scheduled_end'])
        second_start = scheduler.time_to_minutes(schedule[1]['scheduled_start'])
        # Should have some gap for break
        assert second_start > first_end

def test_schedule_efficiency():
    scheduler = TaskScheduler()
    
    # Mock scheduled tasks
    scheduled_tasks = [
        {
            'scheduled_start': '08:00',
            'scheduled_end': '09:00',
            'energy_cost': 5.0
        },
        {
            'scheduled_start': '09:30',
            'scheduled_end': '10:30',
            'energy_cost': 6.0
        }
    ]
    
    efficiency = scheduler.calculate_schedule_efficiency(scheduled_tasks)
    assert 0 <= efficiency <= 1.0