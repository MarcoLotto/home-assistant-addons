import yaml
import os
import shutil
from domain import User, Task

BASE_TARGET_PATH = "/config/home-task-scheduler/"
ABS_SOURCE_PATH = "/usr/bin/server/"
REL_SOURCE_PATH = "./initial_config/"
TASKS_CONFIG_FILENAME = "tasks.yaml"
USERS_CONFIG_FILENAME = "users.yaml"

TASKS_CONFIG_PATH = BASE_TARGET_PATH + TASKS_CONFIG_FILENAME
USERS_CONFIG_PATH = BASE_TARGET_PATH + USERS_CONFIG_FILENAME

def get_task_allowed_days(task: dict):
    if "allowed_days" in task:
        return task["allowed_days"]
    return None

def load_tasks_from_yaml(file_path=TASKS_CONFIG_PATH) -> list[Task]:
    with open(file_path, "r") as file:
        tasks = yaml.safe_load(file)
    return [Task(task["id"], task["name"], task["days_interval"], task["effort"], get_task_allowed_days(task)) for task in tasks]

def load_tasks_from_yaml_as_id_dictionary(file_path=TASKS_CONFIG_PATH) -> dict[Task]:
    tasks = load_tasks_from_yaml(file_path)
    id_dictionary = {}
    for task in tasks:
        task_id = task.task_id
        if task_id in id_dictionary:
            raise ValueError(f"Duplicate ID {task_id} found in tasks.")
        id_dictionary[task_id] = task
    return id_dictionary

def load_users_from_yaml(file_path=USERS_CONFIG_PATH) -> list[User]:
    with open(file_path, "r") as file:
        users_data = yaml.safe_load(file)
    return [User(user["id"], user["username"], user["available_daily_effort"]) for user in users_data]

def load_users_by_id_from_yaml(file_path=USERS_CONFIG_PATH) -> dict[User]:
    users = load_users_from_yaml(file_path)
    id_dictionary = {}
    for user in users:
        user_id = user.id
        if user_id in id_dictionary:
            raise ValueError(f"Duplicate ID {user_id} found in users.")
        id_dictionary[user_id] = user
    return users

def create_config_dir():
    # If there is no /config folder created, it creates it and adds initial content to it
    if not os.path.exists(BASE_TARGET_PATH):
        print(f"Creating config folder {BASE_TARGET_PATH} and initial contents...")
        os.makedirs(BASE_TARGET_PATH)  # Create directory

        # Now let's copy the yaml files into it
        yaml_files = [TASKS_CONFIG_FILENAME, USERS_CONFIG_FILENAME]

        for yaml_file in yaml_files:
            abs_source_yaml_path = ABS_SOURCE_PATH + yaml_file
            rel_source_yaml_path = REL_SOURCE_PATH + yaml_file
            if os.path.exists(abs_source_yaml_path):
                shutil.copy(abs_source_yaml_path, BASE_TARGET_PATH)
            elif os.path.exists(rel_source_yaml_path):
                shutil.copy(rel_source_yaml_path, BASE_TARGET_PATH)
            else:
                print(f"Warning: {yaml_file} was not found and hence not copied.")
    else:
        print(f"The directory {BASE_TARGET_PATH} already exists, not filling it")
