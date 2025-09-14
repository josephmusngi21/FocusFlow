from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api import tasks, schedule

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FocusFlow Backend Task Optimizer",
    description="A FastAPI + PostgreSQL backend for intelligent task scheduling and optimization",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to FocusFlow Backend Task Optimizer",
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "Task CRUD operations",
            "Intelligent task scheduling",
            "Fatigue and break management",
            "Schedule optimization"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}