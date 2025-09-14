# FocusFlow Backend Task Optimizer

A FastAPI + PostgreSQL backend for intelligent task scheduling and optimization.

## Features

- **Task Management**: CRUD operations for tasks with duration, priority, energy level, and time windows
- **Smart Scheduling**: Greedy algorithm that factors in fatigue and breaks
- **Schedule Generation**: Optimized daily schedules based on task constraints
- **PostgreSQL Database**: Reliable data persistence with SQLAlchemy ORM

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

- `GET /tasks` - List all tasks
- `POST /tasks` - Create a new task
- `GET /tasks/{id}` - Get a specific task
- `PUT /tasks/{id}` - Update a task
- `DELETE /tasks/{id}` - Delete a task
- `POST /schedule/generate` - Generate optimized schedule

## Task Properties

- **duration**: Task duration in minutes
- **priority**: Priority level (1-10, higher is more important)
- **energy_level**: Required energy level (1-10)
- **time_window**: Preferred time window for task execution