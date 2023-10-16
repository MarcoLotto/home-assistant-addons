from domain import TaskStatus
from datetime import date

class ScheduledTaskModel():
    def __init__(self, scheduled_task_id: int, task_id: int, scheduled_date: date, user_id: int, status: TaskStatus):
        self.scheduled_task_id = scheduled_task_id
        self.task_id = task_id
        self.scheduled_date = scheduled_date
        self.user_id = user_id
        self.status = status
    
    def to_dict(self):
        return {
            "scheduled_task_id": self.scheduled_task_id,
            "task_id": self.task_id,
            "scheduled_date": self.scheduled_date.isoformat(),
            "user_id": self.user_id,
            "status": self.status.to_string()
        }