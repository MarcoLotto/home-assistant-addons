from pydantic import BaseModel
from domain import TaskStatus
from datetime import date

class ScheduledTaskStatusUpdateModel(BaseModel):
    status: TaskStatus

class ScheduledTaskModel(BaseModel):
    scheduled_task_id: int
    task_id: int
    scheduled_date: date
    user_id: int
    status: TaskStatus

class NotificationModel(BaseModel):
    notification_available: bool
    notification_message: str