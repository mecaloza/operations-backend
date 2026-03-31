-- 004_epics_m2m_system.sql
-- Migración: Sistema de Épicas M2M con Tareas
-- Fecha: 2026-03-27
-- Autor: Shosanna 🔥

-- IMPORTANTE: NO DROP TABLE EN PRODUCCIÓN
-- Esta migración usa solo CREATE TABLE IF NOT EXISTS y ALTER TABLE ADD COLUMN

-- ========== PASO 1: Agregar task_progress a tasks ==========

-- Agregar columna task_progress a tasks (si no existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'task_progress'
    ) THEN
        ALTER TABLE tasks ADD COLUMN task_progress REAL DEFAULT 0.0;
    END IF;
END $$;

-- ========== PASO 2: Crear nueva tabla epics (si no existe) ==========

-- NOTA: Si la tabla epics ya existe con la estructura vieja, necesitaremos renombrarla
-- y crear la nueva. Pero NUNCA hacemos DROP.

-- Renombrar tabla vieja (si existe) para backup
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'epics'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'epics' AND column_name = 'priority'
    ) THEN
        -- La tabla epics existe pero NO tiene la nueva estructura
        -- La renombramos para backup
        ALTER TABLE epics RENAME TO epics_old_backup;
        ALTER TABLE epic_tasks RENAME TO epic_tasks_old_backup;
        ALTER TABLE epic_progress_history RENAME TO epic_progress_history_old_backup;
    END IF;
END $$;

-- Crear nueva tabla epics
CREATE TABLE IF NOT EXISTS epics (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    project_id INTEGER REFERENCES projects(id),
    priority VARCHAR(20) DEFAULT 'medium',
    progress REAL DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'not_started',
    goal TEXT,
    start_date DATE,
    target_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========== PASO 3: Crear tabla M2M epic_task_assignments ==========

CREATE TABLE IF NOT EXISTS epic_task_assignments (
    id SERIAL PRIMARY KEY,
    epic_id INTEGER REFERENCES epics(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_epic_task UNIQUE(epic_id, task_id)
);

-- ========== PASO 4: Crear índices para performance ==========

CREATE INDEX IF NOT EXISTS idx_epics_project_id ON epics(project_id);
CREATE INDEX IF NOT EXISTS idx_epics_status ON epics(status);
CREATE INDEX IF NOT EXISTS idx_epics_priority ON epics(priority);
CREATE INDEX IF NOT EXISTS idx_epic_task_assignments_epic_id ON epic_task_assignments(epic_id);
CREATE INDEX IF NOT EXISTS idx_epic_task_assignments_task_id ON epic_task_assignments(task_id);

-- ========== PASO 5: Migrar datos de épicas viejas (si existen) ==========

-- Esta parte solo se ejecuta si existe epics_old_backup
-- y migra las épicas viejas a la nueva estructura (sin sub-tareas, solo metadata)

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'epics_old_backup'
    ) THEN
        -- Migrar épicas viejas (solo metadata)
        INSERT INTO epics (
            title,
            description,
            project_id,
            priority,
            progress,
            status,
            goal,
            created_at,
            updated_at
        )
        SELECT 
            title,
            description,
            project_id,
            'medium' AS priority,
            calculated_progress,
            CASE status
                WHEN 'active' THEN 'in_progress'
                WHEN 'completed' THEN 'done'
                WHEN 'blocked' THEN 'not_started'
                ELSE 'not_started'
            END AS status,
            NULL AS goal,
            created_at,
            updated_at
        FROM epics_old_backup
        WHERE deleted = FALSE;

        -- NOTA: Las sub-tareas viejas (epic_tasks_old_backup) NO se migran
        -- porque ahora usamos M2M con las tareas existentes del proyecto
    END IF;
END $$;

-- ========== PASO 6: Verificación post-migración ==========

-- Contar épicas migradas
DO $$
DECLARE
    epics_count INTEGER;
    tasks_with_progress INTEGER;
BEGIN
    SELECT COUNT(*) INTO epics_count FROM epics;
    SELECT COUNT(*) INTO tasks_with_progress FROM tasks WHERE task_progress > 0;
    
    RAISE NOTICE 'Migración completada:';
    RAISE NOTICE '  - Épicas totales: %', epics_count;
    RAISE NOTICE '  - Tareas con progreso > 0: %', tasks_with_progress;
    RAISE NOTICE '  - Estructura M2M: epic_task_assignments creada';
END $$;

-- ========== FIN DE MIGRACIÓN ==========
-- Las tablas viejas (epics_old_backup, epic_tasks_old_backup, epic_progress_history_old_backup)
-- se mantienen por seguridad. Se pueden eliminar manualmente después de validar.
