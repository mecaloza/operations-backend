from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal
from models import Base, Project, Agent

from routers import projects, agents, tasks, comms, files, jira_sync, dashboard


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


def _seed(db):
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


app = FastAPI(title="Operations Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://operations-dashboard-nine.vercel.app", "https://operations-dashboard-nine-mecalozas-projects.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(comms.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(jira_sync.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
