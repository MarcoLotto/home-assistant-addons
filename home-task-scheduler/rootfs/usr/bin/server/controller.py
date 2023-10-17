from bottle import Bottle, route, run, request, response, HTTPError
from services.config_loader_service import load_tasks_from_yaml, create_config_dir
from domain import TaskStatus
from model_mapper import scheduledTask_to_model
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
from services.notifications_service import get_notification_message
from services.generate_tasks_service import generate_daily_tasks
from waitress import serve
from repositories.scheduled_task_repository import get_tasks_for_user_from_repo, get_scheduled_task_from_repo, update_scheduled_task_status_from_repo, get_today_scheduled_tasks_by_status_from_repo
from repositories.database_client import open_db_session

app = Bottle()
scheduler = BackgroundScheduler()

def start_scheduler():
    generate_daily_tasks()
    scheduler.add_job(generate_daily_tasks, trigger="cron", hour=6)
    scheduler.start()

# Call on module import
create_config_dir()
start_scheduler()

@app.route("/tasks")
def get_all_tasks():
    return load_tasks_from_yaml()

@app.route("/tasks/<task_id:int>")
def get_task_by_id(task_id):
    tasks = load_tasks_from_yaml()
    for task in tasks:
        if task['task_id'] == task_id:
            return task
    return HTTPError(404, "Task not found")

@app.route("/scheduled-tasks/today")
def read_scheduled_tasks_for_today():
    with open_db_session() as con:
        status = request.query.get("status")
        tasks_today = get_today_scheduled_tasks_by_status_from_repo(con, status)
    return {"tasks": [scheduledTask_to_model(task) for task in tasks_today]}

@app.route("/notifications/scheduled-tasks")
def get_notification_for_scheduled_tasks():
    with open_db_session() as con:
        notification = get_notification_message(con)
    return {"notification_available": notification.notification_available, "notification_message": notification.notification_message}

@app.route("/scheduled-tasks/<scheduled_task_id:int>")
def read_scheduled_task(scheduled_task_id):
    with open_db_session() as con:
        scheduled_task = get_scheduled_task_from_repo(con, scheduled_task_id)
    if not scheduled_task:
        return HTTPError(404, "Scheduled task not found")
    return scheduledTask_to_model(scheduled_task)

@app.route("/scheduled-tasks/<scheduled_task_id:int>", method="PUT")
def update_scheduled_task_status(scheduled_task_id):
    with open_db_session() as con:
        scheduled_task = get_scheduled_task_from_repo(scheduled_task_id)
        if not scheduled_task:
            return HTTPError(404, "Scheduled task not found")
        data = request.json
        update_scheduled_task_status_from_repo(scheduled_task_id, data['status'])
        con.commit()
    return scheduledTask_to_model(scheduled_task)

@app.route("/users/<user_id:int>/pending-tasks", method="PUT")
def update_user_pending_tasks(user_id):
    data = request.json
    with open_db_session() as con:
        scheduled_tasks = get_tasks_for_user_from_repo(con, user_id, TaskStatus.PENDING)
        for scheduled_task in scheduled_tasks:
            update_scheduled_task_status_from_repo(con, scheduled_task["scheduled_task_id"], data['status'])
        con.commit()
        return {"pending_tasks": [scheduledTask_to_model(task) for task in scheduled_tasks]}

@app.route("/users/<user_id:int>/pending-tasks")
def get_user_pending_tasks(user_id):
    with open_db_session() as con:
        scheduled_tasks = get_tasks_for_user_from_repo(con, user_id, TaskStatus.PENDING)
        return {"pending_tasks": [scheduledTask_to_model(task) for task in scheduled_tasks]}

@app.route("/generate-tasks", method="POST")
def generate_tasks_endpoint():
    generate_daily_tasks()
    return {"result": "ok"}

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)
