# 🔐 Credenciales - Operations Dashboard

## Usuario Administrador

```
Username: padawan
Password: admin123
Email: padawan@ops.dev
Rol: admin
```

**Acceso:** Permisos completos sobre el sistema

---

## Usuarios de Prueba

### Hans Landa (Leader)
```
Username: hanslanda
Password: leader123
Email: hans@ops.dev
Rol: leader
```

### Marcel (Member)
```
Username: marcel
Password: member123
Email: marcel@ops.dev
Rol: member
```

### Shosanna (Member)
```
Username: shosanna
Password: member123
Email: shosanna@ops.dev
Rol: member
```

---

## Cómo Loguearse

### 1. Via API (Programático)

```bash
# Login (obtener token)
curl -X POST https://ops-backend-production-e8ce.up.railway.app/api/v1/auth/login \
  -d "username=padawan&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded"

# Respuesta:
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "padawan",
    "email": "padawan@ops.dev",
    "full_name": "Padawan",
    "role": "admin",
    "team_id": 1
  }
}

# Usar token en requests
curl https://ops-backend-production-e8ce.up.railway.app/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 2. Via Frontend (Dashboard)

1. Abrir: https://operations-dashboard-nine.vercel.app
2. Ir a Login
3. Usar: `padawan` / `admin123`
4. El token se guarda automáticamente en localStorage

---

## Roles y Permisos

### admin
- CRUD completo de proyectos, tareas, épicas
- Gestión de usuarios y equipos
- Configuración del sistema
- Acceso a todos los endpoints

### leader
- CRUD de tareas y épicas de su proyecto
- Asignación de tareas a miembros
- Reportes de sprint
- NO puede crear/eliminar proyectos

### member
- Ver tareas asignadas
- Actualizar estado de sus tareas
- Ver épicas del proyecto
- NO puede asignar tareas a otros

---

## Seguridad

### Tokens JWT
- **Algoritmo:** HS256
- **Expiración:** 7 días
- **Secret Key:** Definido en variable de entorno (producción) o hardcoded (dev)
- **Renovación:** Endpoint `/api/v1/auth/refresh`

### Passwords
- **Hashing:** bcrypt (costo 12)
- **Migración:** Passwords plain text se migran automáticamente a bcrypt en primer login
- **Límite:** 72 bytes (limitación de bcrypt)

### Rate Limiting
- **Pendiente implementar** en producción
- Target: 100 req/min por IP

---

## Generar Nuevos Usuarios

### Via Python Console (Local)

```python
from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

# Crear usuario
new_user = User(
    username="nuevo_usuario",
    email="nuevo@ops.dev",
    full_name="Nombre Completo",
    hashed_password=pwd_context.hash("password123"),
    role="member",  # admin, leader, member
    team_id=1,  # ID del team Operations
    active=True
)

db.add(new_user)
db.commit()
print(f"Usuario creado: {new_user.id}")
```

### Via API (Próximamente)

Endpoint `/api/v1/users/register` - En desarrollo

---

## Cambiar Contraseña

### Manualmente (Base de datos)

```python
from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

user = db.query(User).filter(User.username == "padawan").first()
user.hashed_password = pwd_context.hash("nueva_contraseña")
db.commit()
```

### Via API (Próximamente)

Endpoint `/api/v1/auth/change-password` - En desarrollo

---

## Variables de Entorno

### Railway (Producción)

```bash
DATABASE_URL=postgresql://postgres.xorxplnzfdnmuiecgvtt:lpCYw8QVXy6DR0dA@aws-0-us-west-2.pooler.supabase.com:6543/postgres
SECRET_KEY=ops-dashboard-secret-key-change-in-production-2024  # ⚠️ CAMBIAR en producción
```

### Local (.env)

```bash
DATABASE_URL=sqlite:///./operations.db
SECRET_KEY=dev-secret-key-local-only
```

---

## Troubleshooting

### Error: "Could not validate credentials"
- Token expirado (> 7 días)
- Token inválido o corrupto
- Solución: Login de nuevo

### Error: "Incorrect username or password"
- Credenciales incorrectas
- Usuario no existe
- Usuario inactivo (active=False)

### Error: "Operation requires one of: admin, leader"
- Tu rol no tiene permisos para esa acción
- Contactar administrador para cambio de rol

---

**Última actualización:** 2026-03-26 (Shosanna 🔥)
