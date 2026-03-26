import os
from typing import Optional
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Task, TaskStatus, Priority, Project, User
from routers.auth import require_admin

router = APIRouter(prefix="/jira", tags=["Jira Sync"])

SECRETS_PATH = Path(os.getenv("SECRETS_PATH", Path(__file__).resolve().parent.parent / ".secrets" / "jira.env"))

_jira_config: Optional[dict] = None


def _load_jira_config() -> dict:
    global _jira_config
    if _jira_config:
        return _jira_config
    cfg = {}
    if SECRETS_PATH.exists():
        for line in SECRETS_PATH.read_text().strip().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    else:
        cfg = {
            "JIRA_DOMAIN": os.getenv("JIRA_DOMAIN", ""),
            "JIRA_EMAIL": os.getenv("JIRA_EMAIL", ""),
            "JIRA_API_TOKEN": os.getenv("JIRA_API_TOKEN", ""),
        }
    if not cfg.get("JIRA_DOMAIN"):
        raise HTTPException(500, "Jira credentials not configured")
    _jira_config = cfg
    return cfg


JIRA_STATUS_MAP = {
    "to do": TaskStatus.backlog,
    "backlog": TaskStatus.backlog,
    "in progress": TaskStatus.in_progress,
    "in review": TaskStatus.in_progress,
    "done": TaskStatus.done,
    "blocked": TaskStatus.blocked,
}

JIRA_PRIORITY_MAP = {
    "highest": Priority.critical,
    "high": Priority.high,
    "medium": Priority.medium,
    "low": Priority.low,
    "lowest": Priority.low,
}


@router.post("/sync/{project_slug}")
async def sync_jira(
    project_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    cfg = _load_jira_config()
    project = db.query(Project).filter(Project.slug == project_slug).first()
    if not project:
        raise HTTPException(404, "Project not found")

    base_url = f"https://{cfg['JIRA_DOMAIN']}/rest/api/3"
    auth = (cfg["JIRA_EMAIL"], cfg["JIRA_API_TOKEN"])

    jql = f'project = "{project_slug.upper()}" ORDER BY created DESC'
    url = f"{base_url}/search?jql={jql}&maxResults=100"

    async with httpx.AsyncClient(auth=auth, timeout=30) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"Jira API error: {resp.text[:300]}")
        data = resp.json()

    synced = 0
    for issue in data.get("issues", []):
        fields = issue["fields"]
        jira_key = issue["key"]
        title = fields.get("summary", "")
        desc = fields.get("description")
        if isinstance(desc, dict):
            desc = str(desc)
        desc = desc or ""
        raw_status = (fields.get("status", {}).get("name", "") or "").lower()
        raw_priority = (fields.get("priority", {}).get("name", "") or "").lower()
        assignee = fields.get("assignee", {})
        assigned_name = assignee.get("displayName", "") if assignee else ""

        status = JIRA_STATUS_MAP.get(raw_status, TaskStatus.backlog)
        priority = JIRA_PRIORITY_MAP.get(raw_priority, Priority.medium)

        existing = db.query(Task).filter(Task.jira_key == jira_key).first()
        if existing:
            existing.title = title
            existing.description = desc
            existing.status = status
            existing.priority = priority
            existing.assigned_to = assigned_name
        else:
            db.add(Task(
                title=title,
                description=desc,
                status=status,
                priority=priority,
                assigned_to=assigned_name,
                project_id=project.id,
                jira_key=jira_key,
            ))
        synced += 1

    db.commit()
    return {"synced": synced, "project": project.name}
