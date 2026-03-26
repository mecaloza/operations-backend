from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional
import io
from datetime import datetime, timezone

from database import get_db
from models import Transcript, TranscriptVersion, Task, Epic, Project
from schemas import (
    TranscriptCreate,
    TranscriptUpdate,
    TranscriptOut,
    TranscriptVersionOut,
    TranscriptQuery
)

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


def _validate_transcript_data(data: TranscriptCreate, db: Session):
    """Valida datos de transcript antes de crear"""
    # Al menos uno de task_id, epic_id debe estar presente
    if not data.task_id and not data.epic_id:
        raise HTTPException(
            status_code=400,
            detail="Al menos uno de task_id o epic_id debe estar presente"
        )
    
    # Validar que project_id existe
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Proyecto {data.project_id} no encontrado")
    
    # Validar task_id si existe
    if data.task_id:
        task = db.query(Task).filter(Task.id == data.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Tarea {data.task_id} no encontrada")
    
    # Validar epic_id si existe
    if data.epic_id:
        epic = db.query(Epic).filter(Epic.id == data.epic_id).first()
        if not epic:
            raise HTTPException(status_code=404, detail=f"Épica {data.epic_id} no encontrada")
    
    # Validar campos no vacíos
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
    db: Session = Depends(get_db)
):
    """Lista transcripts con filtros opcionales"""
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
        joinedload(Transcript.epic)
    ).all()
    
    # Mapear relaciones
    result = []
    for t in transcripts:
        t_dict = TranscriptOut.model_validate(t).model_dump()
        t_dict["related_task"] = t.task
        t_dict["related_epic"] = t.epic
        result.append(TranscriptOut(**t_dict))
    
    return result


@router.post("", response_model=TranscriptOut, status_code=201)
def create_transcript(data: TranscriptCreate, db: Session = Depends(get_db)):
    """Crea un nuevo transcript"""
    _validate_transcript_data(data, db)
    
    file_size = len(data.content.encode('utf-8'))
    
    transcript = Transcript(
        title=data.title,
        content=data.content,
        task_id=data.task_id,
        epic_id=data.epic_id,
        project_id=data.project_id,
        created_by=data.created_by,
        tags=data.tags or "",
        file_size=file_size,
        version=1,
        is_latest=True
    )
    
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    # Crear versión inicial
    version = TranscriptVersion(
        transcript_id=transcript.id,
        version=1,
        content=data.content,
        changed_by=data.created_by,
        change_summary="Versión inicial"
    )
    db.add(version)
    db.commit()
    
    # Cargar relaciones
    db.refresh(transcript)
    t_dict = TranscriptOut.model_validate(transcript).model_dump()
    t_dict["related_task"] = transcript.task
    t_dict["related_epic"] = transcript.epic
    
    return TranscriptOut(**t_dict)


@router.get("/{transcript_id}", response_model=TranscriptOut)
def get_transcript(transcript_id: int, db: Session = Depends(get_db)):
    """Obtiene detalle de un transcript"""
    transcript = db.query(Transcript).options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic)
    ).filter(
        Transcript.id == transcript_id,
        Transcript.is_latest == True
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")
    
    t_dict = TranscriptOut.model_validate(transcript).model_dump()
    t_dict["related_task"] = transcript.task
    t_dict["related_epic"] = transcript.epic
    
    return TranscriptOut(**t_dict)


@router.patch("/{transcript_id}", response_model=TranscriptOut)
def update_transcript(
    transcript_id: int,
    data: TranscriptUpdate,
    changed_by: str,
    change_summary: Optional[str] = "",
    db: Session = Depends(get_db)
):
    """Actualiza transcript (crea nueva versión automáticamente)"""
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.is_latest == True
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")
    
    # Guardar versión anterior
    old_version = TranscriptVersion(
        transcript_id=transcript.id,
        version=transcript.version,
        content=transcript.content,
        changed_by=changed_by,
        change_summary=f"Versión {transcript.version} archivada"
    )
    db.add(old_version)
    
    # Actualizar transcript
    new_version = transcript.version + 1
    
    if data.title is not None:
        transcript.title = data.title
    if data.content is not None:
        transcript.content = data.content
        transcript.file_size = len(data.content.encode('utf-8'))
    if data.tags is not None:
        transcript.tags = data.tags
    
    transcript.version = new_version
    transcript.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    # Crear nueva versión
    new_version_record = TranscriptVersion(
        transcript_id=transcript.id,
        version=new_version,
        content=transcript.content,
        changed_by=changed_by,
        change_summary=change_summary or f"Actualización a versión {new_version}"
    )
    db.add(new_version_record)
    db.commit()
    db.refresh(transcript)
    
    t_dict = TranscriptOut.model_validate(transcript).model_dump()
    t_dict["related_task"] = transcript.task
    t_dict["related_epic"] = transcript.epic
    
    return TranscriptOut(**t_dict)


@router.delete("/{transcript_id}")
def delete_transcript(transcript_id: int, db: Session = Depends(get_db)):
    """Marca transcript como no-latest (soft delete)"""
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")
    
    transcript.is_latest = False
    db.commit()
    
    return {"message": "Transcript marcado como eliminado"}


@router.get("/{transcript_id}/versions", response_model=list[TranscriptVersionOut])
def get_transcript_versions(transcript_id: int, db: Session = Depends(get_db)):
    """Obtiene historial de versiones de un transcript"""
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")
    
    versions = db.query(TranscriptVersion).filter(
        TranscriptVersion.transcript_id == transcript_id
    ).order_by(TranscriptVersion.version.desc()).all()
    
    return versions


@router.get("/{transcript_id}/download")
def download_transcript(transcript_id: int, db: Session = Depends(get_db)):
    """Descarga transcript como archivo .md"""
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.is_latest == True
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript no encontrado")
    
    # Crear archivo en memoria
    content = f"# {transcript.title}\n\n"
    content += f"**Creado por:** {transcript.created_by}\n"
    content += f"**Versión:** {transcript.version}\n"
    content += f"**Tags:** {transcript.tags}\n\n"
    content += "---\n\n"
    content += transcript.content
    
    file_stream = io.BytesIO(content.encode('utf-8'))
    filename = f"transcript_{transcript.id}_{transcript.title[:30].replace(' ', '_')}.md"
    
    return StreamingResponse(
        file_stream,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/upload", response_model=TranscriptOut, status_code=201)
async def upload_transcript(
    file: UploadFile = File(...),
    project_id: int = None,
    task_id: Optional[int] = None,
    epic_id: Optional[int] = None,
    created_by: str = "system",
    tags: Optional[str] = "",
    db: Session = Depends(get_db)
):
    """Sube un archivo .md/.txt como transcript"""
    if not file.filename.endswith(('.md', '.txt')):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .md o .txt")
    
    content = await file.read()
    content_str = content.decode('utf-8')
    
    # Usar nombre de archivo como título
    title = file.filename.replace('.md', '').replace('.txt', '').replace('_', ' ')
    
    data = TranscriptCreate(
        title=title,
        content=content_str,
        task_id=task_id,
        epic_id=epic_id,
        project_id=project_id,
        created_by=created_by,
        tags=tags
    )
    
    return create_transcript(data, db)


@router.get("/by-task/{task_id}", response_model=list[TranscriptOut])
def get_task_transcripts(task_id: int, db: Session = Depends(get_db)):
    """Lista transcripts de una tarea específica"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    transcripts = db.query(Transcript).options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic)
    ).filter(
        Transcript.task_id == task_id,
        Transcript.is_latest == True
    ).all()
    
    result = []
    for t in transcripts:
        t_dict = TranscriptOut.model_validate(t).model_dump()
        t_dict["related_task"] = t.task
        t_dict["related_epic"] = t.epic
        result.append(TranscriptOut(**t_dict))
    
    return result


@router.get("/by-epic/{epic_id}", response_model=list[TranscriptOut])
def get_epic_transcripts(epic_id: int, db: Session = Depends(get_db)):
    """Lista transcripts de una épica específica"""
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Épica no encontrada")
    
    transcripts = db.query(Transcript).options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic)
    ).filter(
        Transcript.epic_id == epic_id,
        Transcript.is_latest == True
    ).all()
    
    result = []
    for t in transcripts:
        t_dict = TranscriptOut.model_validate(t).model_dump()
        t_dict["related_task"] = t.task
        t_dict["related_epic"] = t.epic
        result.append(TranscriptOut(**t_dict))
    
    return result


@router.get("/by-project/{project_id}", response_model=list[TranscriptOut])
def get_project_transcripts(project_id: int, db: Session = Depends(get_db)):
    """Lista transcripts de un proyecto específico"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    transcripts = db.query(Transcript).options(
        joinedload(Transcript.task),
        joinedload(Transcript.epic)
    ).filter(
        Transcript.project_id == project_id,
        Transcript.is_latest == True
    ).all()
    
    result = []
    for t in transcripts:
        t_dict = TranscriptOut.model_validate(t).model_dump()
        t_dict["related_task"] = t.task
        t_dict["related_epic"] = t.epic
        result.append(TranscriptOut(**t_dict))
    
    return result
