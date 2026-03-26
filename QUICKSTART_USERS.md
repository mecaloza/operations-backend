# Quick Start - Sistema de Usuarios y Equipos

## 🚀 Para Desarrolladores

### 1️⃣ Testing Local (SQLite)

```bash
# Arrancar servidor
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Probar endpoints (en otra terminal)
./test_users_local.sh
```

El seed creará automáticamente:
- Equipo "Operations"
- 4 usuarios: padawan (admin), hanslanda (leader), marcel, shosanna (members)

---

### 2️⃣ Deploy a Producción

**⚠️ PRIMERO:** Ejecutar migración en Supabase

```bash
psql "postgresql://postgres.xorxplnzfdnmuiecgvtt:Padaw@n0311@aws-0-us-west-2.pooler.supabase.com:6543/postgres" \
  -f migrations/003_users_teams.sql
```

**Luego:** Deploy con Railway

```bash
railway up --detach
```

---

### 3️⃣ Ejemplos de Uso

#### Crear Usuario
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@ops.dev",
    "username": "nuevo",
    "full_name": "Nuevo Usuario",
    "password": "pass123",
    "role": "member",
    "team_id": 1
  }'
```

#### Asignar Agente a Usuario
```bash
curl -X POST http://localhost:8000/api/v1/users/1/assign-agent/1
```

#### Listar Agentes de Usuario
```bash
curl http://localhost:8000/api/v1/users/1/agents
```

#### Crear Equipo
```bash
curl -X POST http://localhost:8000/api/v1/teams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Engineering",
    "description": "Equipo de ingeniería",
    "project_id": 1
  }'
```

---

### 4️⃣ Estructura

```
backend/
├── models.py                   # User, Team, UserRole
├── schemas.py                  # UserCreate, TeamOut, etc.
├── routers/
│   ├── users.py               # 8 endpoints
│   └── teams.py               # 6 endpoints
├── migrations/
│   └── 003_users_teams.sql    # Migración PostgreSQL
├── test_users_local.sh        # Tests
├── TASK152_SUMMARY.md         # Resumen ejecutivo
└── TASK152_IMPLEMENTATION.md  # Docs completas
```

---

### 5️⃣ Roles de Usuario

- **admin**: Acceso total (ej: Padawan)
- **leader**: Líder de equipo (ej: Hans Landa)
- **member**: Miembro regular (ej: Marcel, Shosanna)

*(Permisos pendientes de implementar en endpoints)*

---

### 6️⃣ Troubleshooting

**Error: `column users.id does not exist`**
→ Ejecutar migración `003_users_teams.sql` en producción

**Error: `email already exists`**
→ Email debe ser único, cambiar valor

**Error: `Cannot delete user with assigned agents`**
→ Primero desasignar agentes con `DELETE /users/{id}/unassign-agent/{agent_id}`

---

### 7️⃣ Próximos Pasos

1. [ ] Ejecutar migración en Supabase
2. [ ] Deploy a Railway
3. [ ] Implementar autenticación JWT
4. [ ] Frontend para gestión de usuarios
5. [ ] Permisos basados en roles

---

**👤 Usuarios Seed**

| Username | Email | Role | Password |
|----------|-------|------|----------|
| padawan | padawan@ops.dev | admin | admin123 |
| hanslanda | hans@ops.dev | leader | leader123 |
| marcel | marcel@ops.dev | member | member123 |
| shosanna | shosanna@ops.dev | member | member123 |

---

**📚 Docs Completas:** `TASK152_IMPLEMENTATION.md`  
**🔥 Autor:** Shosanna
