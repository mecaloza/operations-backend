from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Index, Table, Date, UniqueConstraint
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
    not_started = "not_started"
    in_progress = "in_progress"
    done = "done"


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
    epics = relationship("Epic", back_populates="project")


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
    task_progress = Column(Float, default=0.0)  # % manual (0.0 - 100.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="tasks")
    epic_assignments = relationship("EpicTaskAssignment", back_populates="task", cascade="all, delete-orphan")


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
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    priority = Column(String(20), default="medium")  # low/medium/high/critical
    progress = Column(Float, default=0.0)  # % manual (0.0 - 100.0)
    status = Column(String(50), default="not_started")  # not_started/in_progress/done
    goal = Column(Text)
    start_date = Column(Date, nullable=True)
    target_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="epics")
    task_assignments = relationship("EpicTaskAssignment", back_populates="epic", cascade="all, delete-orphan")
    evaluation_points = relationship("EpicEvaluationPoint", back_populates="epic", cascade="all, delete-orphan")


class EpicTaskAssignment(Base):
    __tablename__ = "epic_task_assignments"

    id = Column(Integer, primary_key=True, index=True)
    epic_id = Column(Integer, ForeignKey("epics.id", ondelete="CASCADE"))
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    epic = relationship("Epic", back_populates="task_assignments")
    task = relationship("Task", back_populates="epic_assignments")

    # Unique constraint
    __table_args__ = (UniqueConstraint('epic_id', 'task_id', name='uq_epic_task'),)


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


class EpicEvaluationPoint(Base):
    __tablename__ = "epic_evaluation_points"

    id = Column(Integer, primary_key=True, index=True)
    epic_id = Column(Integer, ForeignKey("epics.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100), nullable=False)  # Backend, Admin, Landing, etc.
    description = Column(Text)  # Qué involucra
    assigned_to = Column(Integer, ForeignKey("users.id"))  # Responsable
    progress = Column(Float, default=0.0)  # % actual (0.00 - 100.00)
    weight = Column(Float, default=1.0)  # Para promedio ponderado (futuro)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    epic = relationship("Epic", back_populates="evaluation_points")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index('idx_evaluation_points_epic', 'epic_id'),
        Index('idx_evaluation_points_user', 'assigned_to'),
    )


# TODO: Descomentar cuando exista tabla 'dailys'
# class DailyEvaluationPointProgress(Base):
#     __tablename__ = "daily_evaluation_point_progress"
#
#     id = Column(Integer, primary_key=True, index=True)
#     daily_id = Column(Integer, ForeignKey("dailys.id", ondelete="CASCADE"), nullable=False)
#     evaluation_point_id = Column(Integer, ForeignKey("epic_evaluation_points.id", ondelete="CASCADE"), nullable=False)
#     previous_progress = Column(Float)
#     new_progress = Column(Float)
#     delta = Column(Float)
#     notes = Column(Text)
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
#
#     # Unique constraint
#     __table_args__ = (
#         UniqueConstraint('daily_id', 'evaluation_point_id', name='uq_daily_eval_point'),
#     )
