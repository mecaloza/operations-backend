from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Any, Optional, List


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
    task_progress: Optional[float] = None


class TaskOut(TaskBase):
    id: int
    task_progress: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Alias para compatibilidad con spec
TaskResponse = TaskOut


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


# --- Epic (NEW SPEC: M2M con tareas existentes) ---
class EpicBase(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: int
    priority: str = "medium"
    progress: float = 0.0
    status: str = "not_started"
    goal: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None


class EpicCreate(EpicBase):
    pass


class EpicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    progress: Optional[float] = None
    status: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None


class EpicResponse(EpicBase):
    id: int
    created_at: datetime
    updated_at: datetime
    task_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class EpicDetailResponse(EpicResponse):
    tasks: List["TaskResponse"] = []
    evaluation_points: List["EvaluationPointResponse"] = []
    avg_evaluation_progress: Optional[float] = None

    model_config = {"from_attributes": True}


# Alias para compatibilidad
EpicOut = EpicResponse


# --- Epic Task Assignment ---
class AddTasksToEpicRequest(BaseModel):
    task_ids: List[int]


class AddEpicsToTaskRequest(BaseModel):
    epic_ids: List[int]


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
class TranscriptAttachmentBase(BaseModel):
    filename: str
    content_type: Optional[str] = None
    size_bytes: int = 0
    attachment_role: Optional[str] = None
    storage_path: Optional[str] = None
    content_text: Optional[str] = None
    content_hash: Optional[str] = None
    is_inline: bool = False
    attachment_metadata: Optional[dict[str, Any]] = None


class TranscriptAttachmentOut(TranscriptAttachmentBase):
    id: int
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    is_previewable: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptCreate(BaseModel):
    title: str
    content: str
    task_id: Optional[int] = None
    epic_id: Optional[int] = None
    project_id: int
    created_by: str
    tags: Optional[str] = ""
    source_type: Optional[str] = None
    source_message_id: Optional[str] = None
    source_thread_id: Optional[str] = None
    source_dedup_key: Optional[str] = None
    source_payload: Optional[dict[str, Any]] = None
    raw_email: Optional[str] = None
    transcript_full: Optional[str] = None
    summary_full: Optional[str] = None
    email_from: Optional[str] = None
    email_subject: Optional[str] = None
    email_received_at: Optional[datetime] = None
    attachments_json: Optional[list[dict[str, Any]]] = None


class TranscriptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    source_payload: Optional[dict[str, Any]] = None
    raw_email: Optional[str] = None
    transcript_full: Optional[str] = None
    summary_full: Optional[str] = None
    email_from: Optional[str] = None
    email_subject: Optional[str] = None
    email_received_at: Optional[datetime] = None
    attachments_json: Optional[list[dict[str, Any]]] = None


class TranscriptOut(BaseModel):
    id: int
    title: str
    content: str
    display_content: Optional[str] = None
    display_summary: Optional[str] = None
    task_id: Optional[int]
    epic_id: Optional[int]
    project_id: int  # Proyecto principal
    project_ids: List[int] = Field(default_factory=list)  # Todos los proyectos asociados (M2M)
    project_names: List[str] = Field(default_factory=list)  # Nombres para UI
    created_by: str
    version: int
    is_latest: bool
    tags: str
    file_size: Optional[int] = 0  # Nullable para registros legacy
    source_type: Optional[str] = None
    source_message_id: Optional[str] = None
    source_thread_id: Optional[str] = None
    source_dedup_key: Optional[str] = None
    source_payload: Optional[dict[str, Any]] = None
    raw_email: Optional[str] = None
    transcript_full: Optional[str] = None
    summary_full: Optional[str] = None
    email_from: Optional[str] = None
    email_subject: Optional[str] = None
    email_received_at: Optional[datetime] = None
    attachments_json: Optional[list[dict[str, Any]]] = None
    attachments: List["TranscriptAttachmentOut"] = Field(default_factory=list)
    image_attachments: List["TranscriptAttachmentOut"] = Field(default_factory=list)
    summary_attachments: List["TranscriptAttachmentOut"] = Field(default_factory=list)
    transcript_attachments: List["TranscriptAttachmentOut"] = Field(default_factory=list)
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


class TranscriptProjectUpdate(BaseModel):
    """Schema para actualizar proyectos asociados a un transcript"""
    project_ids: List[int]  # Lista completa de IDs (reemplaza existentes)


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


# --- Evaluation Points ---
class EvaluationPointCreate(BaseModel):
    category: str
    description: Optional[str] = None
    assigned_to: int
    progress: float = 0.0
    weight: float = 1.0


class EvaluationPointUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    progress: Optional[float] = None
    weight: Optional[float] = None


class EvaluationPointResponse(BaseModel):
    id: int
    epic_id: int
    category: str
    description: Optional[str]
    assigned_to: int
    assigned_to_name: Optional[str] = None  # Joined from users
    progress: float
    weight: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvaluationPointBulkUpdate(BaseModel):
    id: int
    progress: float
