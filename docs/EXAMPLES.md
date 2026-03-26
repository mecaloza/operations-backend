# API Examples 🧪

Ejemplos completos de curl para todos los flujos comunes de Operations Dashboard API.

---

## 📋 Tabla de Contenidos

- [Setup](#setup)
- [Proyectos](#proyectos)
- [Agentes](#agentes)
- [Tareas](#tareas)
- [Épicas](#épicas)
- [Dashboard](#dashboard)
- [Comunicación](#comunicación)
- [Files](#files)
- [Jira Sync](#jira-sync)

---

## Setup

### Variables de Entorno

```bash
export API_BASE="https://ops-backend-production-e8ce.up.railway.app/api/v1"
# o para local:
# export API_BASE="http://localhost:8000/api/v1"
```

### Health Check

```bash
curl https://ops-backend-production-e8ce.up.railway.app/health
# {"status":"ok"}
```

---

## Proyectos

### Listar Todos los Proyectos

```bash
curl "$API_BASE/projects"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Action Experience",
    "slug": "action-experience",
    "description": "Action Experience product",
    "team": "Luke ⚔️, Yoda 🧙",
    "status": "active",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

---

### Filtrar Proyectos por Status

```bash
curl "$API_BASE/projects?status=active"
```

---

### Obtener Proyecto por ID

```bash
curl "$API_BASE/projects/1"
```

---

### Crear Proyecto

```bash
curl -X POST "$API_BASE/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Project",
    "slug": "new-project",
    "description": "A brand new project",
    "team": "Agent1, Agent2",
    "status": "active"
  }'
```

**Response:** `201 Created`
```json
{
  "id": 4,
  "name": "New Project",
  "slug": "new-project",
  "description": "A brand new project",
  "team": "Agent1, Agent2",
  "status": "active",
  "created_at": "2025-03-25T22:00:00Z"
}
```

---

### Actualizar Proyecto

```bash
curl -X PATCH "$API_BASE/projects/4" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "status": "completed"
  }'
```

---

### Eliminar Proyecto

```bash
curl -X DELETE "$API_BASE/projects/4"
# 204 No Content (sin response body)
```

---

## Agentes

### Listar Todos los Agentes

```bash
curl "$API_BASE/agents"
```

**Response:**
```json
[
  {
    "id": 7,
    "name": "Shosanna 🔥",
    "role": "Backend Engineer",
    "status": "active",
    "current_task": "Writing API docs",
    "main_files": "main.py, schemas.py",
    "project_id": 3,
    "created_at": "2025-02-01T08:00:00Z"
  }
]
```

---

### Filtrar Agentes por Proyecto

```bash
curl "$API_BASE/agents?project_id=3"
```

---

### Obtener Agente por ID

```bash
curl "$API_BASE/agents/7"
```

---

### Crear Agente

```bash
curl -X POST "$API_BASE/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NewAgent 🚀",
    "role": "QA Engineer",
    "status": "active",
    "current_task": "",
    "main_files": "",
    "project_id": 2
  }'
```

**Response:** `201 Created`

---

### Actualizar Agente (Cambiar Status y Tarea Actual)

```bash
curl -X PATCH "$API_BASE/agents/7" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "working",
    "current_task": "Deploying to production"
  }'
```

---

### Eliminar Agente

```bash
curl -X DELETE "$API_BASE/agents/7"
# 204 No Content
```

---

## Tareas

### Listar Todas las Tareas

```bash
curl "$API_BASE/tasks"
```

---

### Filtrar Tareas por Proyecto

```bash
curl "$API_BASE/tasks?project_id=3"
```

---

### Filtrar Tareas por Status

```bash
curl "$API_BASE/tasks?status=in_progress"
```

---

### Filtrar Tareas por Agente Asignado

```bash
curl "$API_BASE/tasks?assigned_to=Shosanna%20%F0%9F%94%A5"
# URL-encoded: Shosanna 🔥
```

---

### Excluir Tareas Done Antiguas (>5 días)

```bash
curl "$API_BASE/tasks?include_old_done=false"
# Este es el comportamiento por defecto
```

---

### Combinar Filtros

```bash
curl "$API_BASE/tasks?project_id=3&status=in_progress&assigned_to=Shosanna%20%F0%9F%94%A5"
```

---

### Obtener Board Kanban

```bash
curl "$API_BASE/tasks/kanban/3"
```

**Response:**
```json
{
  "backlog": [
    {"id": 1, "title": "Task 1", ...}
  ],
  "in_progress": [
    {"id": 2, "title": "Task 2", ...}
  ],
  "done": [
    {"id": 3, "title": "Task 3", ...}
  ],
  "blocked": []
}
```

---

### Crear Tarea

```bash
curl -X POST "$API_BASE/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement rate limiting",
    "description": "Add rate limiting middleware to all endpoints",
    "status": "backlog",
    "priority": "high",
    "assigned_to": "Shosanna 🔥",
    "project_id": 3,
    "jira_key": null
  }'
```

**Response:** `201 Created`
```json
{
  "id": 42,
  "title": "Implement rate limiting",
  "description": "Add rate limiting middleware to all endpoints",
  "status": "backlog",
  "priority": "high",
  "assigned_to": "Shosanna 🔥",
  "project_id": 3,
  "jira_key": null,
  "created_at": "2025-03-25T22:00:00Z",
  "updated_at": "2025-03-25T22:00:00Z"
}
```

---

### Actualizar Status de Tarea (Optimizado)

```bash
curl -X PATCH "$API_BASE/tasks/42/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress"
  }'
```

**Nota:** Este endpoint valida transiciones. Si la transición es inválida:

```bash
curl -X PATCH "$API_BASE/tasks/42/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'

# Error: 400 Bad Request
# {"detail": "Invalid status transition: done → done"}
```

---

### Actualizar Tarea Completa

```bash
curl -X PATCH "$API_BASE/tasks/42" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement rate limiting + logging",
    "description": "Updated description with more details",
    "priority": "critical"
  }'
```

---

### Bulk Update (Marcar Múltiples Tareas como Done)

```bash
curl -X PATCH "$API_BASE/tasks/bulk-update" \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [10, 11, 12, 13],
    "status": "done"
  }'
```

**Response:**
```json
{
  "updated_count": 3,
  "total_requested": 4,
  "errors": [
    {
      "task_id": 12,
      "error": "Invalid transition: done → done"
    }
  ]
}
```

---

### Eliminar Tarea

```bash
curl -X DELETE "$API_BASE/tasks/42"
# 204 No Content
```

---

## Épicas

### Listar Épicas

```bash
curl "$API_BASE/epics"
```

---

### Filtrar Épicas por Proyecto

```bash
curl "$API_BASE/epics?project_id=3"
```

---

### Filtrar Épicas por Status

```bash
curl "$API_BASE/epics?status=active"
```

---

### Obtener Épica por ID

```bash
curl "$API_BASE/epics/1"
```

**Response:**
```json
{
  "id": 1,
  "title": "Authentication System",
  "description": "Complete auth with JWT",
  "project_id": 3,
  "target_progress": 100.0,
  "calculated_progress": 65.5,
  "status": "active",
  "created_at": "2025-03-01T00:00:00Z",
  "updated_at": "2025-03-25T20:00:00Z"
}
```

---

### Crear Épica

```bash
curl -X POST "$API_BASE/epics" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "User Management",
    "description": "Complete CRUD for users",
    "project_id": 3,
    "target_progress": 100.0,
    "status": "active"
  }'
```

**Response:** `201 Created`
```json
{
  "id": 5,
  "title": "User Management",
  "description": "Complete CRUD for users",
  "project_id": 3,
  "target_progress": 100.0,
  "calculated_progress": 0.0,
  "status": "active",
  "created_at": "2025-03-25T22:00:00Z",
  "updated_at": "2025-03-25T22:00:00Z"
}
```

---

### Actualizar Épica

```bash
curl -X PATCH "$API_BASE/epics/5" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

---

### Eliminar Épica (Soft Delete)

```bash
curl -X DELETE "$API_BASE/epics/5"
# 204 No Content
# La épica se marca como deleted=True (no se borra físicamente)
```

---

### Listar Sub-Tareas de una Épica

```bash
curl "$API_BASE/epics/1/tasks"
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Backend API",
    "epic_id": 1,
    "progress": 80.0,
    "assigned_to": "Shosanna 🔥",
    "status": "in_progress",
    "created_at": "2025-03-10T00:00:00Z",
    "updated_at": "2025-03-25T18:00:00Z"
  }
]
```

---

### Crear Sub-Tarea

```bash
curl -X POST "$API_BASE/epics/1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write integration tests",
    "progress": 0.0,
    "assigned_to": "Stiglitz 🎯",
    "status": "backlog"
  }'
```

**Response:** `201 Created`

**Side Effect:** `Epic.calculated_progress` se recalcula automáticamente.

---

### Actualizar Progreso de Sub-Tarea

```bash
curl -X PATCH "$API_BASE/epic-tasks/1" \
  -H "Content-Type: application/json" \
  -d '{
    "progress": 100.0,
    "status": "done"
  }'
```

**Side Effects:**
1. `Epic.calculated_progress` se recalcula
2. Se guarda un snapshot en `EpicProgressHistory`

---

### Eliminar Sub-Tarea (Soft Delete)

```bash
curl -X DELETE "$API_BASE/epic-tasks/1"
# 204 No Content
```

**Side Effect:** `Epic.calculated_progress` se recalcula.

---

### Obtener Sprint Report

```bash
curl "$API_BASE/projects/3/sprint-report"
```

**Response:**
```json
{
  "project_id": 3,
  "project_name": "Operations",
  "total_progress": 68.3,
  "epics": [
    {
      "id": 1,
      "title": "Authentication System",
      "progress": 65.5,
      "target_progress": 100.0,
      "status": "active",
      "tasks": [
        {
          "title": "Backend API",
          "progress": 80.0,
          "assigned_to": "Shosanna 🔥",
          "status": "in_progress"
        },
        {
          "title": "Frontend Integration",
          "progress": 50.0,
          "assigned_to": "Marcel 🎬",
          "status": "in_progress"
        }
      ]
    }
  ]
}
```

---

## Dashboard

### Obtener Stats Globales

```bash
curl "$API_BASE/dashboard/stats"
```

**Response:**
```json
{
  "total_projects": 3,
  "total_agents": 8,
  "tasks_done": 42,
  "tasks_in_progress": 15,
  "tasks_backlog": 23,
  "tasks_by_project": [
    {
      "project_id": 1,
      "project_name": "Action Experience",
      "backlog": 10,
      "in_progress": 5,
      "done": 20
    },
    {
      "project_id": 2,
      "project_name": "Action Colleague",
      "backlog": 8,
      "in_progress": 7,
      "done": 15
    },
    {
      "project_id": 3,
      "project_name": "Operations",
      "backlog": 5,
      "in_progress": 3,
      "done": 7
    }
  ]
}
```

---

## Comunicación

### Listar Logs de Comunicación

```bash
curl "$API_BASE/comms"
```

**Response:**
```json
[
  {
    "id": 1,
    "from_agent": "Shosanna 🔥",
    "to_agent": "Marcel 🎬",
    "message": "API contract updated. Check Swagger.",
    "channel": "slack",
    "timestamp": "2025-03-25T20:00:00Z"
  }
]
```

---

### Filtrar por Agente

```bash
curl "$API_BASE/comms?agent=Shosanna%20%F0%9F%94%A5"
# Devuelve logs donde Shosanna es from o to
```

---

### Filtrar por Canal

```bash
curl "$API_BASE/comms?channel=slack"
```

---

### Limitar Resultados

```bash
curl "$API_BASE/comms?limit=10"
# Máximo: 200
```

---

### Crear Log de Comunicación

```bash
curl -X POST "$API_BASE/comms" \
  -H "Content-Type: application/json" \
  -d '{
    "from_agent": "Shosanna 🔥",
    "to_agent": "Hans Landa 🎬",
    "message": "✅ Deployed backend to production. All tests passing.",
    "channel": "slack"
  }'
```

**Response:** `201 Created`

---

### Timeline de Comunicaciones

```bash
curl "$API_BASE/comms/timeline?limit=50"
```

**Nota:** Ordena por timestamp DESC (más reciente primero).

---

## Files

### Obtener Árbol de Archivos

```bash
curl "$API_BASE/files/tree/operations"
```

**Response:**
```json
{
  "project": "operations",
  "root": "projects/operations/backend",
  "tree": [
    {
      "name": "routers",
      "type": "directory",
      "path": "projects/operations/backend/routers",
      "children": [
        {
          "name": "projects.py",
          "type": "file",
          "path": "projects/operations/backend/routers/projects.py",
          "size": 2048
        }
      ]
    }
  ]
}
```

---

### Controlar Profundidad

```bash
curl "$API_BASE/files/tree/operations?depth=2"
# Profundidad: 1-6 (default: 3)
```

---

### Leer Archivo

```bash
curl "$API_BASE/files/read?path=projects/operations/backend/main.py"
```

**Response:**
```json
{
  "path": "projects/operations/backend/main.py",
  "content": "from fastapi import FastAPI\n...",
  "size": 3500
}
```

**Errores:**
- `404`: Archivo no existe
- `413`: Archivo > 500KB

---

## Jira Sync

### Sincronizar Tareas desde Jira

```bash
curl -X POST "$API_BASE/jira/sync/operations"
```

**Prerequisitos:**
- Variables de entorno configuradas en Railway:
  ```bash
  JIRA_DOMAIN=your-domain.atlassian.net
  JIRA_EMAIL=your-email@example.com
  JIRA_API_TOKEN=your-api-token
  ```

**Response:** `200 OK`
```json
{
  "synced": 15,
  "project": "Operations"
}
```

**Comportamiento:**
- Busca issues del proyecto con JQL: `project = "OPERATIONS" ORDER BY created DESC`
- Limita a 100 issues más recientes
- Si la tarea ya existe (por `jira_key`), la actualiza
- Si es nueva, la crea

**Mapeo de Status:**
```
Jira              → Operations
─────────────────────────────────
"To Do"           → backlog
"In Progress"     → in_progress
"Done"            → done
"Blocked"         → blocked
```

**Mapeo de Priority:**
```
Jira              → Operations
─────────────────────────────────
"Highest"         → critical
"High"            → high
"Medium"          → medium
"Low/Lowest"      → low
```

**Errores:**
- `404`: Proyecto no encontrado
- `500`: Credenciales de Jira no configuradas o API error

---

## Flujos Completos de Ejemplo

### Flujo 1: Crear Proyecto con Épica y Sub-Tareas

```bash
# 1. Crear proyecto
PROJ=$(curl -X POST "$API_BASE/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"New Product","slug":"new-product","description":"Revolutionary product","team":"Team Alpha","status":"active"}' \
  | jq -r '.id')

echo "Created project ID: $PROJ"

# 2. Crear épica
EPIC=$(curl -X POST "$API_BASE/epics" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"MVP Features\",\"description\":\"Core features for MVP\",\"project_id\":$PROJ,\"status\":\"active\"}" \
  | jq -r '.id')

echo "Created epic ID: $EPIC"

# 3. Crear sub-tarea 1
curl -X POST "$API_BASE/epics/$EPIC/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title":"User authentication","progress":0,"assigned_to":"Agent1","status":"backlog"}'

# 4. Crear sub-tarea 2
curl -X POST "$API_BASE/epics/$EPIC/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title":"Dashboard UI","progress":0,"assigned_to":"Agent2","status":"backlog"}'

# 5. Ver sprint report
curl "$API_BASE/projects/$PROJ/sprint-report" | jq
```

---

### Flujo 2: Agente Consulta y Completa Tareas

```bash
AGENT="Shosanna 🔥"

# 1. Consultar tareas asignadas
TASKS=$(curl "$API_BASE/tasks?assigned_to=Shosanna%20%F0%9F%94%A5&status=backlog" | jq -r '.[0].id')

echo "Found task ID: $TASKS"

# 2. Mover a in_progress
curl -X PATCH "$API_BASE/tasks/$TASKS/status" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'

# 3. Trabajar en la tarea...
# ...

# 4. Actualizar con transcript y marcar done
curl -X PATCH "$API_BASE/tasks/$TASKS" \
  -H "Content-Type: application/json" \
  -d '{
    "status":"done",
    "description":"## Task Completed\n\n### Actions:\n1. Implemented feature X\n2. Wrote tests\n3. Deployed\n\n### Result: ✅"
  }'

# 5. Loguear comunicación
curl -X POST "$API_BASE/comms" \
  -H "Content-Type: application/json" \
  -d "{\"from_agent\":\"$AGENT\",\"to_agent\":\"Hans Landa 🎬\",\"message\":\"✅ Task $TASKS completed and deployed.\",\"channel\":\"slack\"}"
```

---

### Flujo 3: Reportar Progreso en Épica

```bash
EPIC_TASK_ID=15

# 1. Actualizar progreso a 25%
curl -X PATCH "$API_BASE/epic-tasks/$EPIC_TASK_ID" \
  -H "Content-Type: application/json" \
  -d '{"progress":25.0,"status":"in_progress"}'

# 2. Continuar trabajando...
# ...

# 3. Actualizar progreso a 50%
curl -X PATCH "$API_BASE/epic-tasks/$EPIC_TASK_ID" \
  -H "Content-Type: application/json" \
  -d '{"progress":50.0}'

# 4. Completar
curl -X PATCH "$API_BASE/epic-tasks/$EPIC_TASK_ID" \
  -H "Content-Type: application/json" \
  -d '{"progress":100.0,"status":"done"}'

# 5. Ver progreso total de la épica
EPIC_ID=$(curl "$API_BASE/epic-tasks/$EPIC_TASK_ID" | jq -r '.epic_id')
curl "$API_BASE/epics/$EPIC_ID" | jq '.calculated_progress'
```

---

## Uso con jq (JSON Processing)

### Extraer Solo IDs

```bash
curl "$API_BASE/projects" | jq '.[].id'
# 1
# 2
# 3
```

---

### Filtrar por Nombre

```bash
curl "$API_BASE/agents" | jq '.[] | select(.name | contains("Shosanna"))'
```

---

### Contar Tareas por Status

```bash
curl "$API_BASE/tasks" | jq 'group_by(.status) | map({status: .[0].status, count: length})'
```

**Output:**
```json
[
  {"status": "backlog", "count": 23},
  {"status": "in_progress", "count": 15},
  {"status": "done", "count": 42}
]
```

---

### Pretty Print

```bash
curl "$API_BASE/projects/1" | jq .
```

---

## Tips

### Guardar API Key como Variable (Futuro)

Cuando se implemente autenticación:

```bash
export API_KEY="sk-agent-abc123..."

curl "$API_BASE/tasks" \
  -H "X-API-Key: $API_KEY"
```

---

### Verbose Mode (Ver Headers)

```bash
curl -v "$API_BASE/projects"
```

---

### Solo Headers (No Body)

```bash
curl -I "$API_BASE/health"
```

---

### Timeout

```bash
curl --max-time 30 "$API_BASE/jira/sync/operations"
```

---

### Retry en Caso de Falla

```bash
curl --retry 3 --retry-delay 5 "$API_BASE/health"
```

---

**Última actualización:** 2025-03-25  
**Versión:** 1.0.0  
**Mantenido por:** Shosanna 🔥 & Padawan 👨‍💻
