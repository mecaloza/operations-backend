# 🔥 Operations Backend - Quick Start

## TL;DR

```bash
# Setup (primera vez)
./dev_setup.sh

# Desarrollo (cada día)
source venv/bin/activate
./dev.sh
```

Ya está. Server corriendo en http://localhost:8000

## ¿Qué es esto?

Backend del Operations Dashboard - el **source of truth** de todos los proyectos.

**Stack:**
- FastAPI + SQLAlchemy
- SQLite (local) / PostgreSQL (prod via Supabase)
- Deploy en Railway

## Setup de Desarrollo

### 1. Instalación

```bash
./dev_setup.sh
```

Esto configura:
- Virtual environment
- Dependencias (prod + dev)
- Base de datos local
- Pre-commit hooks

### 2. Desarrollo

```bash
./dev.sh
```

Server con hot reload en http://localhost:8000

**API Docs:** http://localhost:8000/docs

## Comandos Útiles

```bash
# Tests
pytest                          # Todos los tests
pytest -m unit                  # Solo unitarios
pytest --cov=.                  # Con coverage

# Code quality
black .                         # Formatear
ruff check .                    # Lint
ruff check . --fix              # Fix automático

# Pre-commit (opcional)
pre-commit run --all-files
```

## Estructura

```
backend/
├── main.py              # App principal
├── models.py            # DB models
├── schemas.py           # Pydantic schemas
├── routers/             # Endpoints
├── tests/               # Tests
├── dev.sh               # 🔥 Dev server
└── dev_setup.sh         # 🔧 Setup inicial
```

## Hot Reload

Guarda cualquier `.py` y el server se actualiza solo. Sin restart.

## Deploy

```bash
railway up --detach
```

Producción: https://ops-backend-production-e8ce.up.railway.app

## Documentación Completa

Lee [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) para:
- Testing avanzado
- Debugging
- Git workflow
- DB migrations
- Variables de entorno
- Y más...

---

**¿Problemas?** Lee [DEVELOPMENT.md](docs/DEVELOPMENT.md) o pregunta en el canal.

**Stack:** FastAPI • SQLAlchemy • Pytest • Black • Ruff

**Deploy:** Railway • Supabase

**Hecho con 🔥 por Shosanna**
