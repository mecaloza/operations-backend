from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models import Team, User, Project
from schemas import TeamCreate, TeamUpdate, TeamOut, UserOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=List[TeamOut])
def list_teams(
    skip: int = 0,
    limit: int = 100,
    project_id: int = None,
    db: Session = Depends(get_db)
):
    """Listar equipos"""
    query = db.query(Team)
    if project_id:
        query = query.filter(Team.project_id == project_id)
    teams = query.offset(skip).limit(limit).all()
    return teams


@router.post("", response_model=TeamOut, status_code=201)
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    """Crear nuevo equipo"""
    # Validar que el proyecto existe
    project = db.query(Project).filter(Project.id == team.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Crear equipo
    db_team = Team(
        name=team.name,
        description=team.description,
        project_id=team.project_id
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Detalle de equipo"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return team


@router.patch("/{team_id}", response_model=TeamOut)
def update_team(team_id: int, team_update: TeamUpdate, db: Session = Depends(get_db)):
    """Actualizar equipo"""
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    # Validar proyecto si se actualiza
    if team_update.project_id:
        project = db.query(Project).filter(Project.id == team_update.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Actualizar campos
    update_data = team_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_team, field, value)

    db.commit()
    db.refresh(db_team)
    return db_team


@router.delete("/{team_id}", status_code=204)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    """Soft delete de equipo (elimina físicamente)"""
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    # Verificar si tiene miembros
    members_count = db.query(User).filter(User.team_id == team_id).count()
    if members_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar equipo con {members_count} miembros. Reasignar o eliminar miembros primero."
        )

    db.delete(db_team)
    db.commit()
    return None


@router.get("/{team_id}/members", response_model=List[UserOut])
def get_team_members(team_id: int, db: Session = Depends(get_db)):
    """Listar miembros del equipo"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    members = db.query(User).filter(User.team_id == team_id, User.active == True).all()
    return members
