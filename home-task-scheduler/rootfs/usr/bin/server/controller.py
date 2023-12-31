from bottle import Bottle, route, run, request, response, HTTPError
from services.config_loader_service import ConfigLoaderService
from domain import TaskStatus
from model_mapper import scheduledTask_to_model, task_to_model
from apscheduler.schedulers.background import BackgroundScheduler
from services.notifications_service import NotificationService
from services.generate_tasks_service import GenerateTasksService
from waitress import serve
from repositories.scheduled_task_repository import ScheduledTaskRepository
from repositories.database_client import open_db_session, init_db

app = Bottle()
scheduler = BackgroundScheduler()
scheduledTaskRepository = ScheduledTaskRepository()
generateTasksService = GenerateTasksService()
notificationService = NotificationService()
configLoaderService = ConfigLoaderService()

def on_start():
    # Create the config dirs and init the database
    configLoaderService.create_config_dir()
    init_db()
    
    # Generate the daily tasks and schedule it for a fixed time
    generateTasksService.generate_daily_tasks()
    scheduler.add_job(generateTasksService.generate_daily_tasks, trigger="cron", hour=6)
    scheduler.start()

@app.route("/tasks")
def get_all_tasks():
    tasks = configLoaderService.load_tasks_from_yaml()
    return {"tasks": [task_to_model(task) for task in tasks]}

@app.route("/tasks/<task_id:int>")
def get_task_by_id(task_id):
    tasks = configLoaderService.load_tasks_from_yaml()
    for task in tasks:
        if task.task_id == task_id:
            return task_to_model(task)
    return HTTPError(404, "Task not found")

@app.route("/scheduled-tasks/today")
def read_scheduled_tasks_for_today():
    with open_db_session() as con:
        status = request.query.get("status")
        tasks_today = scheduledTaskRepository.get_today_scheduled_tasks_by_status(con, status)
    return {"tasks": [scheduledTask_to_model(task) for task in tasks_today]}

@app.route("/notifications/scheduled-tasks")
def get_notification_for_scheduled_tasks():
    language = request.query.get("language")
    with open_db_session() as con:
        notification = notificationService.get_notification_message(con, language)
    return {"notification_available": notification.notification_available, "notification_message": notification.notification_message}

@app.route("/scheduled-tasks/<scheduled_task_id:int>")
def read_scheduled_task(scheduled_task_id):
    with open_db_session() as con:
        scheduled_task = scheduledTaskRepository.get_scheduled_task(con, scheduled_task_id)
    if not scheduled_task:
        return HTTPError(404, "Scheduled task not found")
    return scheduledTask_to_model(scheduled_task)

def get_task_status_from_request_payload(request):
    data = request.json
    if 'status' not in data:
        raise HTTPError(400, "Status is required on payload")
    if data['status'] not in (item.value for item in TaskStatus):
        raise HTTPError(400, "The value is not a valid TaskStatus")
    input_status = data['status'].upper()
    return TaskStatus[input_status]

@app.route("/scheduled-tasks/<scheduled_task_id:int>", method="PUT")
def update_scheduled_task_status(scheduled_task_id):
    input_status = get_task_status_from_request_payload(request)
    with open_db_session() as con:
        scheduledTaskRepository.update_scheduled_task_status(con, scheduled_task_id, input_status)
        con.commit()
    return {"result": "ok"}

@app.route("/users/<user_id:int>/pending-tasks", method="PUT")
def update_user_pending_tasks(user_id):
    input_status = get_task_status_from_request_payload(request)
    with open_db_session() as con:
        scheduledTaskRepository.update_tasks_status_for_user(con, user_id, TaskStatus.PENDING, input_status)
        con.commit()
    return {"result": "ok"}

@app.route("/users/<user_id:int>/pending-tasks")
def get_user_pending_tasks(user_id):
    with open_db_session() as con:
        scheduled_tasks = scheduledTaskRepository.get_tasks_for_user(con, user_id, TaskStatus.PENDING)
        return {"pending_tasks": [scheduledTask_to_model(task) for task in scheduled_tasks]}

@app.route("/generate-tasks", method="POST")
def generate_tasks_endpoint():
    generateTasksService.generate_daily_tasks()
    return {"result": "ok"}

if __name__ == "__main__":
    on_start()
    serve(app, host="0.0.0.0", port=8000)
