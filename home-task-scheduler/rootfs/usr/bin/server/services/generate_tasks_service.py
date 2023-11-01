from services.config_loader_service import ConfigLoaderService
from domain import ScheduledTask, TaskStatus, User
from services.users_service import UsersService
from repositories.database_client import open_db_session
from repositories.scheduled_task_repository import ScheduledTaskRepository
from datetime import date
import random
import logging

DAY_LOOKUP = { 0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun' }

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduledTaskRepository = ScheduledTaskRepository()
configLoaderService = ConfigLoaderService()
usersService = UsersService()

class GenerateTasksService:

    def generate_daily_tasks(self):
        today = date.today()
        logger.info(f"Running task scheduler on {DAY_LOOKUP[today.weekday()]} {str(today)}")
        tasks = configLoaderService.load_tasks_from_yaml()
        random.shuffle(tasks)
        users = usersService.list_users()
        used_effort_by_user = {user.id: 0 for user in users}
        self._log_user_available_efforts(today, users)

        with open_db_session() as con:
            self._delete_pending_tasks_on_date(today, con) # Pending tasks today are being deleted to avoid issues while re-running
            self._mark_as_incompleted_previous_days_pending_tasks(today, con)
            todays_scheduled_task_ids = self._get_today_scheduled_task_ids(con, today)

            # First assign the mandatory tasks (zero effort)
            mandatory_task_ids_assigned = self._assign_mandatory_tasks(tasks, today, users, todays_scheduled_task_ids, con)

            # Then the time-consuming tasks
            unasigned_effort = 0
            for task in tasks:
                if task.task_id in mandatory_task_ids_assigned:
                    continue
                user = self._get_user_to_assign(task, users, used_effort_by_user, today)
                if user != None:
                    if self._schedule_task_for_today(task, today, todays_scheduled_task_ids, con, user):
                        used_effort_by_user[user.id] = used_effort_by_user[user.id] + task.effort
                else:
                    unasigned_effort += task.effort
                    logger.debug(f"Task {task.name} cannot be scheduled as there is not effort remaining")

            if unasigned_effort > 0:
                logger.warn(f"There are a total of {unasigned_effort} effort points not assigned as there is not enough capacity")

            con.commit()
        logger.info(f"Task scheduler finished")

    def _get_remaining_user_effort(self, date, user: User, used_effort: int) -> int:
        current_day = DAY_LOOKUP[date.weekday()]
        return user.available_daily_effort[current_day] - used_effort

    def _get_user_to_assign(self, task, users, used_effort_by_user: dict, date) -> User:
        for user in users:
            remaining_user_effort = self._get_remaining_user_effort(date, user, used_effort_by_user[user.id])
            if task.effort <= remaining_user_effort:
                return user
        return None

    def _schedule_task_for_today(self, task, today, todays_scheduled_task_ids, con, user):
        """Schedule a task for today if it meets the interval criteria. Skip if already scheduled"""
        if task.task_id in todays_scheduled_task_ids:
            logger.info(f"Task '{task.name}' is already scheduled for today - Effort: {task.effort}")
            return False
        
        day_of_week = DAY_LOOKUP[today.weekday()]
        if task.allowed_days != None and day_of_week not in task.allowed_days:
            logger.debug(f"Task '{task.name}' is not available today ({day_of_week}) - allowed days {str(task.allowed_days)}")
            return False
        
        last_scheduled = scheduledTaskRepository.get_last_scheduled_task(con, task.task_id)
        if not last_scheduled or (today - last_scheduled.scheduled_date).days >= task.days_interval:
            new_scheduled_task = ScheduledTask(None, task_id=task.task_id,  user_id=user.id, scheduled_date=today, status=TaskStatus.PENDING)
            scheduledTaskRepository.insert_scheduled_task(con, new_scheduled_task)
            logger.info(f"Task '{task.name}' assigned to {user.username} - Effort: {task.effort}")
            return True
        logger.debug(f"Task '{task.name}' is not assigned as it has been scheduled recently")
        return False

    def _mark_as_incompleted_previous_days_pending_tasks(self, today, con):
        scheduledTaskRepository.update_past_scheduled_tasks_status(con, TaskStatus.PENDING, today, TaskStatus.INCOMPLETE)
        logger.info(f"Marked previous pending tasks as {TaskStatus.INCOMPLETE.value}.")

    def _delete_pending_tasks_on_date(self, date, con):
        scheduledTaskRepository.delete_non_completed_scheduled_tasks(con, date)

    def _get_today_scheduled_task_ids(self, con, today):
        """Get IDs of tasks already scheduled for the current day.""" 
        tasks = scheduledTaskRepository.get_scheduled_tasks(con, None, None, today)
        return {task.task_id for task in tasks}

    def _assign_mandatory_tasks(self, tasks, date, users, todays_scheduled_task_ids, con):
        mandatory_task_ids_assigned = set()
        current_user_index = 0
        for task in tasks:
            if task.effort == 0:  # Mandatory tasks have zero effort
                self._schedule_task_for_today(task, date, todays_scheduled_task_ids, con, users[current_user_index])
                mandatory_task_ids_assigned.add(task.task_id)
                current_user_index += 1 
            if current_user_index >= len(users):
                current_user_index = 0
        return mandatory_task_ids_assigned

    def _log_user_available_efforts(self, today, users):
        for user in users:
            available_effort = self._get_remaining_user_effort(today, user, 0)
            logger.info(f"User {user.username} has today an available effort of {str(available_effort)}")
