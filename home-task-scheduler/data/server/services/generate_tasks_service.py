from services.config_loader_service import load_tasks_from_yaml
from domain import engine, ScheduledTask, TaskStatus, User
from sqlalchemy.orm import sessionmaker
from services.users_service import list_users
from datetime import date
import random
import logging

DAY_LOOKUP = { 0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun' }

SessionLocal = sessionmaker(bind=engine)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_remaining_user_effort(date, user: User, used_effort: int) -> int:
    current_day = DAY_LOOKUP[date.weekday()]
    return user.available_daily_effort[current_day] - used_effort

def _get_user_to_assign(task, users, used_effort_by_user: dict, date) -> User:
    for user in users:
        remaining_user_effort = _get_remaining_user_effort(date, user, used_effort_by_user[user.id])
        if task.effort <= remaining_user_effort:
            return user
    return None

def _schedule_task_for_today(task, today, todays_scheduled_task_ids, db, user):
    """Schedule a task for today if it meets the interval criteria. Skip if already scheduled"""
    if task.task_id in todays_scheduled_task_ids:
        logger.info(f"Task '{task.name}' is already scheduled for today.")
        return False
    
    day_of_week = DAY_LOOKUP[today.weekday()]
    if task.allowed_days != None and day_of_week not in task.allowed_days:
        logger.debug(f"Task '{task.name}' is not available today ({day_of_week}) - allowed days {str(task.allowed_days)}")
        return False
    
    last_scheduled = db.query(ScheduledTask).filter_by(task_id=task.task_id, status=TaskStatus.COMPLETED).order_by(ScheduledTask.scheduled_date.desc()).first()
    if not last_scheduled or (today - last_scheduled.scheduled_date).days >= task.days_interval:
        new_scheduled_task = ScheduledTask(task_id=task.task_id, scheduled_date=today, status=TaskStatus.PENDING, user_id=user.id)
        db.add(new_scheduled_task)
        logger.info(f"Task '{task.name}' assigned to {user.username}")
        return True
    logger.info(f"Task '{task.name}' is not assigned as it has been scheduled recently")
    return False

def _mark_as_incompleted_previous_days_pending_tasks(today, db):
    pending_tasks = db.query(ScheduledTask).filter(ScheduledTask.scheduled_date < today, ScheduledTask.status == TaskStatus.PENDING).all()
    for pending_task in pending_tasks:  
            pending_task.status = TaskStatus.INCOMPLETE
            db.add(pending_task)
            logger.info(f"Marked previous task {pending_task.task_id} as {TaskStatus.INCOMPLETE}.")

def _delete_pending_tasks_on_date(date, db):
    db.query(ScheduledTask).filter(ScheduledTask.scheduled_date == date, ScheduledTask.status != TaskStatus.COMPLETED).delete()

def _get_today_scheduled_task_ids(db, today):
    """Get IDs of tasks already scheduled for the current day.""" 
    return {task.task_id for task in db.query(ScheduledTask).filter_by(scheduled_date=today).all()}

def _assign_mandatory_tasks(tasks, date, users, todays_scheduled_task_ids, db):
    mandatory_task_ids_assigned = set()
    current_user_index = 0
    for task in tasks:
        if task.effort == 0:  # Mandatory tasks have zero effort
            _schedule_task_for_today(task, date, todays_scheduled_task_ids, db, users[current_user_index])
            mandatory_task_ids_assigned.add(task.task_id)
            current_user_index += 1 
        if current_user_index >= len(users):
            current_user_index = 0
    return mandatory_task_ids_assigned

def generate_daily_tasks():
    today = date.today()
    logger.info(f"Running task scheduler on {DAY_LOOKUP[today.weekday()]} {str(today)}")
    tasks = load_tasks_from_yaml()
    random.shuffle(tasks)
    users = list_users()
    used_effort_by_user = {user.id: 0 for user in users}

    with SessionLocal() as db:
        _delete_pending_tasks_on_date(today, db) # Pending tasks today are being deleted to avoid issues while re-running
        _mark_as_incompleted_previous_days_pending_tasks(today, db)
        todays_scheduled_task_ids = _get_today_scheduled_task_ids(db, today)

        # First assign the mandatory tasks (zero effort)
        mandatory_task_ids_assigned = _assign_mandatory_tasks(tasks, today, users, todays_scheduled_task_ids, db)

        # Then the time-consuming tasks
        for task in tasks:
            if task.task_id in mandatory_task_ids_assigned:
                continue
            user = _get_user_to_assign(task, users, used_effort_by_user, today)
            if user != None:
                if _schedule_task_for_today(task, today, todays_scheduled_task_ids, db, user):
                    used_effort_by_user[user.id] = used_effort_by_user[user.id] + task.effort
            else:
                logger.warn(f"Task {task.name} cannot be scheduled as there is not effort remaining")

        db.commit()
    logger.info(f"Task scheduler finished")
