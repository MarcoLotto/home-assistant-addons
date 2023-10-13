from sqlalchemy import create_engine, Column, Integer, Date, Enum as SQLAEnum
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()

class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    
    scheduled_task_id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer)
    user_id = Column(Integer)
    scheduled_date = Column(Date)
    status = Column(SQLAEnum(TaskStatus), default=TaskStatus.PENDING)

class Task():
    task_id: int
    name: str
    days_interval: int
    effort: int
    allowed_days: list

    def __init__(self, task_id, name, days_interval, effort, allowed_days):
        self.task_id = task_id
        self.name = name
        self.days_interval = days_interval
        self.effort = effort
        self.allowed_days = allowed_days

class User():
    id: int
    username: str
    available_daily_effort: dict

    def __init__(self, id, username, available_daily_effort):
        self.id = id
        self.username = username
        self.available_daily_effort = available_daily_effort

class Notification():
    notification_available: bool
    notification_message: str

    def __init__(self, notification_available, notification_message):
        self.notification_available = notification_available
        self.notification_message = notification_message

# Crear la base de datos (SQLite en este caso)
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
