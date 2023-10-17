import yaml
from domain import User, Task

TASKS_FILENAME = "/usr/bin/server/tasks.yaml"
USERS_FILENAME = "/usr/bin/server/users.yaml"

def get_task_allowed_days(task: dict):
    if "allowed_days" in task:
        return task["allowed_days"]
    return None

def load_tasks_from_yaml(file_path=TASKS_FILENAME) -> list[Task]:
    with open(file_path, "r") as file:
        tasks = yaml.safe_load(file)
    return [Task(task["id"], task["name"], task["days_interval"], task["effort"], get_task_allowed_days(task)) for task in tasks]

def load_tasks_from_yaml_as_id_dictionary(file_path=TASKS_FILENAME) -> dict[Task]:
    tasks = load_tasks_from_yaml(file_path)
    id_dictionary = {}
    for task in tasks:
        task_id = task.task_id
        if task_id in id_dictionary:
            raise ValueError(f"Duplicate ID {task_id} found in tasks.")
        id_dictionary[task_id] = task
    return id_dictionary

def load_users_from_yaml(file_path=USERS_FILENAME) -> list[User]:
    with open(file_path, "r") as file:
        users_data = yaml.safe_load(file)
    return [User(user["id"], user["username"], user["available_daily_effort"]) for user in users_data]

def load_users_by_id_from_yaml(file_path=USERS_FILENAME) -> dict[User]:
    users = load_users_from_yaml(file_path)
    id_dictionary = {}
    for user in users:
        user_id = user.id
        if user_id in id_dictionary:
            raise ValueError(f"Duplicate ID {user_id} found in users.")
        id_dictionary[user_id] = user
    return users
