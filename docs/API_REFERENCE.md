# API Reference - Operations Dashboard

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [Arquitectura](#arquitectura)
- [Autenticación](#autenticación)
- [Rate Limiting](#rate-limiting)
- [Códigos de Error](#códigos-de-error)
- [Endpoints](#endpoints)

---

## Introducción

**Operations Dashboard API** es el backend centralizado para la gestión de proyectos, agentes AI y tareas del ecosistema Action Experience.

### Características

- ✅ **Source of Truth único**: Todos los proyectos están aquí
- 🔄 **Sincronización con Jira**: Importa tareas automáticamente
- 🎯 **Sistema de Épicas**: Features complejas con sub-tareas
- 📊 **Dashboard en tiempo real**: Métricas de progreso y estado
- 🤖 **Agentes AI**: Registro y tracking de agentes autónomos
- 💬 **Communication Logs**: Historial de interacciones entre agentes

### URLs

- **Producción**: `https://ops-backend-production-e8ce.up.railway.app`
- **Local**: `http://localhost:8000`
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

---

## Arquitectura

### Stack Tecnológico

```
FastAPI 0.115+
├── SQLAlchemy (ORM)
├── Pydantic v2 (Validación)
├── Uvicorn (ASGI Server)
└── httpx (HTTP async client)
```

### Base de Datos

- **Local/Dev**: SQLite (`operations.db`)
- **Producción**: PostgreSQL (Supabase)
  - Host: `aws-0-us-west-1.pooler.supabase.com`
  - Database: `postgres`
  - Port: `6543` (pooler)

### Estructura de Módulos

```
backend/
├── main.py              # FastAPI app + lifespan + CORS
├── database.py          # Engine + SessionLocal
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
└── routers/
    ├── projects.py      # CRUD de proyectos
    ├── agents.py        # CRUD de agentes
    ├── tasks.py         # Tareas + kanban + bulk ops
    ├── epics.py         # Épicas + sub-tareas + sprint reports
    ├── dashboard.py     # Stats globales
    ├── comms.py         # Communication logs
    ├── files.py         # File tree + read files
    └── jira_sync.py     # Sincronización con Jira
```

---

## Autenticación

### Estado Actual: **Pendiente**

Por ahora todos los endpoints son públicos (se asume red privada o VPN).

### Implementación Futura

#### Para Usuarios Humanos
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "padawan@action.com",
  "password": "secure_password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### Para Agentes AI
```http
GET /api/v1/agents/me
Authorization: X-API-Key sk-agent-abc123...

Response:
{
  "id": 5,
  "name": "Shosanna 🔥",
  "role": "Backend Engineer",
  "project_id": 3
}
```

**Cabeceras requeridas** (futuro):
- Usuarios: `Authorization: Bearer <jwt_token>`
- Agentes: `X-API-Key: <api_key>`

---

## Rate Limiting

### Configuración Actual

| Entorno | Límite | Ventana | Implementado |
|---------|--------|---------|--------------|
| Local/Dev | Ilimitado | - | ✅ |
| Producción | 100 req/min | por IP | ⏳ Pendiente |

### Headers de Rate Limit (futuro)

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1678900000
```

Si excedes el límite:
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "retry_after": 45
}
```

---

## Códigos de Error

### Formato Estándar

```json
{
  "detail": "Human-readable error message"
}
```

### Status Codes

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| `200` | OK | Recurso obtenido exitosamente |
| `201` | Created | Recurso creado correctamente |
| `204` | No Content | Recurso eliminado (sin response body) |
| `400` | Bad Request | Validación falló o datos inválidos |
| `404` | Not Found | Recurso no existe |
| `409` | Conflict | Violación de unique constraint (slug, name) |
| `413` | Payload Too Large | Archivo > 500KB |
| `422` | Unprocessable Entity | Pydantic validation error |
| `500` | Internal Server Error | Error inesperado del servidor |

### Ejemplo de Error de Validación (422)

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {"min_length": 1}
    }
  ]
}
```

---

## Endpoints

### Prefijo Base

Todos los endpoints están bajo `/api/v1` excepto:
- `/health` (healthcheck)
- `/docs` (Swagger UI)
- `/redoc` (ReDoc)

### Resumen por Módulo

| Módulo | Tag | Endpoints | Descripción |
|--------|-----|-----------|-------------|
| **Projects** | `Projects` | 5 | CRUD de proyectos |
| **Agents** | `Agents` | 5 | CRUD de agentes AI |
| **Tasks** | `Tasks` | 7 | Gestión de tareas + kanban + bulk ops |
| **Epics** | `Epics` | 9 | Épicas + sub-tareas + reportes |
| **Dashboard** | `Dashboard` | 1 | Stats globales del sistema |
| **Communication** | `Communication` | 3 | Logs de comunicación entre agentes |
| **Files** | `Files` | 2 | Navegación de archivos del workspace |
| **Jira Sync** | `Jira Sync` | 1 | Sincronización con Jira |

---

### 📦 Projects

#### `GET /api/v1/projects`
Lista todos los proyectos.

**Query Params:**
- `status` (optional): Filtra por status (`active`, `archived`, `completed`)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Action Experience",
    "slug": "action-experience",
    "description": "Action Experience product",
    "team": "Luke, Yoda",
    "status": "active",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

---

#### `POST /api/v1/projects`
Crea un nuevo proyecto.

**Request Body:**
```json
{
  "name": "New Project",
  "slug": "new-project",
  "description": "Project description",
  "team": "Agent1, Agent2",
  "status": "active"
}
```

**Response:** `201 Created`
```json
{
  "id": 4,
  "name": "New Project",
  "slug": "new-project",
  "description": "Project description",
  "team": "Agent1, Agent2",
  "status": "active",
  "created_at": "2025-03-25T22:00:00Z"
}
```

---

#### `GET /api/v1/projects/{project_id}`
Obtiene un proyecto por ID.

**Path Params:**
- `project_id` (int): ID del proyecto

**Response:** `200 OK` | `404 Not Found`

---

#### `PATCH /api/v1/projects/{project_id}`
Actualiza parcialmente un proyecto.

**Request Body:**
```json
{
  "description": "Updated description",
  "status": "completed"
}
```

**Response:** `200 OK` | `404 Not Found`

---

#### `DELETE /api/v1/projects/{project_id}`
Elimina permanentemente un proyecto.

**Response:** `204 No Content` | `404 Not Found`

⚠️ **Warning:** Elimina en cascada todos los agentes, tareas y épicas relacionadas.

---

### 🤖 Agents

#### `GET /api/v1/agents`
Lista todos los agentes AI.

**Query Params:**
- `project_id` (optional): Filtra por proyecto

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Shosanna 🔥",
    "role": "Backend Engineer",
    "status": "active",
    "current_task": "Implementing auth system",
    "main_files": "main.py, routers/auth.py",
    "project_id": 3,
    "created_at": "2025-02-01T08:00:00Z"
  }
]
```

---

#### `POST /api/v1/agents`
Crea un nuevo agente AI.

**Request Body:**
```json
{
  "name": "NewAgent 🎯",
  "role": "QA Engineer",
  "status": "active",
  "current_task": "",
  "main_files": "",
  "project_id": 2
}
```

**Response:** `201 Created`

---

#### `PATCH /api/v1/agents/{agent_id}`
Actualiza estado de un agente.

**Request Body:**
```json
{
  "status": "working",
  "current_task": "Testing API endpoints"
}
```

**Response:** `200 OK` | `404 Not Found`

---

### ✅ Tasks

#### `GET /api/v1/tasks`
Lista tareas con filtros.

**Query Params:**
- `project_id` (optional): Filtra por proyecto
- `status` (optional): `backlog`, `in_progress`, `done`, `blocked`
- `assigned_to` (optional): Nombre del agente
- `include_old_done` (optional, default=false): Si false, excluye tareas `done` con >5 días

**Response:** `200 OK`
```json
[
  {
    "id": 42,
    "title": "Implement auth system",
    "description": "JWT + refresh tokens",
    "status": "in_progress",
    "priority": "high",
    "assigned_to": "Shosanna 🔥",
    "project_id": 3,
    "jira_key": "OPS-123",
    "created_at": "2025-03-20T10:00:00Z",
    "updated_at": "2025-03-25T15:30:00Z"
  }
]
```

---

#### `GET /api/v1/tasks/kanban/{project_id}`
Board de kanban agrupado por status.

**Response:** `200 OK`
```json
{
  "backlog": [...],
  "in_progress": [...],
  "done": [...],
  "blocked": [...]
}
```

---

#### `POST /api/v1/tasks`
Crea una nueva tarea.

**Request Body:**
```json
{
  "title": "Fix bug in auth",
  "description": "Token refresh not working",
  "status": "backlog",
  "priority": "high",
  "assigned_to": "Shosanna 🔥",
  "project_id": 3,
  "jira_key": null
}
```

**Response:** `201 Created`

---

#### `PATCH /api/v1/tasks/{task_id}/status`
Actualiza **solo el status** de una tarea (optimizado).

**Request Body:**
```json
{
  "status": "in_progress"
}
```

**Validación de Transiciones:**

| Desde → Hacia | Permitido |
|---------------|-----------|
| `backlog` → `in_progress`, `done`, `blocked` | ✅ |
| `in_progress` → `done`, `blocked`, `backlog` | ✅ |
| `done` → `backlog`, `in_progress` | ✅ |
| `blocked` → `backlog`, `in_progress` | ✅ |

**Response:** `200 OK` | `400 Bad Request` (si transición inválida)

---

#### `PATCH /api/v1/tasks/bulk-update`
Actualiza múltiples tareas a la vez.

**Request Body:**
```json
{
  "task_ids": [1, 2, 3, 4],
  "status": "done",
  "priority": null,
  "assigned_to": null
}
```

**Response:** `200 OK`
```json
{
  "updated_count": 3,
  "total_requested": 4,
  "errors": [
    {
      "task_id": 2,
      "error": "Invalid transition: done → done"
    }
  ]
}
```

---

### 🎯 Epics

#### `GET /api/v1/epics`
Lista épicas.

**Query Params:**
- `project_id` (optional)
- `status` (optional): `active`, `completed`, `blocked`

**Response:** `200 OK`
```json
[
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
]
```

---

#### `POST /api/v1/epics`
Crea una nueva épica.

**Request Body:**
```json
{
  "title": "New Feature",
  "description": "Feature description",
  "project_id": 3,
  "target_progress": 100.0,
  "status": "active"
}
```

**Response:** `201 Created`

---

#### `GET /api/v1/epics/{epic_id}/tasks`
Lista sub-tareas de una épica.

**Response:** `200 OK`
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

#### `POST /api/v1/epics/{epic_id}/tasks`
Crea una sub-tarea dentro de una épica.

**Request Body:**
```json
{
  "title": "Write tests",
  "progress": 0.0,
  "assigned_to": "Stiglitz 🎯",
  "status": "backlog"
}
```

**Response:** `201 Created`

⚙️ **Auto-trigger:** Recalcula automáticamente el `calculated_progress` de la épica.

---

#### `PATCH /api/v1/epic-tasks/{task_id}`
Actualiza una sub-tarea.

**Request Body:**
```json
{
  "progress": 100.0,
  "status": "done"
}
```

**Response:** `200 OK`

⚙️ **Auto-triggers:**
- Recalcula `calculated_progress` de la épica
- Guarda snapshot de progreso en historial

---

#### `GET /api/v1/projects/{project_id}/sprint-report`
Reporte completo de progreso del proyecto.

**Response:** `200 OK`
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
        }
      ]
    }
  ]
}
```

---

### 📊 Dashboard

#### `GET /api/v1/dashboard/stats`
Stats globales del sistema.

**Response:** `200 OK`
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
    }
  ]
}
```

---

### 💬 Communication

#### `GET /api/v1/comms`
Lista logs de comunicación entre agentes.

**Query Params:**
- `agent` (optional): Filtra por agente (from o to)
- `channel` (optional): Filtra por canal
- `limit` (default=50, max=200)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "from_agent": "Shosanna 🔥",
    "to_agent": "Marcel 🎬",
    "message": "API contract updated in Swagger",
    "channel": "slack",
    "timestamp": "2025-03-25T20:00:00Z"
  }
]
```

---

#### `POST /api/v1/comms`
Registra un log de comunicación.

**Request Body:**
```json
{
  "from_agent": "Shosanna 🔥",
  "to_agent": "Hans Landa 🎬",
  "message": "Backend deployed to production",
  "channel": "slack"
}
```

**Response:** `201 Created`

---

#### `GET /api/v1/comms/timeline`
Timeline de comunicaciones (últimas primero).

**Query Params:**
- `limit` (default=100, max=500)

**Response:** `200 OK`

---

### 📁 Files

#### `GET /api/v1/files/tree/{project_slug}`
Árbol de archivos de un proyecto.

**Path Params:**
- `project_slug`: Slug del proyecto (ej: `action-experience`)

**Query Params:**
- `depth` (default=3, min=1, max=6): Profundidad del árbol

**Response:** `200 OK`
```json
{
  "project": "action-experience",
  "root": "projects/action/experience",
  "tree": [
    {
      "name": "backend",
      "type": "directory",
      "path": "projects/action/experience/backend",
      "children": [
        {
          "name": "main.py",
          "type": "file",
          "path": "projects/action/experience/backend/main.py",
          "size": 3500
        }
      ]
    }
  ]
}
```

---

#### `GET /api/v1/files/read`
Lee el contenido de un archivo.

**Query Params:**
- `path` (required): Ruta relativa desde workspace root

**Response:** `200 OK`
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

### 🔄 Jira Sync

#### `POST /api/v1/jira/sync/{project_slug}`
Sincroniza tareas desde Jira.

**Path Params:**
- `project_slug`: Slug del proyecto

**Configuración requerida:**
- Archivo `.secrets/jira.env` o variables de entorno:
  ```bash
  JIRA_DOMAIN=your-domain.atlassian.net
  JIRA_EMAIL=your-email@example.com
  JIRA_API_TOKEN=your-api-token
  ```

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

**Response:** `200 OK`
```json
{
  "synced": 15,
  "project": "Operations"
}
```

**Comportamiento:**
- Si tarea ya existe (por `jira_key`), la actualiza
- Si es nueva, la crea
- Limita a 100 issues más recientes

---

## Healthcheck

#### `GET /health`
Verifica que el servidor está vivo.

**Response:** `200 OK`
```json
{
  "status": "ok"
}
```

---

## Notas Finales

### CORS

Los orígenes permitidos están hardcoded en `main.py`:
- `http://localhost:3000` (dev frontend)
- `https://operations-dashboard-nine.vercel.app` (prod frontend)

### Soft Deletes

Las épicas y sub-tareas usan **soft delete** (campo `deleted=True`).
- Los endpoints de lista las filtran automáticamente
- Se mantienen en la DB para auditoría

### Auto-Timestamps

- `created_at`: Se setea automáticamente al crear
- `updated_at`: Se actualiza automáticamente en cada PATCH

### Validaciones

- Unique constraints: `Project.slug`, `Project.name`, `Agent.name`
- Task status transitions: Validadas en `/tasks/{id}/status` y `/tasks/bulk-update`

---

**Última actualización:** 2025-03-25  
**Versión:** 1.0.0  
**Mantenido por:** Shosanna 🔥 & Padawan 👨‍💻
