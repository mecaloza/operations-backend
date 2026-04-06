import io
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Epic, Project, Task, Transcript, TranscriptAttachment, TranscriptVersion, User
from plaud_utils import attachment_public_payload, transcript_display_summary, transcript_primary_text
from routers.auth import get_current_user
from schemas import (
    TranscriptCreate,
    TranscriptOut,
    TranscriptProjectUpdate,
    TranscriptUpdate,
    TranscriptVersionOut,
)

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


def _serialize_transcript(transcript: Transcript) -> TranscriptOut:
    attachments_payload = [attachment_public_payload(transcript.id, attachment) for attachment in transcript.attachments]
    payload = {
        "id": transcript.id,
        "title": transcript.title,
        "content": transcript.content,
        "display_content": transcript_primary_text(transcript),
        "display_summary": transcript_display_summary(transcript),
        "task_id": transcript.task_id,
        "epic_id": transcript.epic_id,
        "project_id": transcript.project_id,
        "project_ids": [p.id for p in transcript.projects],
        "project_names": [p.name for p in transcript.projects],
        "created_by": transcript.created_by,
        "version": transcript.version,
        "is_latest": transcript.is_latest,
        "tags": transcript.tags,
        "file_size": transcript.file_size,
        "source_type": transcript.source_type,
        "source_message_id": transcript.source_message_id,
        "source_thread_id": transcript.source_thread_id,
        "source_dedup_key": transcript.source_dedup_key,
        "source_payload": (json.loads(transcript.source_payload_json) if transcript.source_payload_json else None),
        "raw_email": transcript.raw_email,
        "transcript_full": transcript.transcript_full,
        "summary_full": transcript.summary_full,
        "email_from": transcript.email_from,
        "email_subject": transcript.email_subject,
        "email_received_at": transcript.email_received_at,
        "attachments_json": (json.loads(transcript.attachments_json) if transcript.attachments_json else None),
        "attachments": attachments_payload,
        "image_attachments": [attachment for attachment in attachments_payload if attachment["attachment_role"] == "image"],
        "summary_attachments": [attachment for attachment in attachments_payload if attachment["attachment_role"] == "summary"],
        "transcript_attachments": [attachment for attachment in attachments_payload if attachment["attachment_role"] == "transcript"],
        "created_at": transcript.created_at,
        "updated_at": transcript.updated_at,
        "related_task": transcript.task,
        "related_epic": transcript.epic,
    }
    return TranscriptOut.model_validate(payload)


def _validate_transcript_data(data: TranscriptCreate, db: Session):
    if not data.task_id and not data.epic_id:
        raise HTTPException(status_code=400, detail="Al menos uno de task_id o epic_id debe estar presente")

    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Proyecto {data.project_id} no encontrado")

    if data.task_id:
        task = db.query(Task).filter(Task.id == data.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Tarea {data.task_id} no encontrada")

    if data.epic_id:
        epic = db.query(Epic).filter(Epic.id == data.epic_id).first()
        if not epic:
            raise HTTPException(status_code=404, detail=f"Épica {data.epic_id} no encontrada")

    if not data.title.strip():
        raise HTTPException(status_code=400, detail="El título no puede estar vacío")
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="El contenido no puede estar vacío")


@router.get("", response_model=list[TranscriptOut])
def list_transcripts(
    project_id: Optional[int] = None,
    task_id: Optional[int] = None,
    epic_id: Optional[int] = None,
    tags: Optional[str] = None,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transcript).filter(Transcript.is_latest == True)

    if project_id:
        query = query.filter(Transcript.project_id == project_id)
    if task_id:
        query = query.filter(Transcript.task_id == task_id)
    if epic_id:
        query = query.filter(Transcript.epic_id == epic_id)
    if tags:
        query = query.filter(Transcript.tags.contains(tags))
    if created_by:
        query = query.filter(Transcript.created_by == created_by)

    transcripts = query.options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic),
        joinedload(Transcript.projects),
        joinedload(Transcript.attachments),
    ).all()

    return [_serialize_transcript(t) for t in transcripts]


@router.post("", response_model=TranscriptOut, status_code=201)
def create_transcript(
    data: TranscriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_transcript_data(data, db)

    transcript = Transcript(
        title=data.title,
        content=data.content,
        task_id=data.task_id,
        epic_id=data.epic_id,
        project_id=data.project_id,
        created_by=data.created_by,
        tags=data.tags or "",
        file_size=len(data.content.encode("utf-8")),
        version=1,
        is_latest=True,
        source_type=data.source_type,
        source_message_id=data.source_message_id,
        source_thread_id=data.source_thread_id,
        source_dedup_key=data.source_dedup_key,
        source_payload_json=json.dumps(data.source_payload, ensure_ascii=False) if data.source_payload is not None else None,
        raw_email=data.raw_email,
        transcript_full=data.transcript_full,
        summary_full=data.summary_full,
        email_from=data.email_from,
        email_subject=data.email_subject,
        email_received_at=data.email_received_at,
        attachments_json=json.dumps(data.attachments_json, ensure_ascii=False) if data.attachments_json is not None else None,
    )

    db.add(transcript)
    db.flush()

    project = db.query(Project).filter(Project.id == data.project_id).first()
    if project:
        transcript.projects.append(project)

    db.commit()
    db.refresh(transcript)

    version = TranscriptVersion(
        transcript_id=transcript.id,
        version=1,
        content=data.content,
        changed_by=data.created_by,
        change_summary="Versión inicial",
    )
    db.add(version)
    db.commit()
    db.refresh(transcript)

    return _serialize_transcript(transcript)


@router.get("/{transcript_id}", response_model=TranscriptOut)
def get_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transcript = db.query(Transcript).options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic),
        joinedload(Transcript.projects),
        joinedload(Transcript.attachments),
    ).filter(
        Transcript.id == transcript_id,
        Transcript.is_latest == True,
    ).first()

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")

    return _serialize_transcript(transcript)


@router.patch("/{transcript_id}", response_model=TranscriptOut)
def update_transcript(
    transcript_id: int,
    data: TranscriptUpdate,
    changed_by: str,
    change_summary: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transcript = db.query(Transcript).options(
        joinedload(Transcript.projects),
        joinedload(Transcript.attachments),
    ).filter(
        Transcript.id == transcript_id,
        Transcript.is_latest == True,
    ).first()

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")

    old_version = TranscriptVersion(
        transcript_id=transcript.id,
        version=transcript.version,
        content=transcript.content,
        changed_by=changed_by,
        change_summary=f"Versión {transcript.version} archivada",
    )
    db.add(old_version)

    new_version = transcript.version + 1

    if data.title is not None:
        transcript.title = data.title
    if data.content is not None:
        transcript.content = data.content
        transcript.file_size = len(data.content.encode("utf-8"))
    if data.tags is not None:
        transcript.tags = data.tags
    if data.source_payload is not None:
        transcript.source_payload_json = json.dumps(data.source_payload, ensure_ascii=False)
    if data.raw_email is not None:
        transcript.raw_email = data.raw_email
    if data.transcript_full is not None:
        transcript.transcript_full = data.transcript_full
    if data.summary_full is not None:
        transcript.summary_full = data.summary_full
    if data.email_from is not None:
        transcript.email_from = data.email_from
    if data.email_subject is not None:
        transcript.email_subject = data.email_subject
    if data.email_received_at is not None:
        transcript.email_received_at = data.email_received_at
    if data.attachments_json is not None:
        transcript.attachments_json = json.dumps(data.attachments_json, ensure_ascii=False)

    transcript.version = new_version
    transcript.updated_at = datetime.now(timezone.utc)

    db.commit()

    new_version_record = TranscriptVersion(
        transcript_id=transcript.id,
        version=new_version,
        content=transcript.content,
        changed_by=changed_by,
        change_summary=change_summary or f"Actualización a versión {new_version}",
    )
    db.add(new_version_record)
    db.commit()
    db.refresh(transcript)

    return _serialize_transcript(transcript)


@router.patch("/{transcript_id}/projects", response_model=TranscriptOut)
def update_transcript_projects(
    transcript_id: int,
    update: TranscriptProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transcript = db.query(Transcript).options(
        joinedload(Transcript.projects),
        joinedload(Transcript.attachments),
    ).filter(Transcript.id == transcript_id).first()

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")

    projects = db.query(Project).filter(Project.id.in_(update.project_ids)).all()
    if len(projects) != len(update.project_ids):
        raise HTTPException(status_code=400, detail="Uno o más project_ids no son válidos")

    transcript.projects = projects
    if update.project_ids:
        transcript.project_id = update.project_ids[0]

    db.commit()
    db.refresh(transcript)

    return _serialize_transcript(transcript)


@router.delete("/{transcript_id}")
def delete_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")

    transcript.is_latest = False
    db.commit()
    return {"message": "Transcript marcado como eliminado"}


@router.get("/{transcript_id}/versions", response_model=list[TranscriptVersionOut])
def get_transcript_versions(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")

    return db.query(TranscriptVersion).filter(
        TranscriptVersion.transcript_id == transcript_id
    ).order_by(TranscriptVersion.version.desc()).all()


@router.get("/{transcript_id}/download")
def download_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.is_latest == True,
    ).first()

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")

    content = f"# {transcript.title}\n\n"
    content += f"**Creado por:** {transcript.created_by}\n"
    content += f"**Versión:** {transcript.version}\n"
    content += f"**Tags:** {transcript.tags}\n\n"
    content += "---\n\n"
    content += transcript_primary_text(transcript)

    file_stream = io.BytesIO(content.encode("utf-8"))
    filename = f"transcript_{transcript.id}_{transcript.title[:30].replace(' ', '_')}.md"

    return StreamingResponse(
        file_stream,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{transcript_id}/attachments/{attachment_id}")
def get_transcript_attachment(
    transcript_id: int,
    attachment_id: int,
    disposition: str = Query(default="attachment", pattern="^(attachment|inline)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = db.query(TranscriptAttachment).join(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.is_latest == True,
        TranscriptAttachment.id == attachment_id,
        TranscriptAttachment.transcript_id == transcript_id,
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")

    if attachment.storage_path:
        file_path = Path(attachment.storage_path)
        if file_path.exists() and file_path.is_file():
            media_type = attachment.content_type or mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            return FileResponse(
                path=str(file_path),
                media_type=media_type,
                filename=attachment.filename,
                headers={"Content-Disposition": f'{disposition}; filename="{attachment.filename}"'},
            )

    if attachment.content_text is not None:
        media_type = attachment.content_type or "text/plain; charset=utf-8"
        file_stream = io.BytesIO(attachment.content_text.encode("utf-8"))
        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={"Content-Disposition": f'{disposition}; filename="{attachment.filename}"'},
        )

    raise HTTPException(status_code=404, detail="Adjunto sin archivo disponible")


@router.post("/upload", response_model=TranscriptOut, status_code=201)
async def upload_transcript(
    file: UploadFile = File(...),
    project_id: int = None,
    task_id: Optional[int] = None,
    epic_id: Optional[int] = None,
    created_by: str = "system",
    tags: Optional[str] = "",
    db: Session = Depends(get_db),
):
    if not file.filename.endswith((".md", ".txt")):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .md o .txt")

    content = await file.read()
    content_str = content.decode("utf-8")
    title = file.filename.replace(".md", "").replace(".txt", "").replace("_", " ")

    data = TranscriptCreate(
        title=title,
        content=content_str,
        task_id=task_id,
        epic_id=epic_id,
        project_id=project_id,
        created_by=created_by,
        tags=tags,
        source_type="upload",
    )

    return create_transcript(data, db, current_user=None)


@router.get("/by-task/{task_id}", response_model=list[TranscriptOut])
def get_task_transcripts(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    transcripts = db.query(Transcript).options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic),
        joinedload(Transcript.projects),
        joinedload(Transcript.attachments),
    ).filter(
        Transcript.task_id == task_id,
        Transcript.is_latest == True,
    ).all()

    return [_serialize_transcript(t) for t in transcripts]


@router.get("/by-epic/{epic_id}", response_model=list[TranscriptOut])
def get_epic_transcripts(
    epic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Épica no encontrada")

    transcripts = db.query(Transcript).options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic),
        joinedload(Transcript.projects),
        joinedload(Transcript.attachments),
    ).filter(
        Transcript.epic_id == epic_id,
        Transcript.is_latest == True,
    ).all()

    return [_serialize_transcript(t) for t in transcripts]


@router.get("/by-project/{project_id}", response_model=list[TranscriptOut])
def get_project_transcripts(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    transcripts = db.query(Transcript).options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic),
        joinedload(Transcript.projects),
        joinedload(Transcript.attachments),
    ).join(Transcript.projects).filter(
        Project.id == project_id,
        Transcript.is_latest == True,
    ).distinct().all()

    return [_serialize_transcript(t) for t in transcripts]
