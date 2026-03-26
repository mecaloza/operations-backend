# API de Seguimiento de Sprints

## Descripción

Módulo para trackear el % de avance de épicas y sub-tareas por proyecto en Operations Dashboard.

Inspirado en el formato de reporte de Yoda para Action Experience.

## Características

- ✅ Épicas con meta objetivo y % auto-calculado
- ✅ Sub-tareas con % de completitud (0-100)
- ✅ Cálculo automático de % de épica (promedio de sub-tareas)
- ✅ Cálculo automático de % total del proyecto (promedio de épicas)
- ✅ Soft delete (épicas y sub-tareas)
- ✅ Historial de progreso para graficar tendencias
- ✅ Multi-proyecto (Action Experience, Operations, Action Colleague, Newton)

---

## Modelos

### Epic (Épica)

```python
{
  "id": 1,
  "title": "Ventas de membresías",
  "description": "Módulo completo de ventas",
  "project_id": 1,
  "target_progress": 90.0,           # Meta objetivo (%)
  "calculated_progress": 70.0,       # Auto-calculado desde sub-tareas
  "status": "active",                # active | completed | blocked
  "created_at": "2026-03-26T03:08:00.838159",
  "updated_at": "2026-03-26T03:08:20.956919"
}
```

### EpicTask (Sub-tarea)

```python
{
  "id": 1,
  "title": "Diseño",
  "epic_id": 1,
  "progress": 100.0,                 # % completitud (0-100)
  "assigned_to": "Anna",             # Agente o humano
  "status": "done",                  # backlog | in_progress | done | qa
  "created_at": "2026-03-26T03:08:05.621024",
  "updated_at": "2026-03-26T03:08:05.621030"
}
```

### EpicProgressHistory (Historial)

```python
{
  "id": 1,
  "epic_id": 1,
  "progress": 75.0,                  # Snapshot de % en ese momento
  "snapshot_date": "2026-03-26T03:08:00.838159"
}
```

---

## Endpoints

### **Épicas**

#### `GET /api/v1/epics`
Lista épicas con filtros opcionales.

**Query Params:**
- `project_id` (int, opcional) - Filtrar por proyecto
- `status` (str, opcional) - Filtrar por estado (active, completed, blocked)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Ventas de membresías",
    "description": "Módulo completo de ventas",
    "project_id": 1,
    "target_progress": 90.0,
    "calculated_progress": 70.0,
    "status": "active",
    "created_at": "2026-03-26T03:08:00.838159",
    "updated_at": "2026-03-26T03:08:20.956919"
  }
]
```

---

#### `POST /api/v1/epics`
Crea una nueva épica.

**Body:**
```json
{
  "title": "Ventas de membresías",
  "description": "Módulo completo de ventas",
  "project_id": 1,
  "target_progress": 90.0,
  "status": "active"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "Ventas de membresías",
  "description": "Módulo completo de ventas",
  "project_id": 1,
  "target_progress": 90.0,
  "calculated_progress": 0.0,
  "status": "active",
  "created_at": "2026-03-26T03:08:00.838159",
  "updated_at": "2026-03-26T03:08:00.838165"
}
```

---

#### `GET /api/v1/epics/{epic_id}`
Obtiene una épica por ID.

**Response:** `200 OK` o `404 Not Found`

---

#### `PATCH /api/v1/epics/{epic_id}`
Actualiza una épica.

**Body:**
```json
{
  "title": "Nuevo título",
  "description": "Nueva descripción",
  "target_progress": 95.0,
  "status": "completed"
}
```

**Response:** `200 OK` o `404 Not Found`

---

#### `DELETE /api/v1/epics/{epic_id}`
Soft delete de una épica.

**Response:** `204 No Content` o `404 Not Found`

---

### **Sub-tareas**

#### `GET /api/v1/epics/{epic_id}/tasks`
Lista todas las sub-tareas de una épica.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Diseño",
    "epic_id": 1,
    "progress": 100.0,
    "assigned_to": "Anna",
    "status": "done",
    "created_at": "2026-03-26T03:08:05.621024",
    "updated_at": "2026-03-26T03:08:05.621030"
  }
]
```

---

#### `POST /api/v1/epics/{epic_id}/tasks`
Crea una sub-tarea dentro de una épica.

**Body:**
```json
{
  "title": "Diseño",
  "progress": 100.0,
  "assigned_to": "Anna",
  "status": "done"
}
```

**Response:** `201 Created`

**Nota:** Al crear una sub-tarea, el `calculated_progress` de la épica se recalcula automáticamente.

---

#### `PATCH /api/v1/epic-tasks/{task_id}`
Actualiza una sub-tarea (%, estado, asignado).

**Body:**
```json
{
  "progress": 80.0,
  "assigned_to": "Victor",
  "status": "in_progress"
}
```

**Response:** `200 OK` o `404 Not Found`

**Nota:** Al actualizar una sub-tarea:
1. El `calculated_progress` de la épica se recalcula automáticamente
2. Se guarda un snapshot en `epic_progress_history`

---

#### `DELETE /api/v1/epic-tasks/{task_id}`
Soft delete de una sub-tarea.

**Response:** `204 No Content` o `404 Not Found`

**Nota:** Al eliminar una sub-tarea, el `calculated_progress` de la épica se recalcula automáticamente.

---

### **Reportes**

#### `GET /api/v1/projects/{project_id}/sprint-report`
Reporte completo de avance: épicas + sub-tareas + % total.

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "project_name": "Action Experience",
  "total_progress": 77.5,
  "epics": [
    {
      "id": 1,
      "title": "Ventas de membresías",
      "progress": 70.0,
      "target_progress": 90.0,
      "status": "active",
      "tasks": [
        {
          "title": "Diseño",
          "progress": 100.0,
          "assigned_to": "Anna",
          "status": "done"
        },
        {
          "title": "Crud BE",
          "progress": 100.0,
          "assigned_to": "Victor",
          "status": "done"
        },
        {
          "title": "Admin",
          "progress": 30.0,
          "assigned_to": "Sin asignar",
          "status": "in_progress"
        },
        {
          "title": "QA",
          "progress": 50.0,
          "assigned_to": "Hans",
          "status": "qa"
        }
      ]
    },
    {
      "id": 2,
      "title": "Sistema de pagos",
      "progress": 85.0,
      "target_progress": 100.0,
      "status": "active",
      "tasks": [
        {
          "title": "Integración Stripe",
          "progress": 90.0,
          "assigned_to": "Victor",
          "status": "qa"
        },
        {
          "title": "Testing pagos",
          "progress": 80.0,
          "assigned_to": "Hans",
          "status": "in_progress"
        }
      ]
    }
  ]
}
```

---

## Cálculos Automáticos

### % Avance de Épica
```python
calculated_progress = sum(task.progress for task in tasks) / len(tasks)
```

**Ejemplo:**
- Diseño: 100%
- Crud BE: 100%
- Admin: 30%
- QA: 50%

→ `(100 + 100 + 30 + 50) / 4 = 70%`

### % Avance Total del Proyecto
```python
total_progress = sum(epic.calculated_progress for epic in epics) / len(epics)
```

**Ejemplo:**
- Epic 1: 70%
- Epic 2: 85%

→ `(70 + 85) / 2 = 77.5%`

---

## Flujo de Trabajo Típico

1. **Crear épica para un proyecto:**
   ```bash
   POST /api/v1/epics
   {
     "title": "Módulo de ventas",
     "project_id": 1,
     "target_progress": 90.0
   }
   ```

2. **Añadir sub-tareas:**
   ```bash
   POST /api/v1/epics/1/tasks
   {
     "title": "Diseño UI",
     "progress": 0,
     "assigned_to": "Anna",
     "status": "backlog"
   }
   ```

3. **Actualizar progreso de sub-tarea:**
   ```bash
   PATCH /api/v1/epic-tasks/1
   {
     "progress": 50.0,
     "status": "in_progress"
   }
   ```
   → La épica se recalcula automáticamente.

4. **Ver reporte completo:**
   ```bash
   GET /api/v1/projects/1/sprint-report
   ```

---

## Formato Inspirado (Yoda)

Este módulo replica el formato de reporte de Yoda:

```
REPORTE DE AVANCE - ÉPICAS DEL PROYECTO
AVANCE TOTAL: 80% ↑25%

EPIC 1: Ventas de membresías
 Avance: 35.71% | Meta: 90%
 Diseño: 100% → Anna
 Crud BE: 100% → Victor
 Admin: 30% → Sin asignar
 QA: 50%
```

Ahora está disponible vía API para el frontend del Operations Dashboard.

---

## Deploy

**Producción:** Railway  
**Base de datos:** Supabase PostgreSQL  
**URL:** `https://ops-backend-production-e8ce.up.railway.app`

---

## Docs Interactivas

FastAPI genera documentación automática:

- **Swagger UI:** `https://ops-backend-production-e8ce.up.railway.app/docs`
- **ReDoc:** `https://ops-backend-production-e8ce.up.railway.app/redoc`
