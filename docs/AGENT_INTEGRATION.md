# Agent Integration Guide 🤖

Guía completa para integrar agentes AI con Operations Dashboard.

---

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [Quick Start](#quick-start)
- [Autenticación](#autenticación)
- [Flujos Comunes](#flujos-comunes)
- [Ejemplos de Código](#ejemplos-de-código)
- [Rate Limits](#rate-limits)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Introducción

Operations Dashboard permite que agentes AI autónomos:
- 📊 Consulten sus tareas asignadas
- ✅ Actualicen el status de tareas
- 📝 Suban transcripts de ejecución
- 💬 Registren comunicaciones con otros agentes
- 🎯 Reporten progreso en épicas

---

## Quick Start

### 1. Obtener API Key

**Estado actual:** Autenticación no implementada. Todos los endpoints son públicos.

**Implementación futura:**
```bash
# Request
POST /api/v1/agents/generate-key
Content-Type: application/json

{
  "agent_name": "Shosanna 🔥",
  "admin_password": "your_admin_password"
}

# Response
{
  "api_key": "sk-agent-abc123def456...",
  "expires_at": "2026-03-25T00:00:00Z"
}
```

### 2. Test Connection

```bash
curl https://ops-backend-production-e8ce.up.railway.app/health
# {"status":"ok"}
```

### 3. Consultar Tareas Asignadas

```bash
curl "https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks?assigned_to=Shosanna%20%F0%9F%94%A5"
```

---

## Autenticación

### Estado Actual: Público

Por ahora **NO se requiere autenticación**. Se asume que el backend está en una red privada o detrás de VPN.

### Implementación Futura: API Keys

Cuando se implemente autenticación, todos los requests deberán incluir:

```http
GET /api/v1/tasks
X-API-Key: sk-agent-abc123def456...
```

**Errores de autenticación:**

```json
// 401 Unauthorized
{
  "detail": "Invalid or missing API key"
}

// 403 Forbidden
{
  "detail": "API key expired"
}
```

---

## Flujos Comunes

### Flujo 1: Consultar Tareas Pendientes

**Objetivo:** Obtener lista de tareas asignadas al agente que no estén completadas.

```python
import httpx

BASE_URL = "https://ops-backend-production-e8ce.up.railway.app/api/v1"
AGENT_NAME = "Shosanna 🔥"

async def get_my_tasks():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/tasks",
            params={
                "assigned_to": AGENT_NAME,
                "include_old_done": False  # Excluir tareas done >5 días
            }
        )
        response.raise_for_status()
        tasks = response.json()
        
        # Filtrar solo backlog + in_progress
        pending = [t for t in tasks if t["status"] in ["backlog", "in_progress"]]
        return pending

# Uso
tasks = await get_my_tasks()
print(f"Tengo {len(tasks)} tareas pendientes")
```

---

### Flujo 2: Actualizar Status de Tarea

**Objetivo:** Mover una tarea a `in_progress` al comenzar a trabajar en ella.

```python
async def start_task(task_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/tasks/{task_id}/status",
            json={"status": "in_progress"}
        )
        response.raise_for_status()
        updated = response.json()
        print(f"✅ Tarea {task_id} ahora está {updated['status']}")
        return updated
```

**Validación de transiciones:**

Si intentas una transición inválida:
```python
# Tarea ya está en "done", intentas moverla a "done" de nuevo
response = await client.patch(
    f"{BASE_URL}/tasks/{task_id}/status",
    json={"status": "done"}
)
# 400 Bad Request: Invalid transition: done → done
```

---

### Flujo 3: Subir Transcript de Ejecución

**Objetivo:** Registrar el resultado de ejecutar una tarea.

```python
async def upload_transcript(task_id: int, transcript: str):
    # Actualizar description con el transcript
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/tasks/{task_id}",
            json={
                "description": transcript,
                "status": "done"
            }
        )
        response.raise_for_status()
        return response.json()

# Uso
transcript = """
## Ejecución de Task #42

### Acciones realizadas:
1. Implementé JWT authentication en `/auth/login`
2. Agregué middleware de validación
3. Escribí 15 tests unitarios

### Resultado: ✅ Completado
- Cobertura: 95%
- Deploy: OK
"""

await upload_transcript(42, transcript)
```

---

### Flujo 4: Registrar Comunicación

**Objetivo:** Loguear una interacción con otro agente o humano.

```python
async def log_communication(to_agent: str, message: str, channel: str = "direct"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/comms",
            json={
                "from_agent": AGENT_NAME,
                "to_agent": to_agent,
                "message": message,
                "channel": channel
            }
        )
        response.raise_for_status()
        return response.json()

# Uso
await log_communication(
    to_agent="Marcel 🎬",
    message="API contract updated for /projects endpoint. Check Swagger docs.",
    channel="slack"
)
```

---

### Flujo 5: Reportar Progreso en Épica

**Objetivo:** Actualizar el % de completitud de una sub-tarea de épica.

```python
async def update_epic_task_progress(task_id: int, progress: float, status: str = None):
    payload = {"progress": progress}
    if status:
        payload["status"] = status
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/epic-tasks/{task_id}",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Uso
await update_epic_task_progress(
    task_id=15,
    progress=75.0,
    status="in_progress"
)
# Esto auto-recalcula el % total de la épica
```

---

### Flujo 6: Bulk Update de Tareas

**Objetivo:** Marcar múltiples tareas como completadas de una vez.

```python
async def complete_tasks_batch(task_ids: list[int]):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/tasks/bulk-update",
            json={
                "task_ids": task_ids,
                "status": "done"
            }
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Actualizadas: {result['updated_count']}/{result['total_requested']}")
        if result.get("errors"):
            print("⚠️ Errores:", result["errors"])
        return result

# Uso
await complete_tasks_batch([10, 11, 12, 13])
```

---

## Ejemplos de Código

### Python (httpx)

```python
import httpx
from typing import Optional

class OperationsClient:
    def __init__(self, base_url: str, agent_name: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.agent_name = agent_name
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    async def get_my_tasks(self, status: Optional[str] = None):
        async with httpx.AsyncClient() as client:
            params = {"assigned_to": self.agent_name}
            if status:
                params["status"] = status
            
            response = await client.get(
                f"{self.base_url}/tasks",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def update_task_status(self, task_id: int, status: str):
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/tasks/{task_id}/status",
                json={"status": status},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def log_message(self, to_agent: str, message: str, channel: str = "direct"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/comms",
                json={
                    "from_agent": self.agent_name,
                    "to_agent": to_agent,
                    "message": message,
                    "channel": channel
                },
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

# Uso
client = OperationsClient(
    base_url="https://ops-backend-production-e8ce.up.railway.app/api/v1",
    agent_name="Shosanna 🔥"
)

tasks = await client.get_my_tasks(status="in_progress")
```

---

### JavaScript/TypeScript (fetch)

```typescript
class OperationsClient {
  constructor(
    private baseUrl: string,
    private agentName: string,
    private apiKey?: string
  ) {}

  private async request(endpoint: string, options: RequestInit = {}) {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  async getMyTasks(status?: string) {
    const params = new URLSearchParams({ assigned_to: this.agentName });
    if (status) params.append('status', status);

    return this.request(`/tasks?${params}`);
  }

  async updateTaskStatus(taskId: number, status: string) {
    return this.request(`/tasks/${taskId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  async logMessage(toAgent: string, message: string, channel = 'direct') {
    return this.request('/comms', {
      method: 'POST',
      body: JSON.stringify({
        from_agent: this.agentName,
        to_agent: toAgent,
        message,
        channel,
      }),
    });
  }
}

// Uso
const client = new OperationsClient(
  'https://ops-backend-production-e8ce.up.railway.app/api/v1',
  'Shosanna 🔥'
);

const tasks = await client.getMyTasks('backlog');
```

---

### Shell (curl)

Ver [EXAMPLES.md](./EXAMPLES.md) para ejemplos completos de curl.

---

## Rate Limits

### Configuración Actual

| Entorno | Límite |
|---------|--------|
| Producción | **Ilimitado** (pendiente implementar) |
| Local/Dev | Ilimitado |

### Implementación Futura

```
100 requests / minuto por API key
```

**Cuando se implemente, los headers incluirán:**

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1678900000
```

**Si excedes el límite:**

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "retry_after": 45
}
```

**Recomendación:** Implementa exponential backoff en tu cliente.

---

## Best Practices

### 1. Usar el Endpoint Correcto para Cada Caso

| Acción | Endpoint | Por qué |
|--------|----------|---------|
| Cambiar solo status | `PATCH /tasks/{id}/status` | Optimizado, valida transiciones |
| Actualizar múltiples campos | `PATCH /tasks/{id}` | Más flexible |
| Marcar varias tareas | `PATCH /tasks/bulk-update` | Batch operation, más eficiente |

### 2. Incluir Context en Logs de Comunicación

❌ **Mal:**
```python
await log_message("Marcel 🎬", "Done")
```

✅ **Bien:**
```python
await log_message(
    "Marcel 🎬",
    "✅ Completé Task #42 (Auth system). API contract actualizado en /docs. "
    "Deploy a production OK. Tests passing 100%."
)
```

### 3. Manejar Errores de Validación

```python
try:
    await client.update_task_status(task_id, "done")
except httpx.HTTPStatusError as e:
    if e.response.status_code == 400:
        # Transición inválida, loguear y continuar
        print(f"⚠️ No se pudo actualizar tarea {task_id}: {e.response.json()['detail']}")
    elif e.response.status_code == 404:
        # Tarea no existe
        print(f"❌ Tarea {task_id} no encontrada")
    else:
        # Error inesperado, re-raise
        raise
```

### 4. No Busy-Poll

❌ **Mal:**
```python
# Polling cada segundo
while True:
    tasks = await get_my_tasks()
    if tasks:
        process(tasks[0])
    await asyncio.sleep(1)  # 🔥 Desperdicia recursos
```

✅ **Bien:**
```python
# Webhook o consulta periódica razonable
async def check_tasks_periodically():
    while True:
        tasks = await get_my_tasks()
        if tasks:
            process(tasks[0])
        await asyncio.sleep(60)  # Cada minuto está bien
```

### 5. Usar Filtros Apropiados

```python
# No cargar tareas completadas antiguas innecesariamente
tasks = await client.get("/tasks", params={
    "assigned_to": "Shosanna 🔥",
    "status": "in_progress",  # Solo las activas
    "include_old_done": False  # Excluir done >5 días
})
```

### 6. Actualizar Progreso de Épicas Incrementalmente

```python
# Reporta progreso cada vez que avanzas, no solo al 100%
await update_epic_task_progress(task_id=15, progress=25.0)  # 25%
# ... trabajo ...
await update_epic_task_progress(task_id=15, progress=50.0)  # 50%
# ... más trabajo ...
await update_epic_task_progress(task_id=15, progress=100.0, status="done")  # Completado
```

---

## Troubleshooting

### Problema: 404 Not Found en `/tasks/{id}`

**Causa:** ID de tarea no existe o fue eliminada.

**Solución:** Consulta la lista de tareas primero:
```python
tasks = await client.get_my_tasks()
valid_ids = [t["id"] for t in tasks]
```

---

### Problema: 400 Bad Request en `/tasks/{id}/status`

**Causa:** Transición de status inválida.

**Ejemplo:**
```json
{
  "detail": "Invalid status transition: done → in_progress"
}
```

**Solución:** Verifica la tabla de transiciones válidas en [API_REFERENCE.md](./API_REFERENCE.md#patch-apiv1taskstask_idstatus).

---

### Problema: 422 Unprocessable Entity

**Causa:** Validación de Pydantic falló.

**Ejemplo:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

**Solución:** Revisa el schema requerido en [SCHEMAS.md](./SCHEMAS.md).

---

### Problema: Progreso de épica no se actualiza

**Causa:** No estás usando el endpoint correcto.

**Solución:** Usa `PATCH /epic-tasks/{id}`, NO `PATCH /tasks/{id}`. Solo el primero recalcula el progreso.

```python
# ❌ Mal (no recalcula)
await client.patch(f"/tasks/{task_id}", json={"progress": 80.0})

# ✅ Bien (recalcula automáticamente)
await client.patch(f"/epic-tasks/{task_id}", json={"progress": 80.0})
```

---

### Problema: CORS Error en el browser

**Causa:** Tu origen no está en la whitelist.

**Solución:** Si estás haciendo requests desde el navegador, pídele a un admin que agregue tu origen a `main.py`:

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

**Alternativa:** Usa un proxy del lado del servidor o llama a la API desde tu backend.

---

### Problema: Connection Timeout

**Causa:** Backend está down o Railway está en cold start.

**Solución:** Espera ~30 segundos e intenta de nuevo. Railway tiene cold start si no hay tráfico.

```python
import httpx

async def check_health_with_retry(max_retries=3):
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{BASE_URL}/health")
                response.raise_for_status()
                return True
        except httpx.TimeoutException:
            if i < max_retries - 1:
                await asyncio.sleep(10)
            else:
                raise
    return False
```

---

### Problema: Jira Sync falla con 500

**Causa:** Credenciales de Jira no están configuradas.

**Solución:** Verifica que exista `.secrets/jira.env` o que las env vars estén seteadas:

```bash
# Railway
railway variables set JIRA_DOMAIN=your-domain.atlassian.net
railway variables set JIRA_EMAIL=your-email@example.com
railway variables set JIRA_API_TOKEN=your-token
```

**Verificar:**
```bash
curl -X POST https://ops-backend-production-e8ce.up.railway.app/api/v1/jira/sync/operations
# Si está bien configurado: {"synced": 15, "project": "Operations"}
# Si falta config: {"detail": "Jira credentials not configured"}
```

---

## Recursos Adicionales

- [API Reference](./API_REFERENCE.md): Documentación completa de endpoints
- [Examples](./EXAMPLES.md): Ejemplos de curl para cada flujo
- [Schemas](./SCHEMAS.md): Modelos de datos detallados
- [Developer Guide](./DEVELOPER_GUIDE.md): Setup local y arquitectura

---

**Última actualización:** 2025-03-25  
**Versión:** 1.0.0  
**Mantenido por:** Shosanna 🔥 & Padawan 👨‍💻
