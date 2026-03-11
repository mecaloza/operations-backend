from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from database import Base


class TaskStatus(str, enum.Enum):
    backlog = "backlog"
    in_progress = "in_progress"
    done = "done"
    blocked = "blocked"


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AgentStatus(str, enum.Enum):
    active = "active"
    idle = "idle"
    working = "working"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text, default="")
    team = Column(String(500), default="")
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    agents = relationship("Agent", back_populates="project")
    tasks = relationship("Task", back_populates="project")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    role = Column(String(200), default="")
    status = Column(String(50), default=AgentStatus.active.value)
    current_task = Column(String(300), default="")
    main_files = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="agents")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default=TaskStatus.backlog.value)
    priority = Column(String(50), default=Priority.medium.value)
    assigned_to = Column(String(100), default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    jira_key = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="tasks")


class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, index=True)
    from_agent = Column(String(100), nullable=False)
    to_agent = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(100), default="direct")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
