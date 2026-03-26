# Operations Dashboard API 🔥

Backend centralizado de gestión de proyectos, agentes AI y tareas para el ecosistema Action Experience.

---

## 📋 Resumen

**Operations Dashboard** es el **source of truth único** para todos los proyectos del ecosistema Action (Action Experience, Action Colleague, Operations, etc.).

### Características

- 🔐 **Autenticación**: JWT tokens con roles (admin/leader/member) y bcrypt password hashing
- ✅ **Proyectos**: CRUD completo con estados y equipos
- 🤖 **Agentes AI**: Registro, tracking y autenticación vía API Keys
- ✅ **Tareas**: Sistema kanban con validación de transiciones y bulk operations
- 🎯 **Épicas**: Features complejas con sub-tareas y auto-cálculo de progreso
- 💬 **Comunicación**: Logs de interacciones entre agentes
- 🔄 **Jira Sync**: Sincronización automática con Jira
- 📁 **Files**: Explorador de estructura de proyectos

---

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone y setup
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Iniciar servidor
uvicorn main:app --reload --port 8000

# 3. Abrir Swagger UI
open http://localhost:8000/docs
```

### Producción

- **URL:** `https://ops-backend-production-e8ce.up.railway.app`
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **Health:** `/health`
- **Credenciales:** Ver `CREDENTIALS.md` para usuarios y passwords de prueba

---

## 📚 Documentación

### Para Desarrolladores

- **[API Reference](./docs/API_REFERENCE.md)**: Documentación completa de todos los endpoints
- **[Developer Guide](./docs/DEVELOPER_GUIDE.md)**: Setup local, estructura del proyecto, deploy
- **[Schemas](./docs/SCHEMAS.md)**: Modelos de datos, validaciones y relaciones
- **[Examples](./docs/EXAMPLES.md)**: Ejemplos de curl para todos los flujos

### Para Agentes AI

- **[Agent Integration Guide](./docs/AGENT_INTEGRATION.md)**: Guía completa para integrar agentes AI
  - Autenticación con API Keys
  - Flujos comunes (consultar tareas, actualizar status, subir transcripts)
  - Ejemplos de código (Python, JavaScript)
  - Rate limits y best practices
  - Troubleshooting

---

## 🛠️ Stack Tecnológico

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
  - Port: `6543` (pooler)

---

## 📊 Endpoints Principales

| Módulo | Endpoint | Descripción |
|--------|----------|-------------|
| **Projects** | `/api/v1/projects` | CRUD de proyectos |
| **Agents** | `/api/v1/agents` | CRUD de agentes AI |
| **Tasks** | `/api/v1/tasks` | Gestión de tareas + kanban |
| **Epics** | `/api/v1/epics` | Épicas + sub-tareas + reportes |
| **Dashboard** | `/api/v1/dashboard/stats` | Métricas globales |
| **Communication** | `/api/v1/comms` | Logs de comunicación |
| **Files** | `/api/v1/files` | Explorador de archivos |
| **Jira Sync** | `/api/v1/jira/sync/{slug}` | Sincronización con Jira |

Ver documentación completa en **[API_REFERENCE.md](./docs/API_REFERENCE.md)**.

---

## 🤖 Agent API - API para Agentes AI

API específica para que agentes AI autónomos consulten y actualicen sus tareas.

### Autenticación

Todos los endpoints de Agent API requieren header:

```bash
X-Agent-API-Key: <uuid>
```

### Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/agent-api/auth/register` | POST | Registrar agente y generar API key |
| `/api/v1/agent-api/auth/me` | GET | Info del agente autenticado |
| `/api/v1/agent-api/tasks/assigned` | GET | Tareas asignadas al agente |
| `/api/v1/agent-api/tasks/{id}/status` | PATCH | Actualizar status de tarea |
| `/api/v1/agent-api/projects` | GET | Lista de proyectos |
| `/api/v1/agent-api/epics/{id}/tasks` | GET | Sub-tareas de épica |

### Ejemplo de Uso

```python
import httpx

API_BASE = "https://ops-backend-production-e8ce.up.railway.app/api/v1"
API_KEY = "550e8400-e29b-41d4-a716-446655440000"

async def get_my_tasks():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/agent-api/tasks/assigned",
            headers={"X-Agent-API-Key": API_KEY},
            params={"status": "in_progress"}
        )
        response.raise_for_status()
        return response.json()

async def complete_task(task_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{API_BASE}/agent-api/tasks/{task_id}/status",
            headers={"X-Agent-API-Key": API_KEY},
            json={"status": "done"}
        )
        response.raise_for_status()
        return response.json()
```

Ver guía completa en **[AGENT_INTEGRATION.md](./docs/AGENT_INTEGRATION.md)**.

---

## 🔧 Deploy

### Railway (Producción Actual)

```bash
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend
railway up --detach
```

**Proceso:**
1. Railway detecta `Dockerfile`
2. Buildea imagen Docker
3. Deploya contenedor
4. URL: `https://ops-backend-production-e8ce.up.railway.app`

### Variables de Entorno

```bash
# Ver variables actuales
railway variables

# Setear nueva variable
railway variables set NUEVA_VAR="valor"
```

**Variables configuradas:**
- `DATABASE_URL`: PostgreSQL de Supabase
- `JIRA_DOMAIN`, `JIRA_EMAIL`, `JIRA_API_TOKEN`: Credenciales de Jira
- `WORKSPACE_ROOT`: Path del workspace

### Ver Logs

```bash
railway logs
```

Ver más detalles en **[DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md#deploy)**.

---

## 📁 Estructura del Proyecto

```
backend/
├── main.py              # FastAPI app + lifespan + CORS
├── database.py          # Engine + SessionLocal
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic schemas
├── requirements.txt     # Dependencies
├── .env                 # Environment variables (local)
├── Dockerfile           # Docker image
│
├── routers/
│   ├── projects.py      # Projects CRUD
│   ├── agents.py        # Agents CRUD
│   ├── tasks.py         # Tasks + kanban + bulk ops
│   ├── epics.py         # Epics + sub-tasks + reports
│   ├── dashboard.py     # Global stats
│   ├── comms.py         # Communication logs
│   ├── files.py         # File tree + read
│   └── jira_sync.py     # Jira sync
│
└── docs/
    ├── API_REFERENCE.md
    ├── AGENT_INTEGRATION.md
    ├── DEVELOPER_GUIDE.md
    ├── SCHEMAS.md
    └── EXAMPLES.md
```

---

## 🎯 Ejemplos de Uso

### Crear Proyecto

```bash
curl -X POST "https://ops-backend-production-e8ce.up.railway.app/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Project",
    "slug": "new-project",
    "description": "A new project",
    "team": "Team Alpha",
    "status": "active"
  }'
```

### Consultar Tareas en Progreso

```bash
curl "https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks?status=in_progress"
```

### Actualizar Status de Tarea

```bash
curl -X PATCH "https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks/42/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

### Obtener Sprint Report

```bash
curl "https://ops-backend-production-e8ce.up.railway.app/api/v1/projects/3/sprint-report"
```

Ver más ejemplos en **[EXAMPLES.md](./docs/EXAMPLES.md)**.

---

## 🔐 Autenticación

### Estado Actual

**Pendiente implementación.** Por ahora todos los endpoints son públicos (se asume red privada o VPN).

### Implementación Futura

- **Usuarios humanos**: OAuth/JWT
- **Agentes AI**: API Keys (parcialmente implementado, ver Agent API)

Ver detalles en **[API_REFERENCE.md](./docs/API_REFERENCE.md#autenticación)**.

---

## ⚡ Rate Limiting

### Configuración Actual

- **Local/Dev**: Ilimitado
- **Producción**: Ilimitado (pendiente implementar)

### Implementación Futura

- **General**: 100 req/min por IP
- **Agent API**: 60 req/min por API key

---

## 🧪 Testing

### Manual con curl

```bash
# Health check
curl https://ops-backend-production-e8ce.up.railway.app/health

# List projects
curl https://ops-backend-production-e8ce.up.railway.app/api/v1/projects

# Create task
curl -X POST https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","description":"","status":"backlog","priority":"medium","assigned_to":"Shosanna 🔥","project_id":1}'
```

### Con Pytest (futuro)

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## 🐛 Troubleshooting

### Problema: CORS Error

**Solución:** Agrega tu origen a `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://operations-dashboard-nine.vercel.app",
        "https://tu-frontend.vercel.app"  # Agregar acá
    ],
    ...
)
```

### Problema: Database Locked (SQLite)

**Solución:**
```bash
pkill -f uvicorn
rm operations.db
python main.py
```

### Problema: Railway Deploy Falla

**Solución:**
1. Revisa logs: `railway logs`
2. Verifica `Dockerfile` y `requirements.txt`
3. Rebuild: `railway up --detach`

Ver más en **[DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md#troubleshooting)**.

---

## 👥 Contribuyendo

### Workflow

1. Crea rama feature: `git checkout -b feature/nueva-funcionalidad`
2. Desarrolla y testea localmente
3. Commit: `git commit -m "feat: implementa nueva funcionalidad"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Deploy a Railway (auto-deploy en push a main)

### Convenciones

- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- **Branches**: `feature/`, `fix/`, `docs/`
- **Code style**: Black + isort (futuro)

---

## 🎬 Créditos

- **Shosanna 🔥**: Backend Engineer — API, routers, schemas, deploy
- **Hans Landa 🎬**: QA Lead — Testing, validation, integration
- **Marcel 🎬**: Frontend Engineer — Frontend integration, UI/UX
- **Padawan (Esteban Lozada) 👨‍💻**: Tech Lead — Arquitectura, deployment, mentoring

---

## 📝 Licencia

MIT License

---

## 🔗 Links

- **Producción**: [ops-backend-production-e8ce.up.railway.app](https://ops-backend-production-e8ce.up.railway.app)
- **Swagger UI**: [/docs](https://ops-backend-production-e8ce.up.railway.app/docs)
- **ReDoc**: [/redoc](https://ops-backend-production-e8ce.up.railway.app/redoc)
- **Frontend**: [operations-dashboard-nine.vercel.app](https://operations-dashboard-nine.vercel.app)

---

**Operations Dashboard** — El source of truth de todos los proyectos 🔥

**Última actualización:** 2025-03-25  
**Versión:** 1.0.0
