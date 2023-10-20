from domain import ScheduledTask, TaskStatus, Notification
from services.config_loader_service import ConfigLoaderService
from services.users_service import UsersService
from repositories.scheduled_task_repository import ScheduledTaskRepository

scheduledTaskRepository = ScheduledTaskRepository()
configLoaderService = ConfigLoaderService()
usersService = UsersService()

DEFAULT_LANGUAGE = "en"
YOUR_TASKS_ARE_MSG_BY_LANGUAGE = {
    "en": "your tasks are",
    "es": "tus tareas son"
}

class NotificationService:

    def get_notification_message(self, con, language: str):
        notification_available = False
        notification_message = ""

        your_tasks_message = self._get_your_tasks_message(language)
        users = usersService.list_users()
        for user in users:
            user_notification = self._generate_task_message_for_user(con, user.id)
            if user_notification.notification_available:
                notification_available = True
                notification_message += f"\n{user.username}, {your_tasks_message}: {user_notification.notification_message}."

        if not notification_available:
            return Notification(notification_available, "No notifications")
        return Notification(notification_available, notification_message)
    
    def _get_your_tasks_message(self, language: str):
        if language == None:
            language = DEFAULT_LANGUAGE

        if language not in YOUR_TASKS_ARE_MSG_BY_LANGUAGE:
            raise ValueError(f"Language {language} is not supported")
        return YOUR_TASKS_ARE_MSG_BY_LANGUAGE[language]
    
    def _generate_task_message_for_user(self, con, user_id: int):
        tasks_today = scheduledTaskRepository.get_today_scheduled_tasks_by_status_and_user(con, TaskStatus.PENDING.to_string(), user_id)
        notification_available = len(tasks_today) > 0
        if not notification_available:
            return Notification(notification_available, "No notifications")
        
        task_names = self._fetch_tasks_names(tasks_today)
        task_names_str = ", ".join(map(lambda task_name: str(task_name), task_names))
        return Notification(notification_available, task_names_str)
    
    def _fetch_tasks_names(self, scheduled_tasks: ScheduledTask):
        tasks_by_id = configLoaderService.load_tasks_from_yaml_as_id_dictionary()
        task_names = []
        for scheduled_task in scheduled_tasks:
            task_names.append(tasks_by_id[scheduled_task.task_id].name)
        return task_names