from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# --- Project ---
class ProjectBase(BaseModel):
    name: str
    slug: str
    description: str = ""
    team: str = ""
    status: str = "active"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    team: Optional[str] = None
    status: Optional[str] = None


class ProjectOut(ProjectBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Agent ---
class AgentBase(BaseModel):
    name: str
    role: str = ""
    status: str = "active"
    current_task: str = ""
    main_files: str = ""
    project_id: Optional[int] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    current_task: Optional[str] = None
    main_files: Optional[str] = None
    project_id: Optional[int] = None


class AgentOut(AgentBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Task ---
class TaskBase(BaseModel):
    title: str
    description: str = ""
    status: str = "backlog"
    priority: str = "medium"
    assigned_to: str = ""
    project_id: int
    jira_key: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    jira_key: Optional[str] = None


class TaskOut(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskStatusUpdate(BaseModel):
    """Schema for updating only task status"""
    status: str


class BulkTaskUpdate(BaseModel):
    """Schema for bulk updating tasks"""
    task_ids: list[int]
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None


# --- Communication Log ---
class CommLogBase(BaseModel):
    from_agent: str
    to_agent: str
    message: str
    channel: str = "direct"


class CommLogCreate(CommLogBase):
    pass


class CommLogOut(CommLogBase):
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Epic ---
class EpicBase(BaseModel):
    title: str
    description: str = ""
    project_id: int
    target_progress: float = 100.0
    status: str = "active"


class EpicCreate(EpicBase):
    pass


class EpicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_progress: Optional[float] = None
    status: Optional[str] = None


class EpicOut(EpicBase):
    id: int
    calculated_progress: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Epic Task ---
class EpicTaskBase(BaseModel):
    title: str
    progress: float = 0.0
    assigned_to: str = "Sin asignar"
    status: str = "backlog"


class EpicTaskCreate(EpicTaskBase):
    pass


class EpicTaskUpdate(BaseModel):
    title: Optional[str] = None
    progress: Optional[float] = None
    assigned_to: Optional[str] = None
    status: Optional[str] = None


class EpicTaskOut(EpicTaskBase):
    id: int
    epic_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Sprint Report ---
class SprintEpicTask(BaseModel):
    title: str
    progress: float
    assigned_to: str
    status: str


class SprintEpic(BaseModel):
    id: int
    title: str
    progress: float
    target_progress: float
    status: str
    tasks: list[SprintEpicTask]


class SprintReport(BaseModel):
    project_id: int
    project_name: str
    total_progress: float
    epics: list[SprintEpic]


# --- AgentAuth ---
class AgentAuthCreate(BaseModel):
    """Schema for creating a new agent auth entry"""
    agent_name: str
    permissions: Optional[str] = "read:tasks,write:tasks,read:projects"


class AgentAuthOut(BaseModel):
    """Schema for agent auth output"""
    id: int
    agent_name: str
    api_key: str
    permissions: str
    rate_limit_per_minute: int
    last_access: Optional[datetime] = None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentAuthUpdate(BaseModel):
    """Schema for updating agent auth"""
    permissions: Optional[str] = None
    rate_limit_per_minute: Optional[int] = None
    active: Optional[bool] = None


class AgentTaskQuery(BaseModel):
    """Schema for filtering agent tasks"""
    status: Optional[str] = None
    priority: Optional[str] = None
    project_id: Optional[int] = None


# --- Transcript ---
class TranscriptCreate(BaseModel):
    title: str
    content: str
    task_id: Optional[int] = None
    epic_id: Optional[int] = None
    project_id: int
    created_by: str
    tags: Optional[str] = ""


class TranscriptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None


class TranscriptOut(BaseModel):
    id: int
    title: str
    content: str
    task_id: Optional[int]
    epic_id: Optional[int]
    project_id: int
    created_by: str
    version: int
    is_latest: bool
    tags: str
    file_size: int
    created_at: datetime
    updated_at: datetime
    related_task: Optional["TaskOut"] = None
    related_epic: Optional["EpicOut"] = None

    model_config = {"from_attributes": True}


class TranscriptVersionOut(BaseModel):
    id: int
    transcript_id: int
    version: int
    content: str
    changed_by: str
    change_summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptQuery(BaseModel):
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    epic_id: Optional[int] = None
    tags: Optional[str] = None
    created_by: Optional[str] = None


# --- Team ---
class TeamBase(BaseModel):
    name: str
    description: str = ""
    project_id: int


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None


class TeamOut(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- User ---
class UserBase(BaseModel):
    email: str
    username: str
    full_name: str
    role: str = "member"
    team_id: Optional[int] = None


class UserCreate(UserBase):
    password: str  # Plain text por ahora


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    team_id: Optional[int] = None
    active: Optional[bool] = None


class UserOut(UserBase):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserWithAgents(UserOut):
    """User con lista de agentes asignados"""
    assigned_agents: List["AgentOut"] = []

    model_config = {"from_attributes": True}
