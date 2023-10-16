from enum import Enum
from datetime import date

class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"

    def to_string(self):
        return self.value

class ScheduledTask():
    __tablename__ = "scheduled_tasks"
    
    scheduled_task_id: int
    task_id: int
    user_id: int
    scheduled_date: date
    status: TaskStatus

    def __init__(self, scheduled_task_id, task_id, user_id, scheduled_date, status):
        self.scheduled_task_id = scheduled_task_id
        self.task_id=task_id
        self.user_id=user_id
        self.scheduled_date = scheduled_date
        self.status = status

    def to_tuple(self):
        return [self.task_id, self.user_id, self.scheduled_date, self.status.to_string()]

class Task():
    task_id: int
    name: str
    days_interval: int
    effort: int
    allowed_days: list

    def __init__(self, task_id, name, days_interval, effort, allowed_days):
        self.task_id = task_id
        self.name = name
        self.days_interval = days_interval
        self.effort = effort
        self.allowed_days = allowed_days

class User():
    id: int
    username: str
    available_daily_effort: dict

    def __init__(self, id, username, available_daily_effort):
        self.id = id
        self.username = username
        self.available_daily_effort = available_daily_effort

class Notification():
    notification_available: bool
    notification_message: str

    def __init__(self, notification_available, notification_message):
        self.notification_available = notification_available
        self.notification_message = notification_message
