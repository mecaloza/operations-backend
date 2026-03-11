from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models import TaskStatus, Priority, AgentStatus


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
    status: AgentStatus = AgentStatus.active
    current_task: str = ""
    main_files: str = ""
    project_id: Optional[int] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[AgentStatus] = None
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
    status: TaskStatus = TaskStatus.backlog
    priority: Priority = Priority.medium
    assigned_to: str = ""
    project_id: int
    jira_key: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    assigned_to: Optional[str] = None
    jira_key: Optional[str] = None


class TaskOut(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
