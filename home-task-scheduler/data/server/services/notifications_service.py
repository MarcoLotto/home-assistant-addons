
from sqlalchemy.orm import sessionmaker
from domain import engine, ScheduledTask, TaskStatus, Notification
from datetime import date
from services.config_loader_service import load_tasks_from_yaml_as_id_dictionary
from services.users_service import list_users

SessionLocal = sessionmaker(bind=engine)

def fetch_tasks_names(scheduled_tasks: ScheduledTask):
    tasks_by_id = load_tasks_from_yaml_as_id_dictionary()
    task_names = []
    for scheduled_task in scheduled_tasks:
        task_names.append(tasks_by_id[scheduled_task.task_id].name)
    return task_names

def generate_task_message_for_user(db, user_id: int):
    query = db.query(ScheduledTask).filter(ScheduledTask.scheduled_date == date.today())
    query = query.filter(ScheduledTask.user_id == user_id)
    query = query.filter(ScheduledTask.status == TaskStatus.PENDING)
    tasks_today = query.all()
    
    notification_available = len(tasks_today) > 0
    if not notification_available:
        return Notification(notification_available, "No notifications")
    
    task_names = fetch_tasks_names(tasks_today)
    task_names_str = ", ".join(map(lambda task_name: str(task_name), task_names))
    return Notification(notification_available, task_names_str)

def get_notification_message(db):
    notification_available = False
    notification_message = ""

    users = list_users()
    for user in users:
         user_notification = generate_task_message_for_user(db, user.id)
         if user_notification.notification_available:
             notification_available = True
             notification_message += f"\n{user.username}, tus tareas son: {user_notification.notification_message}."

    if not notification_available:
          return Notification(notification_available, "No notifications")
    return Notification(notification_available, notification_message)