# Task #152 - Sistema de Usuarios y Equipos

## ✅ Implementación Completa

**Autor:** Shosanna 🔥  
**Fecha:** 2026-03-25  
**Status:** Implementado (pendiente migración a producción)

---

## 📦 Archivos Creados

### Routers
- `routers/users.py` - CRUD completo de usuarios + asignación de agentes
- `routers/teams.py` - CRUD completo de equipos

### Migraciones
- `migrations/003_users_teams.sql` - Migración SQL para PostgreSQL/Supabase
- `migrations/README.md` - Guía de ejecución de migraciones

### Tests
- `test_users_local.sh` - Script de prueba de endpoints en local

### Documentación
- `TASK152_IMPLEMENTATION.md` - Este archivo

---

## 🗄️ Modelos Actualizados

### `models.py`

#### 1. Nuevos Enums
```python
class UserRole(str, enum.Enum):
    admin = "admin"
    leader = "leader"
    member = "member"
```

#### 2. Tabla M2M User <-> Agent
```python
user_agent_association = Table(
    'user_agent_assignments',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('agent_id', Integer, ForeignKey('agents.id'), primary_key=True)
)
```

#### 3. Modelo Team
```python
class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=...)
    
    project = relationship("Project", back_populates="teams")
    members = relationship("User", back_populates="team")
```

#### 4. Modelo User
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Plain text por ahora
    role = Column(String(50), nullable=False, default=UserRole.member.value)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    active = Column(Boolean, default=True)  # Soft delete
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=...)
    
    team = relationship("Team", back_populates="members")
    assigned_agents = relationship("Agent", secondary=user_agent_association, back_populates="assigned_users")
```

#### 5. Agent Actualizado
```python
class Agent(Base):
    # ... campos existentes ...
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # ... relaciones existentes ...
    assigned_users = relationship("User", secondary=user_agent_association, back_populates="assigned_agents")
```

---

## 📄 Schemas Creados

### `schemas.py`

```python
# Team Schemas
class TeamBase(BaseModel):
    name: str
    description: str = ""
    project_id: int

class TeamCreate(TeamBase): pass
class TeamUpdate(BaseModel): ...
class TeamOut(TeamBase): ...

# User Schemas
class UserBase(BaseModel):
    email: str
    username: str
    full_name: str
    role: str = "member"
    team_id: Optional[int] = None

class UserCreate(UserBase):
    password: str  # Plain text por ahora

class UserUpdate(BaseModel): ...
class UserOut(UserBase): ...

class UserWithAgents(UserOut):
    assigned_agents: List[AgentOut] = []
```

---

## 🌐 Endpoints Implementados

### Users Router (`/api/v1/users`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/users` | Listar usuarios (con filtro `active_only`) |
| POST | `/users` | Crear usuario nuevo |
| GET | `/users/{user_id}` | Detalle de usuario |
| PATCH | `/users/{user_id}` | Actualizar usuario |
| DELETE | `/users/{user_id}` | Soft delete (marca `active=False`) |
| POST | `/users/{user_id}/assign-agent/{agent_id}` | Asignar agente a usuario |
| DELETE | `/users/{user_id}/unassign-agent/{agent_id}` | Desasignar agente |
| GET | `/users/{user_id}/agents` | Listar agentes asignados |

### Teams Router (`/api/v1/teams`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/teams` | Listar equipos (filtro opcional por `project_id`) |
| POST | `/teams` | Crear equipo nuevo |
| GET | `/teams/{team_id}` | Detalle de equipo |
| PATCH | `/teams/{team_id}` | Actualizar equipo |
| DELETE | `/teams/{team_id}` | Eliminar equipo (físicamente) |
| GET | `/teams/{team_id}/members` | Listar miembros del equipo |

---

## ✅ Validaciones Implementadas

### User
- ✅ Email único (constraint + validación en endpoint)
- ✅ Username único (constraint + validación en endpoint)
- ✅ Role válido (`admin`, `leader`, `member`)
- ✅ No borrar usuario con agentes asignados (raise 400)
- ✅ Soft delete con campo `active`

### Team
- ✅ No borrar equipo con miembros (raise 400)
- ✅ Validar que `project_id` existe

### Agent Assignment
- ✅ No asignar agente ya asignado al usuario
- ✅ Validar que user y agent existan antes de asignar/desasignar

---

## 🌱 Seed Data

### En `main.py`

```python
SEED_USERS = [
    {"username": "padawan", "email": "padawan@ops.dev", "full_name": "Padawan", "password": "admin123", "role": "admin", "team_name": "Operations"},
    {"username": "hanslanda", "email": "hans@ops.dev", "full_name": "Hans Landa", "password": "leader123", "role": "leader", "team_name": "Operations"},
    {"username": "marcel", "email": "marcel@ops.dev", "full_name": "Marcel", "password": "member123", "role": "member", "team_name": "Operations"},
    {"username": "shosanna", "email": "shosanna@ops.dev", "full_name": "Shosanna", "password": "member123", "role": "member", "team_name": "Operations"},
]
```

**Equipo creado:** Operations (vinculado al proyecto `operations`)

---

## 🚀 Deployment

### Local (SQLite)

1. Arrancar servidor:
```bash
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. Probar endpoints:
```bash
./test_users_local.sh
```

SQLAlchemy creará las tablas automáticamente en `operations.db`.

### Producción (Supabase PostgreSQL)

**⚠️ PENDIENTE - Requiere ejecutar migración:**

```bash
psql "postgresql://postgres.xorxplnzfdnmuiecgvtt:Padaw@n0311@aws-0-us-west-2.pooler.supabase.com:6543/postgres" \
  -f migrations/003_users_teams.sql
```

Una vez ejecutada la migración, hacer deploy:

```bash
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend
railway up --detach
```

---

## 📝 Notas Importantes

### Seguridad (TO-DO)

- ⚠️ **Passwords en plain text** - Por diseño temporal según requerimientos
- 🔒 Falta implementar:
  - Bcrypt hashing
  - JWT authentication
  - Password policy
  - Rate limiting en endpoints sensibles

### Relaciones

- **User -> Team**: FK `team_id` (nullable, ON DELETE SET NULL)
- **User <-> Agent**: M2M via `user_agent_assignments`
- **Agent -> User**: FK nullable `assigned_to_user_id` (no usado actualmente, preparado para futuro)
- **Team -> Project**: FK `project_id` (required, ON DELETE CASCADE)

### Índices Creados

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_team_id ON users(team_id);
CREATE INDEX idx_users_active ON users(active);
CREATE INDEX idx_teams_project_id ON teams(project_id);
CREATE INDEX idx_user_agent_user_id ON user_agent_assignments(user_id);
CREATE INDEX idx_user_agent_agent_id ON user_agent_assignments(agent_id);
CREATE INDEX idx_agents_assigned_to_user_id ON agents(assigned_to_user_id);
```

---

## 🧪 Testing

### Casos de Prueba Cubiertos

1. ✅ Crear usuarios con roles diferentes
2. ✅ Validar email/username únicos
3. ✅ Asignar múltiples agentes a un usuario
4. ✅ Impedir borrar usuario con agentes asignados
5. ✅ Soft delete de usuarios
6. ✅ Crear equipos vinculados a proyectos
7. ✅ Listar miembros de un equipo
8. ✅ Impedir borrar equipo con miembros

### Ejecutar Tests

```bash
# Arrancar servidor en puerto 8000
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# En otra terminal
./test_users_local.sh
```

---

## 📊 Próximos Pasos

1. **Ejecutar migración en producción** (Supabase)
2. **Implementar autenticación JWT**
3. **Hash de passwords con bcrypt**
4. **Frontend para gestión de usuarios/equipos**
5. **Permisos basados en roles**
6. **Auditoría de cambios de usuarios**

---

**¿Listo para production?**  
✅ Código  
✅ Tests locales  
⚠️ Migración DB (pendiente ejecutar en Supabase)  
⚠️ Seguridad (passwords plain text - por diseño temporal)
