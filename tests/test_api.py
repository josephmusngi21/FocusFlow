import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to FocusFlow Backend Task Optimizer"
    assert "features" in data

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_task():
    task_data = {
        "title": "Test Task",
        "description": "A test task",
        "duration": 60,
        "priority": 5,
        "energy_level": 4,
        "time_window_start": "09:00",
        "time_window_end": "12:00"
    }
    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["status"] == "pending"
    assert "id" in data

def test_list_tasks():
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_and_get_task():
    # Create task
    task_data = {
        "title": "Get Task Test",
        "description": "Test getting a specific task",
        "duration": 30,
        "priority": 3,
        "energy_level": 2
    }
    create_response = client.post("/tasks/", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["id"]
    
    # Get task
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["title"] == task_data["title"]

def test_update_task():
    # Create task
    task_data = {
        "title": "Update Test Task",
        "duration": 45,
        "priority": 6,
        "energy_level": 5
    }
    create_response = client.post("/tasks/", json=task_data)
    task_id = create_response.json()["id"]
    
    # Update task
    update_data = {"priority": 8, "status": "completed"}
    update_response = client.put(f"/tasks/{task_id}", json=update_data)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["priority"] == 8
    assert data["status"] == "completed"

def test_delete_task():
    # Create task
    task_data = {
        "title": "Delete Test Task",
        "duration": 15,
        "priority": 2,
        "energy_level": 1
    }
    create_response = client.post("/tasks/", json=task_data)
    task_id = create_response.json()["id"]
    
    # Delete task
    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 200
    
    # Verify task is gone
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404

def test_generate_schedule():
    # Create some tasks first
    tasks = [
        {
            "title": "Schedule Test Task 1",
            "duration": 60,
            "priority": 7,
            "energy_level": 5,
            "time_window_start": "09:00",
            "time_window_end": "12:00"
        },
        {
            "title": "Schedule Test Task 2",
            "duration": 45,
            "priority": 6,
            "energy_level": 4,
            "time_window_start": "13:00",
            "time_window_end": "16:00"
        }
    ]
    
    for task in tasks:
        response = client.post("/tasks/", json=task)
        assert response.status_code == 200
    
    # Generate schedule
    schedule_request = {
        "date": "2025-09-15",
        "work_start": "08:00",
        "work_end": "17:00",
        "max_energy": 10.0,
        "break_duration": 15
    }
    
    response = client.post("/schedule/generate", json=schedule_request)
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2025-09-15"
    assert "schedule_items" in data
    assert "total_tasks" in data

def test_get_schedule():
    response = client.get("/schedule/2025-09-15")
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2025-09-15"
    assert "schedule_items" in data