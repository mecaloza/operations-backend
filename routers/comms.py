from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import CommunicationLog, User
from schemas import CommLogCreate, CommLogOut
from routers.auth import get_current_user

router = APIRouter(prefix="/comms", tags=["Communication"])


@router.get("/", response_model=list[CommLogOut])
def list_logs(
    agent: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(CommunicationLog)
    if agent:
        q = q.filter(or_(
            CommunicationLog.from_agent == agent,
            CommunicationLog.to_agent == agent,
        ))
    if channel:
        q = q.filter(CommunicationLog.channel == channel)
    return q.order_by(CommunicationLog.timestamp.desc()).limit(limit).all()


@router.post("/", response_model=CommLogOut, status_code=201)
def create_log(
    data: CommLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = CommunicationLog(**data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/timeline", response_model=list[CommLogOut])
def timeline(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(CommunicationLog)
        .order_by(CommunicationLog.timestamp.desc())
        .limit(limit)
        .all()
    )
