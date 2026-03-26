from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Agent, User
from schemas import AgentCreate, AgentUpdate, AgentOut
from routers.auth import get_current_user, require_admin

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/", response_model=list[AgentOut])
def list_agents(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Agent)
    if project_id:
        q = q.filter(Agent.project_id == project_id)
    return q.order_by(Agent.id).all()


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


@router.post(
    "/",
    response_model=AgentOut,
    status_code=201,
    summary="Crear agente",
    description="Registra un nuevo agente AI en el sistema. El nombre debe ser único.",
)
def create_agent(
    data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    agent = Agent(**data.model_dump(mode="json"))
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/{agent_id}", response_model=AgentOut)
def update_agent(
    agent_id: int,
    data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    for k, v in data.model_dump(exclude_unset=True, mode="json").items():
        setattr(agent, k, v)
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    db.delete(agent)
    db.commit()
