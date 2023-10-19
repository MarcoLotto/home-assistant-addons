from model import ScheduledTaskModel, TaskModel
from domain import ScheduledTask, Task

def scheduledTask_to_model(domain: ScheduledTask):
    return ScheduledTaskModel(
            scheduled_task_id=domain.scheduled_task_id,
            task_id=domain.task_id,
            scheduled_date=domain.scheduled_date,
            status=domain.status,
            user_id=domain.user_id
        ).to_dict()

def task_to_model(domain: Task):
    return TaskModel(
            task_id=domain.task_id,
            name=domain.name,
            days_interval=domain.days_interval,
            effort=domain.effort
        ).to_dict()