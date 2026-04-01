from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models import User, Agent, UserRole
from schemas import UserCreate, UserUpdate, UserOut, UserWithAgents, AgentOut
from routers.auth import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Lista todos los usuarios (público para dropdowns)"""
    query = db.query(User)
    if active_only:
        query = query.filter(User.active == True)
    users = query.offset(skip).limit(limit).all()
    return users


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Crear nuevo usuario"""
    # Validar role
    if user.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail=f"Role inválido. Debe ser: admin, leader o member")

    # Validar email único
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    # Validar username único
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username ya registrado")

    # Crear usuario
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=user.password,  # Plain text por ahora
        role=user.role,
        team_id=user.team_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Detalle de usuario"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Actualizar usuario"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar email único si se actualiza
    if user_update.email and user_update.email != db_user.email:
        if db.query(User).filter(User.email == user_update.email).first():
            raise HTTPException(status_code=400, detail="Email ya registrado")

    # Validar username único si se actualiza
    if user_update.username and user_update.username != db_user.username:
        if db.query(User).filter(User.username == user_update.username).first():
            raise HTTPException(status_code=400, detail="Username ya registrado")

    # Validar role si se actualiza
    if user_update.role and user_update.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail=f"Role inválido. Debe ser: admin, leader o member")

    # Actualizar campos
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = update_data.pop("password")

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft delete de usuario"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Verificar si tiene agentes asignados
    if db_user.assigned_agents:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar usuario con {len(db_user.assigned_agents)} agentes asignados. Desasignar primero."
        )

    # Soft delete
    db_user.active = False
    db.commit()
    return None


@router.post("/{user_id}/assign-agent/{agent_id}", response_model=UserOut)
def assign_agent(
    user_id: int,
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Asignar agente a usuario"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado")

    # Verificar si ya está asignado
    if db_agent in db_user.assigned_agents:
        raise HTTPException(status_code=400, detail="Agente ya asignado a este usuario")

    db_user.assigned_agents.append(db_agent)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}/unassign-agent/{agent_id}", status_code=204)
def unassign_agent(
    user_id: int,
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Desasignar agente de usuario"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado")

    # Verificar si está asignado
    if db_agent not in db_user.assigned_agents:
        raise HTTPException(status_code=400, detail="Agente no está asignado a este usuario")

    db_user.assigned_agents.remove(db_agent)
    db.commit()
    return None


@router.get("/{user_id}/agents", response_model=List[AgentOut])
def get_user_agents(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Listar agentes asignados a usuario"""
    db_user = db.query(User).options(joinedload(User.assigned_agents)).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return db_user.assigned_agents
