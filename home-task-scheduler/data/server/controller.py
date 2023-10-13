from fastapi import FastAPI, HTTPException
from services.config_loader_service import load_tasks_from_yaml
from domain import engine, ScheduledTask, TaskStatus
from model import ScheduledTaskStatusUpdateModel, NotificationModel
from model_mapper import scheduledTask_to_model
from sqlalchemy.orm import sessionmaker
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
from services.notifications_service import get_notification_message
from services.generate_tasks_service import generate_daily_tasks

app = FastAPI()
SessionLocal = sessionmaker(bind=engine)
scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    generate_daily_tasks() # Execute on startup in case that it has been down for the day
    scheduler.add_job(generate_daily_tasks, trigger="cron", hour=6)  # This sets it to run daily at 6:00 AM.
    scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

@app.get("/tasks")
def get_all_tasks():
    return load_tasks_from_yaml()

@app.get("/tasks/{task_id}")
def get_task_by_id(task_id: int):
    tasks = load_tasks_from_yaml()
    for task in tasks:
        if task.task_id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/scheduled-tasks/today")
def read_scheduled_tasks_for_today(status: Optional[TaskStatus] = None):
    with SessionLocal() as db:
        query = db.query(ScheduledTask).filter(ScheduledTask.scheduled_date == date.today())
        if status:
            query = query.filter(ScheduledTask.status == status)
        tasks_today = query.all()
    return { "tasks": [scheduledTask_to_model(task) for task in tasks_today] }

@app.get("/notifications/scheduled-tasks")
def get_notification_for_scheduled_tasks():
    with SessionLocal() as db:
        notification = get_notification_message(db)
    return NotificationModel(notification_available=notification.notification_available, notification_message=notification.notification_message)

@app.get("/scheduled-tasks/{scheduled_task_id}")
def read_scheduled_tasks_for_today(scheduled_task_id: int):
    with SessionLocal() as db:
        scheduled_task = db.query(ScheduledTask).filter(ScheduledTask.id == scheduled_task_id).first()
        return scheduledTask_to_model(scheduled_task)

@app.put("/scheduled-tasks/{scheduled_task_id}")
def update_scheduled_task_status(scheduled_task_id: int, data: ScheduledTaskStatusUpdateModel):
    with SessionLocal() as db:
        scheduled_task = db.query(ScheduledTask).filter(ScheduledTask.id == scheduled_task_id).first()
        if not scheduled_task:
            raise HTTPException(status_code=404, detail="Scheduled task not found")
        
        scheduled_task.status = data.status
        db.add(scheduled_task)
        db.commit()
        return scheduledTask_to_model(scheduled_task)
    
def get_pending_tasks_for_user(db, user_id: int):
    return db.query(ScheduledTask).filter(ScheduledTask.user_id == user_id).filter(ScheduledTask.status == TaskStatus.PENDING).all()
    
@app.put("/users/{user_id}/pending-tasks")
def update_scheduled_task_status(user_id: int, data: ScheduledTaskStatusUpdateModel):
    with SessionLocal() as db:
        scheduled_tasks = get_pending_tasks_for_user(db, user_id)
        for scheduled_task in scheduled_tasks:
            scheduled_task.status = data.status
            db.add(scheduled_task)
        db.commit()
        return { "pending_tasks": [scheduledTask_to_model(task) for task in scheduled_tasks] }

@app.get("/users/{user_id}/pending-tasks")
def update_scheduled_task_status(user_id: int):
    with SessionLocal() as db:
        scheduled_tasks = get_pending_tasks_for_user(db, user_id)
        return { "pending_tasks": [scheduledTask_to_model(task) for task in scheduled_tasks] }
    
@app.post("/generate-tasks")
def read_scheduled_tasks_for_today():
    generate_daily_tasks()
    return {"result": "ok"}

