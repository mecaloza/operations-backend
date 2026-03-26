from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Index, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
import uuid

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


class EpicStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    blocked = "blocked"


class EpicTaskStatus(str, enum.Enum):
    backlog = "backlog"
    in_progress = "in_progress"
    done = "done"
    qa = "qa"


class UserRole(str, enum.Enum):
    admin = "admin"
    leader = "leader"
    member = "member"


# Tabla asociación M2M User <-> Agent
user_agent_association = Table(
    'user_agent_assignments',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('agent_id', Integer, ForeignKey('agents.id'), primary_key=True)
)


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
    teams = relationship("Team", back_populates="project")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="teams")
    members = relationship("User", back_populates="team")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Plain text por ahora
    role = Column(String(50), nullable=False, default=UserRole.member.value)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    active = Column(Boolean, default=True)  # Soft delete
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    team = relationship("Team", back_populates="members")
    assigned_agents = relationship("Agent", secondary=user_agent_association, back_populates="assigned_users")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    role = Column(String(200), default="")
    status = Column(String(50), default=AgentStatus.active.value)
    current_task = Column(String(300), default="")
    main_files = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    # assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # TODO: Migración pendiente
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="agents")
    assigned_users = relationship("User", secondary=user_agent_association, back_populates="assigned_agents")


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


class Epic(Base):
    __tablename__ = "epics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    target_progress = Column(Float, default=100.0)  # Meta objetivo (% target)
    calculated_progress = Column(Float, default=0.0)  # Auto-calculado desde sub-tareas
    status = Column(String(50), default=EpicStatus.active.value)
    deleted = Column(Boolean, default=False)  # Soft delete
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", backref="epics")
    tasks = relationship("EpicTask", back_populates="epic", cascade="all, delete-orphan")


class EpicTask(Base):
    __tablename__ = "epic_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False)
    progress = Column(Float, default=0.0)  # % completitud (0-100)
    assigned_to = Column(String(200), default="Sin asignar")  # Agente o humano
    status = Column(String(50), default=EpicTaskStatus.backlog.value)
    deleted = Column(Boolean, default=False)  # Soft delete
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    epic = relationship("Epic", back_populates="tasks")


class EpicProgressHistory(Base):
    __tablename__ = "epic_progress_history"

    id = Column(Integer, primary_key=True, index=True)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False)
    progress = Column(Float, nullable=False)  # Snapshot de % en ese momento
    snapshot_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    epic = relationship("Epic", backref="progress_history")


class AgentAuth(Base):
    """Agent API Authentication and Rate Limiting"""
    __tablename__ = "agent_auth"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False, unique=True, index=True)
    api_key = Column(String(36), nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    permissions = Column(Text, default="read:tasks,write:tasks,read:projects")  # Comma-separated permisos
    rate_limit_per_minute = Column(Integer, default=60)
    last_access = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_agent_auth_agent_name', 'agent_name'),
        Index('idx_agent_auth_api_key', 'api_key'),
    )


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # Markdown del transcript
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_by = Column(String(200), nullable=False)  # Nombre del agente/usuario
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)  # Solo última versión visible
    tags = Column(Text, default="")  # Comma-separated tags
    file_size = Column(Integer, default=0)  # Tamaño en bytes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", backref="transcripts")
    task = relationship("Task", backref="transcripts")
    epic = relationship("Epic", backref="transcripts")
    versions = relationship("TranscriptVersion", back_populates="transcript", cascade="all, delete-orphan")


class TranscriptVersion(Base):
    __tablename__ = "transcript_versions"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    changed_by = Column(String(200), nullable=False)
    change_summary = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    transcript = relationship("Transcript", back_populates="versions")
