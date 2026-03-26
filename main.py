from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal
from models import Base, Project, Agent, AgentAuth, Task, Transcript, TranscriptVersion, Team, User

from routers import projects, agents, tasks, comms, files, jira_sync, dashboard, epics, agent_api, transcripts, users, teams, auth


SEED_PROJECTS = [
    {"name": "Action Experience", "slug": "action-experience", "description": "Action Experience product"},
    {"name": "Action Colleague", "slug": "action-colleague", "description": "Action Colleague product"},
    {"name": "Operations", "slug": "operations", "description": "Operations & tooling"},
]

SEED_AGENTS = [
    {"name": "Luke ⚔️", "role": "Lead Engineer", "project_slug": "action-experience"},
    {"name": "Yoda 🧙", "role": "Architect", "project_slug": "action-experience"},
    {"name": "Aldo Raine 🎬", "role": "Tech Lead", "project_slug": "action-colleague"},
    {"name": "Donowitz 🔨", "role": "Backend Engineer", "project_slug": "action-colleague"},
    {"name": "Stiglitz 🎯", "role": "Backend Engineer", "project_slug": "action-colleague"},
    {"name": "Hans Landa 🎬", "role": "QA Lead", "project_slug": "action-colleague"},
    {"name": "Shosanna 🔥", "role": "Ops Engineer", "project_slug": "operations"},
    {"name": "Marcel 🎬", "role": "Ops Engineer", "project_slug": "operations"},
]

SEED_USERS = [
    {"username": "padawan", "email": "padawan@ops.dev", "full_name": "Padawan", "password": "admin123", "role": "admin", "team_name": "Operations"},
    {"username": "hanslanda", "email": "hans@ops.dev", "full_name": "Hans Landa", "password": "leader123", "role": "leader", "team_name": "Operations"},
    {"username": "marcel", "email": "marcel@ops.dev", "full_name": "Marcel", "password": "member123", "role": "member", "team_name": "Operations"},
    {"username": "shosanna", "email": "shosanna@ops.dev", "full_name": "Shosanna", "password": "member123", "role": "member", "team_name": "Operations"},
]


def _seed(db):
    import uuid
    
    slug_to_project = {}
    for p in SEED_PROJECTS:
        proj = db.query(Project).filter_by(slug=p["slug"]).first()
        if not proj:
            proj = Project(name=p["name"], slug=p["slug"], description=p["description"])
            db.add(proj)
            db.flush()
        slug_to_project[p["slug"]] = proj

    for a in SEED_AGENTS:
        existing = db.query(Agent).filter_by(name=a["name"]).first()
        if not existing:
            project = slug_to_project[a["project_slug"]]
            agent = Agent(name=a["name"], role=a["role"], project_id=project.id)
            db.add(agent)

    # Seedear AgentAuth para cada Agent
    for a in SEED_AGENTS:
        existing_auth = db.query(AgentAuth).filter_by(agent_name=a["name"]).first()
        if not existing_auth:
            agent_auth = AgentAuth(
                agent_name=a["name"],
                api_key=str(uuid.uuid4()),
                permissions="read:tasks,write:tasks,read:projects,read:epics,read:transcripts,write:transcripts",
                rate_limit_per_minute=60,
                active=True
            )
            db.add(agent_auth)

    # Seedear Team de Operations (necesario para usuarios)
    ops_project = slug_to_project["operations"]
    ops_team = db.query(Team).filter_by(name="Operations", project_id=ops_project.id).first()
    if not ops_team:
        ops_team = Team(
            name="Operations",
            description="Equipo de operaciones y desarrollo del dashboard",
            project_id=ops_project.id
        )
        db.add(ops_team)
        db.flush()

    # Seedear Users
    for u in SEED_USERS:
        existing_user = db.query(User).filter_by(username=u["username"]).first()
        if not existing_user:
            user = User(
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                hashed_password=u["password"],  # Plain text por ahora
                role=u["role"],
                team_id=ops_team.id
            )
            db.add(user)

    db.commit()
    
    # Seedear transcripts de ejemplo
    _seed_transcripts(db, slug_to_project)


def _seed_transcripts(db, slug_to_project):
    """Seedear transcripts de ejemplo vinculados a tareas existentes"""
    # Obtener proyecto Operations
    ops_project = slug_to_project.get("operations")
    if not ops_project:
        return
    
    # Crear una tarea de ejemplo si no existe
    task = db.query(Task).filter_by(
        title="Sistema de Transcripts",
        project_id=ops_project.id
    ).first()
    
    if not task:
        task = Task(
            title="Sistema de Transcripts",
            description="Implementar sistema completo de transcripts vinculados a tareas y épicas",
            status="in_progress",
            priority="high",
            assigned_to="Shosanna 🔥",
            project_id=ops_project.id
        )
        db.add(task)
        db.flush()
    
    # Transcript 1: Planning
    if not db.query(Transcript).filter_by(title="Planning - Sistema de Transcripts").first():
        content1 = """# Planning - Sistema de Transcripts

## Objetivo
Crear un sistema completo para gestionar transcripts (documentación markdown) vinculados a tareas y épicas.

## Requisitos Funcionales
- ✅ Modelo Transcript con versionado
- ✅ Relaciones con Task, Epic, Project
- ✅ CRUD completo via API
- ✅ Upload/Download de archivos .md
- ✅ Historial de versiones automático
- ✅ Tags para categorización
- ✅ API para agentes AI

## Stack
- FastAPI + SQLAlchemy
- SQLite (local) / PostgreSQL (producción)
- Schemas con Pydantic

## Timeline
- Fase 1: Modelos y schemas ✅
- Fase 2: Router principal ✅
- Fase 3: Agent API ✅
- Fase 4: Testing e integración
"""
        
        transcript1 = Transcript(
            title="Planning - Sistema de Transcripts",
            content=content1,
            task_id=task.id,
            project_id=ops_project.id,
            created_by="Shosanna 🔥",
            tags="planning,backend,transcripts",
            file_size=len(content1.encode('utf-8')),
            version=1,
            is_latest=True
        )
        db.add(transcript1)
        db.flush()
        
        version1 = TranscriptVersion(
            transcript_id=transcript1.id,
            version=1,
            content=content1,
            changed_by="Shosanna 🔥",
            change_summary="Versión inicial - planning del sistema"
        )
        db.add(version1)
    
    # Transcript 2: Implementación
    if not db.query(Transcript).filter_by(title="Implementación - Modelos y Schemas").first():
        content2 = """# Implementación - Modelos y Schemas

## Modelo Transcript
- id, title (String 500)
- content (Text markdown)
- task_id, epic_id (FK nullable)
- project_id (FK)
- created_by (String 200)
- version, is_latest
- tags, file_size
- created_at, updated_at

## Validaciones
- Al menos task_id o epic_id requerido
- project_id obligatorio
- title y content no vacíos
- Versionado automático en updates

## Endpoints
- GET /transcripts - lista con filtros
- POST /transcripts - crear
- PATCH /transcripts/{id} - update con versionado
- GET /transcripts/{id}/download - descarga .md
"""
        
        transcript2 = Transcript(
            title="Implementación - Modelos y Schemas",
            content=content2,
            task_id=task.id,
            project_id=ops_project.id,
            created_by="Shosanna 🔥",
            tags="implementation,backend,models",
            file_size=len(content2.encode('utf-8')),
            version=1,
            is_latest=True
        )
        db.add(transcript2)
        db.flush()
        
        version2 = TranscriptVersion(
            transcript_id=transcript2.id,
            version=1,
            content=content2,
            changed_by="Shosanna 🔥",
            change_summary="Versión inicial - documentación técnica"
        )
        db.add(version2)
    
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Operations Dashboard API",
    description="""
## 🚀 Operations Dashboard Backend

Sistema centralizado de gestión de proyectos, agentes AI y tareas para el ecosistema Action Experience.

### Características principales:
- 📊 **Gestión de Proyectos**: CRUD completo de proyectos con estados y equipos
- 🤖 **Agentes AI**: Registro y seguimiento de agentes autónomos
- ✅ **Tareas**: Sistema de tareas con kanban, estados validados y bulk operations
- 🎯 **Épicas**: Planificación de features con sub-tareas y tracking de progreso
- 💬 **Comunicación**: Logs de comunicación entre agentes
- 🔄 **Jira Sync**: Sincronización bidireccional con Jira
- 📁 **Explorador de Archivos**: Navegación de estructura de proyectos

### Autenticación
- **Usuarios**: Pendiente implementación (OAuth/JWT)
- **Agentes AI**: Pendiente implementación (API Keys)

### Rate Limiting
- Producción: 100 req/min por IP (pendiente implementar)
- Local/Dev: Sin límites

### Source of Truth
Este backend es el **único source of truth** para todos los proyectos del ecosistema Action.
    """,
    version="1.0.0",
    contact={
        "name": "Padawan (Esteban Lozada)",
        "email": "padawan@action.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://operations-dashboard-nine.vercel.app", "https://operations-dashboard-nine-mecalozas-projects.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(comms.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(jira_sync.router, prefix="/api/v1")
app.include_router(epics.router, prefix="/api/v1")
app.include_router(agent_api.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(transcripts.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
