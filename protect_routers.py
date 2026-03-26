#!/usr/bin/env python3
"""
Script para proteger TODOS los endpoints de routers con autenticación.
"""
import re
from pathlib import Path

ROUTERS_DIR = Path("/Users/lukeskywalker/.openclaw/workspace/projects/operations/backend/routers")

# Routers a proteger (excluye auth.py y __init__.py)
ROUTERS_TO_PROTECT = [
    "dashboard.py",
    "comms.py",
    "files.py",
    "jira_sync.py",
    "transcripts.py",
    "users.py",
    "teams.py",
    "agent_api.py",
    "epics.py",
]

# Endpoints que requieren admin en DELETE o POST/PATCH de recursos críticos
ADMIN_ENDPOINTS = {
    "delete",  # Todos los DELETE
    "create_project",
    "update_project",
    "create_agent",
    "update_agent",
    "delete_agent",
    "delete_task",
}


def add_auth_imports(content: str) -> str:
    """Agrega imports de auth si no existen"""
    if "from routers.auth import" in content:
        return content
    
    # Encontrar línea después de imports de models
    lines = content.split("\n")
    insert_index = -1
    
    for i, line in enumerate(lines):
        if line.startswith("from models import") or line.startswith("from database import"):
            insert_index = i + 1
    
    if insert_index > 0:
        # Agregar User a models import si no existe
        for i, line in enumerate(lines):
            if line.startswith("from models import") and "User" not in line:
                lines[i] = line.replace("from models import", "from models import User,")
                break
        
        # Agregar auth imports
        lines.insert(insert_index, "from routers.auth import get_current_user, require_admin")
        
    return "\n".join(lines)


def protect_endpoint(match: re.Match, func_name: str) -> str:
    """Protege un endpoint agregando current_user dependency"""
    decorator = match.group(1)
    func_def = match.group(2)
    
    # Si ya tiene current_user, skip
    if "current_user" in func_def:
        return match.group(0)
    
    # Determinar si requiere admin
    needs_admin = any(pattern in func_name for pattern in ADMIN_ENDPOINTS)
    auth_dep = "require_admin" if needs_admin else "get_current_user"
    
    # Encontrar último parámetro antes del cierre
    if "):" in func_def:
        func_def = func_def.replace(
            "):",
            f",\n    current_user: User = Depends({auth_dep})\n):"
        )
    elif "," in func_def and func_def.rstrip().endswith(","):
        func_def = func_def.rstrip().rstrip(",")
        func_def += f",\n    current_user: User = Depends({auth_dep})\n):"
    
    return f"{decorator}\n{func_def}"


def protect_router_file(filepath: Path) -> None:
    """Protege todos los endpoints de un router"""
    print(f"🔒 Protegiendo {filepath.name}...")
    
    content = filepath.read_text()
    
    # 1. Agregar imports
    content = add_auth_imports(content)
    
    # 2. Proteger endpoints
    # Pattern: captura @router.MÉTODO(...) seguido de def función(...)
    pattern = r'(@router\.(get|post|patch|delete|put)\([^)]+\))\s*\ndef\s+(\w+)\s*\(([^)]*)\):'
    
    def replace_func(match):
        func_name = match.group(3)
        return protect_endpoint(match, func_name)
    
    content = re.sub(pattern, replace_func, content, flags=re.MULTILINE)
    
    # Escribir de vuelta
    filepath.write_text(content)
    print(f"   ✅ {filepath.name} protegido")


def main():
    print("🚨 PROTEGIENDO ENDPOINTS DE OPERATIONS BACKEND\n")
    
    for router_file in ROUTERS_TO_PROTECT:
        filepath = ROUTERS_DIR / router_file
        if filepath.exists():
            protect_router_file(filepath)
        else:
            print(f"   ⚠️  {router_file} no encontrado")
    
    print("\n✅ PROTECCIÓN COMPLETA")


if __name__ == "__main__":
    main()
