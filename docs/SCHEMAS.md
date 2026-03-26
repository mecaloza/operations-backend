# Data Schemas 📊

Documentación completa de todos los modelos de datos de Operations Dashboard API.

---

## 📋 Tabla de Contenidos

- [Resumen](#resumen)
- [Project](#project)
- [Agent](#agent)
- [Task](#task)
- [Epic](#epic)
- [EpicTask](#epictask)
- [CommunicationLog](#communicationlog)
- [Enums](#enums)
- [Relaciones](#relaciones)

---

## Resumen

| Entidad | Descripción | Endpoints |
|---------|-------------|-----------|
| **Project** | Proyectos del ecosistema | `/api/v1/projects` |
| **Agent** | Agentes AI registrados | `/api/v1/agents` |
| **Task** | Tareas regulares (kanban) | `/api/v1/tasks` |
| **Epic** | Features complejas con sub-tareas | `/api/v1/epics` |
| **EpicTask** | Sub-tareas de épicas | `/api/v1/epic-tasks` |
| **CommunicationLog** | Logs de comunicación | `/api/v1/comms` |

---

## Project

### Descripción
Representa un proyecto dentro del ecosistema Action (Action Experience, Action Colleague, Operations, etc.).

### Database Model

```python
class Project(Base):
    __tablename__ = "projects"
    
    id: int                # Primary key
    name: str              # Nombre del proyecto (unique)
    slug: str              # Identificador URL-friendly (unique)
    description: str       # Descripción del proyecto
    team: str              # Miembros del equipo (comma-separated)
    status: str            # Estado: active, archived, completed
    created_at: datetime   # Timestamp de creación
```

### Pydantic Schemas

#### ProjectBase
```json
{
  "name": "string (required)",
  "slug": "string (required)",
  "description": "string (default: '')",
  "team": "string (default: '')",
  "status": "string (default: 'active')"
}
```

#### ProjectCreate (hereda ProjectBase)
```json
{
  "name": "Action Experience",
  "slug": "action-experience",
  "description": "Action Experience product",
  "team": "Luke ⚔️, Yoda 🧙",
  "status": "active"
}
```

#### ProjectUpdate
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "team": "string (optional)",
  "status": "string (optional)"
}
```

**Ejemplo:**
```json
{
  "description": "Updated project description",
  "status": "completed"
}
```

#### ProjectOut (response)
```json
{
  "id": 1,
  "name": "Action Experience",
  "slug": "action-experience",
  "description": "Action Experience product",
  "team": "Luke ⚔️, Yoda 🧙",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Validaciones

- `name`: Debe ser único
- `slug`: Debe ser único, se usa para paths de filesystem y URLs
- `status`: Valores comunes: `active`, `archived`, `completed`

### Relaciones

- `1:N` con **Agent** (un proyecto tiene muchos agentes)
- `1:N` con **Task** (un proyecto tiene muchas tareas)
- `1:N` con **Epic** (un proyecto tiene muchas épicas)

---

## Agent

### Descripción
Representa un agente AI autónomo que trabaja en proyectos.

### Database Model

```python
class Agent(Base):
    __tablename__ = "agents"
    
    id: int                # Primary key
    name: str              # Nombre del agente (unique)
    role: str              # Rol: Backend Engineer, QA Lead, etc.
    status: str            # Estado: active, idle, working
    current_task: str      # Descripción de tarea actual
    main_files: str        # Archivos principales que maneja
    project_id: int | None # Foreign key → Project (nullable)
    created_at: datetime   # Timestamp de creación
```

### Pydantic Schemas

#### AgentBase
```json
{
  "name": "string (required)",
  "role": "string (default: '')",
  "status": "string (default: 'active')",
  "current_task": "string (default: '')",
  "main_files": "string (default: '')",
  "project_id": "int | null (optional)"
}
```

#### AgentCreate (hereda AgentBase)
```json
{
  "name": "Shosanna 🔥",
  "role": "Backend Engineer",
  "status": "active",
  "current_task": "Implementing auth system",
  "main_files": "main.py, routers/auth.py",
  "project_id": 3
}
```

#### AgentUpdate
```json
{
  "name": "string (optional)",
  "role": "string (optional)",
  "status": "string (optional)",
  "current_task": "string (optional)",
  "main_files": "string (optional)",
  "project_id": "int | null (optional)"
}
```

**Ejemplo:**
```json
{
  "status": "working",
  "current_task": "Writing API documentation"
}
```

#### AgentOut (response)
```json
{
  "id": 7,
  "name": "Shosanna 🔥",
  "role": "Backend Engineer",
  "status": "working",
  "current_task": "Writing API documentation",
  "main_files": "main.py, schemas.py, routers/",
  "project_id": 3,
  "created_at": "2025-02-01T08:00:00Z"
}
```

### Validaciones

- `name`: Debe ser único
- `status`: Valores del enum `AgentStatus`: `active`, `idle`, `working`

### Relaciones

- `N:1` con **Project** (muchos agentes pertenecen a un proyecto)

---

## Task

### Descripción
Tareas regulares del sistema (no confundir con sub-tareas de épicas).

### Database Model

```python
class Task(Base):
    __tablename__ = "tasks"
    
    id: int                # Primary key
    title: str             # Título de la tarea
    description: str       # Descripción/transcript
    status: str            # backlog, in_progress, done, blocked
    priority: str          # low, medium, high, critical
    assigned_to: str       # Nombre del agente o humano
    project_id: int        # Foreign key → Project (required)
    jira_key: str | None   # Key de Jira (ej: OPS-123), nullable
    created_at: datetime   # Timestamp de creación
    updated_at: datetime   # Auto-updated en cada cambio
```

### Pydantic Schemas

#### TaskBase
```json
{
  "title": "string (required)",
  "description": "string (default: '')",
  "status": "string (default: 'backlog')",
  "priority": "string (default: 'medium')",
  "assigned_to": "string (default: '')",
  "project_id": "int (required)",
  "jira_key": "string | null (optional)"
}
```

#### TaskCreate (hereda TaskBase)
```json
{
  "title": "Implement JWT authentication",
  "description": "Add JWT tokens with refresh mechanism",
  "status": "backlog",
  "priority": "high",
  "assigned_to": "Shosanna 🔥",
  "project_id": 3,
  "jira_key": "OPS-123"
}
```

#### TaskUpdate
```json
{
  "title": "string (optional)",
  "description": "string (optional)",
  "status": "string (optional)",
  "priority": "string (optional)",
  "assigned_to": "string (optional)",
  "jira_key": "string | null (optional)"
}
```

**Ejemplo:**
```json
{
  "status": "in_progress",
  "description": "Started implementing token generation"
}
```

#### TaskStatusUpdate (optimizado)
```json
{
  "status": "string (required)"
}
```

**Ejemplo:**
```json
{
  "status": "done"
}
```

#### BulkTaskUpdate
```json
{
  "task_ids": [1, 2, 3, 4],
  "status": "string (optional)",
  "priority": "string (optional)",
  "assigned_to": "string (optional)"
}
```

**Ejemplo:**
```json
{
  "task_ids": [10, 11, 12],
  "status": "done",
  "assigned_to": null
}
```

#### TaskOut (response)
```json
{
  "id": 42,
  "title": "Implement JWT authentication",
  "description": "Add JWT tokens with refresh mechanism",
  "status": "in_progress",
  "priority": "high",
  "assigned_to": "Shosanna 🔥",
  "project_id": 3,
  "jira_key": "OPS-123",
  "created_at": "2025-03-20T10:00:00Z",
  "updated_at": "2025-03-25T15:30:00Z"
}
```

### Validaciones

- `status`: Debe ser uno de: `backlog`, `in_progress`, `done`, `blocked`
- `priority`: Debe ser uno de: `low`, `medium`, `high`, `critical`
- Transiciones de status: Ver tabla en [API_REFERENCE.md](./API_REFERENCE.md#patch-apiv1taskstask_idstatus)

### Relaciones

- `N:1` con **Project** (muchas tareas pertenecen a un proyecto)

### Comportamientos Especiales

- `updated_at`: Se actualiza automáticamente en cada PATCH
- **Auto-filtrado**: `GET /tasks?include_old_done=false` excluye tareas `done` con >5 días

---

## Epic

### Descripción
Features complejas que contienen sub-tareas. El progreso se calcula automáticamente.

### Database Model

```python
class Epic(Base):
    __tablename__ = "epics"
    
    id: int                       # Primary key
    title: str                    # Título de la épica
    description: str              # Descripción del feature
    project_id: int               # Foreign key → Project (required)
    target_progress: float        # Meta objetivo (% target, default: 100.0)
    calculated_progress: float    # Auto-calculado desde sub-tareas
    status: str                   # active, completed, blocked
    deleted: bool                 # Soft delete (default: False)
    created_at: datetime          # Timestamp de creación
    updated_at: datetime          # Auto-updated
```

### Pydantic Schemas

#### EpicBase
```json
{
  "title": "string (required)",
  "description": "string (default: '')",
  "project_id": "int (required)",
  "target_progress": "float (default: 100.0)",
  "status": "string (default: 'active')"
}
```

#### EpicCreate (hereda EpicBase)
```json
{
  "title": "Authentication System",
  "description": "Complete auth with JWT + refresh tokens",
  "project_id": 3,
  "target_progress": 100.0,
  "status": "active"
}
```

#### EpicUpdate
```json
{
  "title": "string (optional)",
  "description": "string (optional)",
  "target_progress": "float (optional)",
  "status": "string (optional)"
}
```

**Ejemplo:**
```json
{
  "status": "completed",
  "target_progress": 100.0
}
```

#### EpicOut (response)
```json
{
  "id": 1,
  "title": "Authentication System",
  "description": "Complete auth with JWT + refresh tokens",
  "project_id": 3,
  "target_progress": 100.0,
  "calculated_progress": 65.5,
  "status": "active",
  "created_at": "2025-03-01T00:00:00Z",
  "updated_at": "2025-03-25T20:00:00Z"
}
```

### Validaciones

- `status`: `active`, `completed`, `blocked`
- `target_progress`: Típicamente 100.0, pero puede variar
- `calculated_progress`: **Read-only**, auto-calculado

### Relaciones

- `N:1` con **Project**
- `1:N` con **EpicTask** (cascade delete)
- `1:N` con **EpicProgressHistory**

### Comportamientos Especiales

- **Auto-cálculo de progreso**: Al crear/actualizar/eliminar sub-tareas, se recalcula `calculated_progress`
- **Soft delete**: No se borra físicamente, solo se marca `deleted=True`
- **Historial**: Cada update de sub-tarea guarda un snapshot en `EpicProgressHistory`

---

## EpicTask

### Descripción
Sub-tareas de una épica. Su progreso individual afecta el progreso total de la épica.

### Database Model

```python
class EpicTask(Base):
    __tablename__ = "epic_tasks"
    
    id: int                # Primary key
    title: str             # Título de la sub-tarea
    epic_id: int           # Foreign key → Epic (required)
    progress: float        # % completitud (0.0-100.0)
    assigned_to: str       # Agente o humano asignado
    status: str            # backlog, in_progress, done, qa
    deleted: bool          # Soft delete (default: False)
    created_at: datetime   # Timestamp de creación
    updated_at: datetime   # Auto-updated
```

### Pydantic Schemas

#### EpicTaskBase
```json
{
  "title": "string (required)",
  "progress": "float (default: 0.0)",
  "assigned_to": "string (default: 'Sin asignar')",
  "status": "string (default: 'backlog')"
}
```

#### EpicTaskCreate (hereda EpicTaskBase)
```json
{
  "title": "Backend API implementation",
  "progress": 0.0,
  "assigned_to": "Shosanna 🔥",
  "status": "backlog"
}
```

#### EpicTaskUpdate
```json
{
  "title": "string (optional)",
  "progress": "float (optional)",
  "assigned_to": "string (optional)",
  "status": "string (optional)"
}
```

**Ejemplo:**
```json
{
  "progress": 80.0,
  "status": "in_progress"
}
```

#### EpicTaskOut (response)
```json
{
  "id": 1,
  "title": "Backend API implementation",
  "epic_id": 1,
  "progress": 80.0,
  "assigned_to": "Shosanna 🔥",
  "status": "in_progress",
  "created_at": "2025-03-10T00:00:00Z",
  "updated_at": "2025-03-25T18:00:00Z"
}
```

### Validaciones

- `progress`: 0.0 - 100.0
- `status`: `backlog`, `in_progress`, `done`, `qa`

### Relaciones

- `N:1` con **Epic** (muchas sub-tareas pertenecen a una épica)

### Comportamientos Especiales

- **Auto-recálculo**: Al crear/actualizar/eliminar, recalcula `Epic.calculated_progress`
- **Snapshot**: Cada update guarda un registro en `EpicProgressHistory`
- **Soft delete**: No se borra físicamente

---

## CommunicationLog

### Descripción
Registros de comunicación entre agentes o entre agentes y humanos.

### Database Model

```python
class CommunicationLog(Base):
    __tablename__ = "communication_logs"
    
    id: int              # Primary key
    from_agent: str      # Nombre del agente que envía
    to_agent: str        # Nombre del agente que recibe
    message: str         # Contenido del mensaje
    channel: str         # Canal: direct, slack, telegram, etc.
    timestamp: datetime  # Timestamp de creación
```

### Pydantic Schemas

#### CommLogBase
```json
{
  "from_agent": "string (required)",
  "to_agent": "string (required)",
  "message": "string (required)",
  "channel": "string (default: 'direct')"
}
```

#### CommLogCreate (hereda CommLogBase)
```json
{
  "from_agent": "Shosanna 🔥",
  "to_agent": "Marcel 🎬",
  "message": "API contract updated. Check Swagger docs.",
  "channel": "slack"
}
```

#### CommLogOut (response)
```json
{
  "id": 1,
  "from_agent": "Shosanna 🔥",
  "to_agent": "Marcel 🎬",
  "message": "API contract updated. Check Swagger docs.",
  "channel": "slack",
  "timestamp": "2025-03-25T20:00:00Z"
}
```

### Validaciones

- `message`: No puede estar vacío
- `channel`: Valores comunes: `direct`, `slack`, `telegram`, `webhook`

---

## Sprint Report

### Descripción
Reporte consolidado de progreso de un proyecto con todas sus épicas y sub-tareas.

### Pydantic Schemas

#### SprintEpicTask
```json
{
  "title": "string",
  "progress": "float",
  "assigned_to": "string",
  "status": "string"
}
```

#### SprintEpic
```json
{
  "id": "int",
  "title": "string",
  "progress": "float",
  "target_progress": "float",
  "status": "string",
  "tasks": ["array of SprintEpicTask"]
}
```

#### SprintReport
```json
{
  "project_id": "int",
  "project_name": "string",
  "total_progress": "float",
  "epics": ["array of SprintEpic"]
}
```

**Ejemplo completo:**
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

## Enums

### TaskStatus
```python
class TaskStatus(str, enum.Enum):
    backlog = "backlog"
    in_progress = "in_progress"
    done = "done"
    blocked = "blocked"
```

### Priority
```python
class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
```

### AgentStatus
```python
class AgentStatus(str, enum.Enum):
    active = "active"
    idle = "idle"
    working = "working"
```

### EpicStatus
```python
class EpicStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    blocked = "blocked"
```

### EpicTaskStatus
```python
class EpicTaskStatus(str, enum.Enum):
    backlog = "backlog"
    in_progress = "in_progress"
    done = "done"
    qa = "qa"
```

---

## Relaciones

### Diagrama ERD

```
Project
├── 1:N → Agent
├── 1:N → Task
└── 1:N → Epic
            └── 1:N → EpicTask
            └── 1:N → EpicProgressHistory

(CommunicationLog es independiente)
```

### Cascade Deletes

- **Project → Task**: CASCADE (eliminar proyecto elimina sus tareas)
- **Project → Epic**: CASCADE (eliminar proyecto elimina sus épicas)
- **Epic → EpicTask**: CASCADE (eliminar épica elimina sus sub-tareas)
- **Epic → EpicProgressHistory**: CASCADE

### Soft Deletes

- **Epic**: `deleted=True` (no se borra físicamente)
- **EpicTask**: `deleted=True` (no se borra físicamente)

Los endpoints de lista filtran automáticamente los registros con `deleted=True`.

---

## Validaciones Cross-Field

### Task Status Transitions

Ver tabla completa en [API_REFERENCE.md](./API_REFERENCE.md#patch-apiv1taskstask_idstatus).

**Ejemplo de validación:**
```python
# Tarea actualmente en "done"
# Intentas moverla a "blocked"
# Error: "Invalid status transition: done → blocked"
```

### Epic Progress Calculation

```python
# Épica con 3 sub-tareas:
# - Tarea 1: 100%
# - Tarea 2: 80%
# - Tarea 3: 50%

calculated_progress = (100 + 80 + 50) / 3 = 76.67%
```

---

## Campos Auto-Generados

| Campo | Modelo | Cuándo | Valor |
|-------|--------|--------|-------|
| `id` | Todos | CREATE | Auto-increment |
| `created_at` | Todos | CREATE | `datetime.now(timezone.utc)` |
| `updated_at` | Task, Epic, EpicTask | CREATE/UPDATE | `datetime.now(timezone.utc)` |
| `calculated_progress` | Epic | CREATE/UPDATE sub-task | Promedio de `EpicTask.progress` |
| `deleted` | Epic, EpicTask | CREATE | `False` |

---

## Ejemplos de JSON Completos

### Crear Proyecto con Agente y Tarea

```bash
# 1. Crear proyecto
POST /api/v1/projects
{
  "name": "New Product",
  "slug": "new-product",
  "description": "Revolutionary product",
  "team": "Team Alpha",
  "status": "active"
}
# Response: {"id": 4, ...}

# 2. Crear agente
POST /api/v1/agents
{
  "name": "NewAgent 🚀",
  "role": "Full Stack",
  "status": "active",
  "project_id": 4
}
# Response: {"id": 10, ...}

# 3. Crear tarea
POST /api/v1/tasks
{
  "title": "Setup project structure",
  "description": "Initialize repo and dependencies",
  "status": "backlog",
  "priority": "high",
  "assigned_to": "NewAgent 🚀",
  "project_id": 4
}
# Response: {"id": 100, ...}
```

### Crear Épica con Sub-Tareas

```bash
# 1. Crear épica
POST /api/v1/epics
{
  "title": "User Management",
  "description": "Complete user CRUD + auth",
  "project_id": 3,
  "target_progress": 100.0,
  "status": "active"
}
# Response: {"id": 5, "calculated_progress": 0.0, ...}

# 2. Crear sub-tarea 1
POST /api/v1/epics/5/tasks
{
  "title": "User model + DB",
  "progress": 0.0,
  "assigned_to": "Shosanna 🔥",
  "status": "backlog"
}
# Response: {"id": 20, "epic_id": 5, ...}
# Epic.calculated_progress ahora es 0.0

# 3. Crear sub-tarea 2
POST /api/v1/epics/5/tasks
{
  "title": "API endpoints",
  "progress": 0.0,
  "assigned_to": "Shosanna 🔥",
  "status": "backlog"
}
# Epic.calculated_progress sigue en 0.0

# 4. Actualizar progreso de sub-tarea 1
PATCH /api/v1/epic-tasks/20
{
  "progress": 100.0,
  "status": "done"
}
# Epic.calculated_progress ahora es 50.0 (promedio de 100 y 0)

# 5. Actualizar progreso de sub-tarea 2
PATCH /api/v1/epic-tasks/21
{
  "progress": 80.0,
  "status": "in_progress"
}
# Epic.calculated_progress ahora es 90.0 (promedio de 100 y 80)
```

---

**Última actualización:** 2025-03-25  
**Versión:** 1.0.0  
**Mantenido por:** Shosanna 🔥 & Padawan 👨‍💻
