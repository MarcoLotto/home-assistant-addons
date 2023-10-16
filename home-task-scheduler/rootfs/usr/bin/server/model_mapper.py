from model import ScheduledTaskModel
from domain import ScheduledTask

def scheduledTask_to_model(domain: ScheduledTask):
    return ScheduledTaskModel(
            scheduled_task_id=domain.scheduled_task_id,
            task_id=domain.task_id,
            scheduled_date=domain.scheduled_date,
            status=domain.status,
            user_id=domain.user_id
        ).to_dict()