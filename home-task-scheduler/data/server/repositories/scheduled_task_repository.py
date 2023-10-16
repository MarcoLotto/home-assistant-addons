from sqlite3 import Connection
from domain import TaskStatus, ScheduledTask
from datetime import date

class QueryAttribute:
    column: str
    operation: str
    value: object
    def __init__(self, column: str, operation: str, value: object):
        self.column = column
        self.operation = operation
        self.value = value

def dict_factory(cursor, row):
    task_dict = {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    scheduled_date = date.fromisoformat(task_dict["scheduled_date"])
    status = TaskStatus[task_dict["status"].upper()]
    print("QUERY RESULT: " + str(task_dict))
    return ScheduledTask(scheduled_task_id=task_dict["scheduled_task_id"], task_id=task_dict["task_id"], user_id=task_dict["user_id"], scheduled_date=scheduled_date, status=status)

def get_tasks_for_user_from_repo(con: Connection, user_id: str, task_status: TaskStatus):
    con.row_factory = dict_factory
    cursor = con.cursor()
    cursor.execute("SELECT * FROM scheduled_tasks WHERE user_id=? AND status=?", (user_id, task_status.to_string()))
    tasks = cursor.fetchall()
    return tasks

def get_scheduled_task_from_repo(con: Connection, scheduled_task_id: int):
    con.row_factory = dict_factory
    cursor = con.cursor()

    # Check if scheduled_task exists
    cursor.execute("SELECT * FROM scheduled_tasks WHERE id=?", (scheduled_task_id,))
    scheduled_task = cursor.fetchone()
    if not scheduled_task:
        return None
    return dict_factory(scheduled_task)

def update_scheduled_task_status_from_repo(con: Connection, scheduled_task_id: int, task_status: str):
    cursor = con.cursor()
    cursor.execute("UPDATE scheduled_tasks SET status=? WHERE id=?", (task_status, scheduled_task_id))

def insert_scheduled_task_from_repo(con: Connection, scheduled_task: ScheduledTask):
    cursor = con.cursor()
    query = "INSERT INTO scheduled_tasks (task_id, user_id, scheduled_date, status) VALUES (?, ?, ?, ?)"
    cursor.execute(query, scheduled_task.to_tuple())

def get_today_scheduled_tasks_by_status_and_user_from_repo(con: Connection, status: str, user_id: int):
    return get_scheduled_tasks_from_repo(con, status, user_id, date.today())
    
def get_today_scheduled_tasks_by_status_from_repo(con: Connection, status: str):
    return get_scheduled_tasks_from_repo(con, status, None, date.today())

def _execute_scheduled_tasks_query(operation: str, con: Connection, query_attributes: list[QueryAttribute]):
    return _execute_scheduled_tasks_query_with_subquery(operation, con, query_attributes, "")

def _execute_scheduled_tasks_query_with_subquery(query_clause: str, con: Connection, query_attributes: list[QueryAttribute], subquery_query: str):
    con.row_factory = dict_factory
    cursor = con.cursor()
    query = query_clause + " FROM scheduled_tasks WHERE "
    params = []

    for attribute in query_attributes:
        if not query.strip().endswith("WHERE"):
             query += " AND "
        query += f"{attribute.column}{attribute.operation}?"
        final_param = attribute.value
        if isinstance(attribute.value, date): 
            final_param = final_param.isoformat() # Convert date to string format (SQLite doesn't have a date type)
        params.append(final_param)
    query += subquery_query

    print("QUERY PARAMS: " + str(params))
    cursor.execute(query, params)
    return cursor

def get_scheduled_tasks_from_repo(con: Connection, status: str, user_id: int, date: date):
    query_attributes = []
    if status != None:
        query_attributes.append(QueryAttribute("status", "=", status))
    if user_id != None:
        query_attributes.append(QueryAttribute("user_id", "=", user_id))
    if date != None:
        query_attributes.append(QueryAttribute("scheduled_date", "=", date.today()))

    cursor = _execute_scheduled_tasks_query("SELECT *", con, query_attributes)
    return cursor.fetchall()

def delete_non_completed_scheduled_tasks_from_repo(con: Connection, date: date):
    _execute_scheduled_tasks_query("DELETE", con, [QueryAttribute("status", "!=", TaskStatus.COMPLETED.value), QueryAttribute("scheduled_date", "=", date)])

def get_last_completed_task_from_repo(con: Connection, task_id: int, status: TaskStatus):
    order_query = " ORDER BY scheduled_date DESC"
    cursor = _execute_scheduled_tasks_query_with_subquery("SELECT *", con, [QueryAttribute("task_id", "=", task_id), QueryAttribute("status", "=", status.value)], order_query)
    return cursor.fetchall()

def get_past_previous_tasks_from_repo(con: Connection, date: date):
    cursor = _execute_scheduled_tasks_query("SELECT *", con, [QueryAttribute("scheduled_date", "<", date), QueryAttribute("status", "=", TaskStatus.PENDING.value)])
    return cursor.fetchall()

