# Migraciones de Base de Datos

## Ejecutar Migraciones en Producción (Supabase)

Para ejecutar una migración en la base de datos de producción:

1. Conéctate a Supabase:
```bash
psql "postgresql://postgres.xorxplnzfdnmuiecgvtt:Padaw@n0311@aws-0-us-west-2.pooler.supabase.com:6543/postgres"
```

2. Ejecuta la migración:
```bash
\i migrations/003_users_teams.sql
```

O directamente desde el shell:
```bash
psql "postgresql://postgres.xorxplnzfdnmuiecgvtt:Padaw@n0311@aws-0-us-west-2.pooler.supabase.com:6543/postgres" -f migrations/003_users_teams.sql
```

## Historial de Migraciones

- **001_initial_schema.sql** (implícita) - Schema inicial con projects, agents, tasks, comms
- **002_epics_transcripts.sql** (implícita) - Épicas, EpicTasks, Transcripts, AgentAuth
- **003_users_teams.sql** - Sistema de usuarios, equipos y asignación de agentes

## Local (SQLite)

Para desarrollo local, SQLAlchemy crea las tablas automáticamente con:
```python
Base.metadata.create_all(bind=engine)
```

Las migraciones SQL son solo para producción PostgreSQL.
