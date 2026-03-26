from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Depends

from models import User
from routers.auth import get_current_user

router = APIRouter(prefix="/files", tags=["Files"])

import os
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", Path(__file__).resolve().parent.parent))

IGNORED = {".git", "__pycache__", "node_modules", ".next", ".venv", "venv", ".DS_Store", "*.pyc"}


def _should_ignore(name: str) -> bool:
    return name in IGNORED or name.startswith(".")


@router.get("/tree/{project_slug}")
def file_tree(
    project_slug: str,
    depth: int = Query(3, ge=1, le=6),
    current_user: User = Depends(get_current_user)
):
    project_dir = WORKSPACE_ROOT / "projects" / project_slug.replace("-", "/")
    if not project_dir.exists():
        alt = WORKSPACE_ROOT / "projects" / project_slug
        if alt.exists():
            project_dir = alt
        else:
            raise HTTPException(404, f"Project directory not found: {project_dir}")

    def _walk(directory: Path, current_depth: int) -> list[dict]:
        items = []
        if current_depth > depth:
            return items
        try:
            entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return items
        for entry in entries:
            if _should_ignore(entry.name):
                continue
            node = {"name": entry.name, "path": str(entry.relative_to(WORKSPACE_ROOT))}
            if entry.is_dir():
                node["type"] = "directory"
                node["children"] = _walk(entry, current_depth + 1)
            else:
                node["type"] = "file"
                node["size"] = entry.stat().st_size
            items.append(node)
        return items

    return {"project": project_slug, "root": str(project_dir.relative_to(WORKSPACE_ROOT)), "tree": _walk(project_dir, 1)}


@router.get("/read")
def read_file(
    path: str = Query(..., description="Relative path from workspace root"),
    current_user: User = Depends(get_current_user)
):
    full = WORKSPACE_ROOT / path
    if not full.exists() or not full.is_file():
        raise HTTPException(404, "File not found")
    if full.stat().st_size > 500_000:
        raise HTTPException(413, "File too large (max 500KB)")
    try:
        content = full.read_text(errors="replace")
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"path": path, "content": content, "size": full.stat().st_size}
