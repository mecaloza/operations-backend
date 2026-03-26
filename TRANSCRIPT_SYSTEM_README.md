# Sistema de Transcripts - Implementación Completa ✅

## 📋 Resumen

Sistema completo de gestión de transcripts (documentación markdown) vinculados a tareas y épicas con versionado automático, upload/download de archivos, y API específica para agentes AI.

## 🗄️ Modelos de Base de Datos

### Transcript
```python
- id: Integer (PK)
- title: String(500) - Título del transcript
- content: Text - Contenido markdown
- task_id: FK(tasks.id) - Nullable, vinculado a tarea
- epic_id: FK(epics.id) - Nullable, vinculado a épica
- project_id: FK(projects.id) - Obligatorio
- created_by: String(200) - Nombre del agente/usuario
- version: Integer - Versión actual (default 1)
- is_latest: Boolean - Solo última versión visible (default True)
- tags: Text - Tags separados por comas
- file_size: Integer - Tamaño en bytes
- created_at: DateTime
- updated_at: DateTime
```

**Relaciones:**
- `project` → Project
- `task` → Task (nullable)
- `epic` → Epic (nullable)
- `versions` → TranscriptVersion (cascade delete)

### TranscriptVersion
```python
- id: Integer (PK)
- transcript_id: FK(transcripts.id)
- version: Integer
- content: Text - Snapshot del contenido
- changed_by: String(200)
- change_summary: Text
- created_at: DateTime
```

**Relación:**
- `transcript` → Transcript

## 📦 Schemas (Pydantic)

### TranscriptCreate
- title: str
- content: str
- task_id: Optional[int]
- epic_id: Optional[int]
- project_id: int
- created_by: str
- tags: Optional[str]

### TranscriptUpdate
- title: Optional[str]
- content: Optional[str]
- tags: Optional[str]

### TranscriptOut
- Todos los campos del modelo
- related_task: Optional[TaskOut]
- related_epic: Optional[EpicOut]

### TranscriptVersionOut
- id, transcript_id, version, content
- changed_by, change_summary, created_at

### TranscriptQuery
- Filtros: project_id, task_id, epic_id, tags, created_by

## 🚀 API Endpoints

### Router Principal (`/api/v1/transcripts`)

#### 1. Listar Transcripts
```http
GET /api/v1/transcripts
Query params: project_id, task_id, epic_id, tags, created_by
Response: List[TranscriptOut]
```

#### 2. Crear Transcript
```http
POST /api/v1/transcripts
Body: TranscriptCreate
Response: TranscriptOut (201)
```
- Valida que al menos task_id o epic_id esté presente
- Calcula file_size automáticamente
- Crea versión inicial automáticamente

#### 3. Obtener Transcript
```http
GET /api/v1/transcripts/{transcript_id}
Response: TranscriptOut
```

#### 4. Actualizar Transcript (con versionado)
```http
PATCH /api/v1/transcripts/{transcript_id}
Query params: changed_by, change_summary
Body: TranscriptUpdate
Response: TranscriptOut
```
- Guarda versión anterior en TranscriptVersion
- Incrementa version automáticamente
- Nueva versión se marca como is_latest=True

#### 5. Eliminar Transcript (soft delete)
```http
DELETE /api/v1/transcripts/{transcript_id}
Response: {message: "Transcript marcado como eliminado"}
```
- Marca is_latest=False (soft delete)

#### 6. Historial de Versiones
```http
GET /api/v1/transcripts/{transcript_id}/versions
Response: List[TranscriptVersionOut]
```

#### 7. Descargar Transcript
```http
GET /api/v1/transcripts/{transcript_id}/download
Response: File (.md)
Content-Disposition: attachment; filename=transcript_{id}_{title}.md
```

#### 8. Upload de Transcript
```http
POST /api/v1/transcripts/upload
Multipart form:
  - file: UploadFile (.md/.txt)
  - project_id: int
  - task_id: Optional[int]
  - epic_id: Optional[int]
  - created_by: str
  - tags: Optional[str]
Response: TranscriptOut (201)
```

#### 9. Transcripts por Tarea
```http
GET /api/v1/transcripts/by-task/{task_id}
Response: List[TranscriptOut]
```

#### 10. Transcripts por Épica
```http
GET /api/v1/transcripts/by-epic/{epic_id}
Response: List[TranscriptOut]
```

#### 11. Transcripts por Proyecto
```http
GET /api/v1/transcripts/by-project/{project_id}
Response: List[TranscriptOut]
```

### Agent API (`/api/v1/agent-api`)

Todos requieren autenticación via `X-Agent-API-Key` header.

#### 1. Descargar Transcript
```http
GET /api/v1/agent-api/transcripts/{transcript_id}
Requiere: read:transcripts permission
Response: TranscriptOut
```

#### 2. Contexto de Tarea
```http
GET /api/v1/agent-api/tasks/{task_id}/context
Requiere: read:tasks, read:transcripts
Response: {
  task: TaskOut,
  transcripts: List[TranscriptOut],
  epic: Optional[EpicOut]
}
```
Devuelve contexto completo de una tarea para que agentes AI tengan toda la información necesaria.

#### 3. Crear Transcript desde Agente
```http
POST /api/v1/agent-api/transcripts
Requiere: write:transcripts permission
Body: TranscriptCreate
Response: TranscriptOut (201)
```
- Auto-asigna created_by al nombre del agente autenticado si no se provee

## ✅ Validaciones

1. **Al crear/actualizar:**
   - Al menos uno de `task_id` o `epic_id` debe estar presente
   - `project_id` es obligatorio
   - `title` no puede estar vacío
   - `content` no puede estar vacío

2. **Relaciones:**
   - Valida que project_id exista
   - Valida que task_id exista (si se provee)
   - Valida que epic_id exista (si se provee)

## 🔄 Versionado Automático

Al actualizar un transcript (PATCH):
1. Se guarda la versión actual en `TranscriptVersion`
2. Se incrementa el campo `version` del transcript
3. Se actualiza el contenido/título/tags
4. Se crea un nuevo registro en `TranscriptVersion` con la nueva versión
5. El transcript mantiene `is_latest=True`

## 🌱 Seeds de Ejemplo

Se crean automáticamente al iniciar la app:

### Tarea de Ejemplo
- **Título:** "Sistema de Transcripts"
- **Proyecto:** Operations
- **Asignado a:** Shosanna 🔥
- **Status:** in_progress
- **Priority:** high

### Transcripts de Ejemplo

#### 1. Planning - Sistema de Transcripts
- Tags: `planning,backend,transcripts`
- Contenido: Objetivos, requisitos, stack técnico, timeline
- Vinculado a tarea #1

#### 2. Implementación - Modelos y Schemas
- Tags: `implementation,backend,models`
- Contenido: Documentación técnica de modelos, validaciones, endpoints
- Vinculado a tarea #1

## 🔐 Permisos para Agentes

Permisos agregados a AgentAuth:
- `read:transcripts` - Leer transcripts
- `write:transcripts` - Crear/actualizar transcripts

Todos los agentes seeded tienen estos permisos por defecto.

## 📁 Archivos Modificados/Creados

### Nuevos
- ✅ `routers/transcripts.py` - Router principal con 11 endpoints

### Modificados
- ✅ `models.py` - Agregados Transcript y TranscriptVersion
- ✅ `schemas.py` - Agregados schemas de transcripts
- ✅ `routers/agent_api.py` - Agregados 3 endpoints para agentes
- ✅ `main.py` - Registrado router y seeds

## 🧪 Testing

Script de prueba creado: `test_transcripts.py`

```bash
python3 test_transcripts.py
```

Resultado esperado:
```
✅ Base de datos creada
✅ Proyectos seeded
✅ Transcripts seeded
📝 Transcripts en DB: 2
✅ Tareas en DB: 1
✅ TEST EXITOSO
```

## 🚀 Uso

### 1. Crear un Transcript
```bash
curl -X POST http://localhost:8000/api/v1/transcripts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mi Transcript",
    "content": "# Contenido markdown",
    "task_id": 1,
    "project_id": 1,
    "created_by": "Shosanna 🔥",
    "tags": "testing,example"
  }'
```

### 2. Listar Transcripts de una Tarea
```bash
curl http://localhost:8000/api/v1/transcripts/by-task/1
```

### 3. Actualizar con Versionado
```bash
curl -X PATCH http://localhost:8000/api/v1/transcripts/1?changed_by=Shosanna \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Contenido actualizado",
    "tags": "updated,v2"
  }'
```

### 4. Upload de Archivo
```bash
curl -X POST http://localhost:8000/api/v1/transcripts/upload \
  -F "file=@transcript.md" \
  -F "project_id=1" \
  -F "task_id=1" \
  -F "created_by=Shosanna"
```

### 5. Descargar Transcript
```bash
curl -O http://localhost:8000/api/v1/transcripts/1/download
```

### 6. Agent API - Contexto de Tarea
```bash
curl http://localhost:8000/api/v1/agent-api/tasks/1/context \
  -H "X-Agent-API-Key: {API_KEY}"
```

## 📊 Diagrama de Flujo

```
Usuario/Agente
    ↓
POST /transcripts (crear)
    ↓
Transcript (v1, is_latest=true)
    ↓
TranscriptVersion (v1, snapshot)
    ↓
PATCH /transcripts/{id} (actualizar)
    ↓
TranscriptVersion (v1, snapshot anterior)
    ↓
Transcript (v2, is_latest=true, contenido nuevo)
    ↓
TranscriptVersion (v2, snapshot nuevo)
    ↓
GET /transcripts/{id}/versions (historial)
    ↓
[v2, v1] (ordenado desc)
```

## ✨ Features Destacadas

1. **Versionado Automático**: Cada update crea una nueva versión
2. **Soft Delete**: Los transcripts nunca se borran, solo se marcan como no-latest
3. **Upload/Download**: Soporte nativo para archivos .md/.txt
4. **Agent API**: Endpoints específicos con autenticación y rate limiting
5. **Relaciones Flexibles**: Puede estar vinculado a task, epic, o ambos
6. **Tags**: Categorización flexible con tags separados por comas
7. **File Size Tracking**: Se calcula automáticamente al crear/actualizar
8. **Contexto Completo**: Endpoint para agentes que devuelve task + transcripts + epic

## 🎯 Source of Truth

El Operations Dashboard es el **único source of truth** para transcripts en todo el ecosistema Action Experience.

---

**Implementado por:** Shosanna 🔥  
**Fecha:** 2026-03-25  
**Estado:** ✅ Completo y funcionando
