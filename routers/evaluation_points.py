from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Epic, EpicEvaluationPoint, User
from schemas import (
    EvaluationPointCreate,
    EvaluationPointUpdate,
    EvaluationPointResponse,
    EvaluationPointBulkUpdate
)

router = APIRouter(prefix="/api/v1", tags=["evaluation-points"])


@router.get("/epics/{epic_id}/evaluation-points", response_model=List[EvaluationPointResponse])
def get_epic_evaluation_points(epic_id: int, db: Session = Depends(get_db)):
    """Listar puntos de evaluación de una épica"""
    # Validar que épica existe
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(404, f"Epic {epic_id} not found")
    
    points = db.query(EpicEvaluationPoint).filter(
        EpicEvaluationPoint.epic_id == epic_id
    ).all()
    
    # Join with users to get assigned_to_name
    result = []
    for p in points:
        user = db.query(User).filter(User.id == p.assigned_to).first()
        result.append({
            **p.__dict__,
            "assigned_to_name": user.full_name if user else None
        })
    
    return result


@router.post("/epics/{epic_id}/evaluation-points", response_model=EvaluationPointResponse, status_code=201)
def create_evaluation_point(
    epic_id: int,
    point: EvaluationPointCreate,
    db: Session = Depends(get_db)
):
    """Crear punto de evaluación"""
    # Validar que epic existe
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(404, f"Epic {epic_id} not found")
    
    # Validar que usuario existe
    user = db.query(User).filter(User.id == point.assigned_to).first()
    if not user:
        raise HTTPException(404, f"User {point.assigned_to} not found")
    
    # Validar progress 0-100
    if not (0 <= point.progress <= 100):
        raise HTTPException(400, "Progress must be between 0 and 100")
    
    new_point = EpicEvaluationPoint(
        epic_id=epic_id,
        category=point.category,
        description=point.description,
        assigned_to=point.assigned_to,
        progress=point.progress,
        weight=point.weight
    )
    db.add(new_point)
    db.commit()
    db.refresh(new_point)
    
    return {
        **new_point.__dict__,
        "assigned_to_name": user.full_name
    }


@router.get("/evaluation-points/{point_id}", response_model=EvaluationPointResponse)
def get_evaluation_point(point_id: int, db: Session = Depends(get_db)):
    """Obtener punto de evaluación"""
    point = db.query(EpicEvaluationPoint).filter(EpicEvaluationPoint.id == point_id).first()
    if not point:
        raise HTTPException(404, f"Evaluation point {point_id} not found")
    
    user = db.query(User).filter(User.id == point.assigned_to).first()
    return {
        **point.__dict__,
        "assigned_to_name": user.full_name if user else None
    }


@router.patch("/evaluation-points/{point_id}", response_model=EvaluationPointResponse)
def update_evaluation_point(
    point_id: int,
    update: EvaluationPointUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar punto de evaluación"""
    point = db.query(EpicEvaluationPoint).filter(EpicEvaluationPoint.id == point_id).first()
    if not point:
        raise HTTPException(404, f"Evaluation point {point_id} not found")
    
    # Validar assigned_to si se actualiza
    if update.assigned_to is not None:
        user = db.query(User).filter(User.id == update.assigned_to).first()
        if not user:
            raise HTTPException(404, f"User {update.assigned_to} not found")
    
    # Validar progress
    if update.progress is not None and not (0 <= update.progress <= 100):
        raise HTTPException(400, "Progress must be between 0 and 100")
    
    # Actualizar campos
    for key, value in update.dict(exclude_unset=True).items():
        setattr(point, key, value)
    
    db.commit()
    db.refresh(point)
    
    user = db.query(User).filter(User.id == point.assigned_to).first()
    return {
        **point.__dict__,
        "assigned_to_name": user.full_name if user else None
    }


@router.delete("/evaluation-points/{point_id}", status_code=204)
def delete_evaluation_point(point_id: int, db: Session = Depends(get_db)):
    """Eliminar punto de evaluación"""
    point = db.query(EpicEvaluationPoint).filter(EpicEvaluationPoint.id == point_id).first()
    if not point:
        raise HTTPException(404, f"Evaluation point {point_id} not found")
    
    db.delete(point)
    db.commit()


@router.patch("/epics/{epic_id}/evaluation-points/bulk", status_code=200)
def bulk_update_evaluation_points(
    epic_id: int,
    updates: List[EvaluationPointBulkUpdate],
    db: Session = Depends(get_db)
):
    """Actualizar múltiples puntos a la vez (para dailys)"""
    # Validar que épica existe
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(404, f"Epic {epic_id} not found")
    
    updated_count = 0
    for update in updates:
        point = db.query(EpicEvaluationPoint).filter(
            EpicEvaluationPoint.id == update.id,
            EpicEvaluationPoint.epic_id == epic_id
        ).first()
        
        if point and 0 <= update.progress <= 100:
            point.progress = update.progress
            updated_count += 1
    
    db.commit()
    return {"updated": updated_count}
