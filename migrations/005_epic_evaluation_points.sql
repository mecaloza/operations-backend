-- Migración 005: Epic Evaluation Points System
-- Fecha: 2026-03-30
-- Autor: Shosanna 🔥
-- Descripción: Sistema de puntos de evaluación por workstream/categoría para épicas

-- ============================================================
-- Tabla: epic_evaluation_points
-- ============================================================
CREATE TABLE IF NOT EXISTS epic_evaluation_points (
    id SERIAL PRIMARY KEY,
    epic_id INTEGER NOT NULL REFERENCES epics(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    assigned_to INTEGER REFERENCES users(id),
    progress DECIMAL(5,2) DEFAULT 0.0 CHECK (progress >= 0 AND progress <= 100),
    weight DECIMAL(5,2) DEFAULT 1.0 CHECK (weight > 0),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para optimizar queries
CREATE INDEX IF NOT EXISTS idx_evaluation_points_epic ON epic_evaluation_points(epic_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_points_user ON epic_evaluation_points(assigned_to);

-- Trigger para updated_at automático
CREATE OR REPLACE FUNCTION update_evaluation_points_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_evaluation_points_updated_at
    BEFORE UPDATE ON epic_evaluation_points
    FOR EACH ROW
    EXECUTE FUNCTION update_evaluation_points_updated_at();

-- ============================================================
-- Tabla: daily_evaluation_point_progress (PENDIENTE - tabla dailys no existe)
-- ============================================================
-- TODO: Descomentar cuando exista tabla 'dailys'
-- CREATE TABLE IF NOT EXISTS daily_evaluation_point_progress (
--     id SERIAL PRIMARY KEY,
--     daily_id INTEGER NOT NULL REFERENCES dailys(id) ON DELETE CASCADE,
--     evaluation_point_id INTEGER NOT NULL REFERENCES epic_evaluation_points(id) ON DELETE CASCADE,
--     previous_progress DECIMAL(5,2),
--     new_progress DECIMAL(5,2) CHECK (new_progress >= 0 AND new_progress <= 100),
--     delta DECIMAL(5,2),
--     notes TEXT,
--     created_at TIMESTAMP DEFAULT NOW(),
--     UNIQUE(daily_id, evaluation_point_id)
-- );
--
-- -- Índice para queries por daily
-- CREATE INDEX IF NOT EXISTS idx_daily_eval_progress_daily ON daily_evaluation_point_progress(daily_id);

-- ============================================================
-- Comentarios para documentación
-- ============================================================
COMMENT ON TABLE epic_evaluation_points IS 'Puntos de evaluación (workstreams) de épicas con responsables y % independientes';
COMMENT ON COLUMN epic_evaluation_points.category IS 'Categoría del workstream: Backend, Admin, Landing, App, Diseño, QA, etc.';
COMMENT ON COLUMN epic_evaluation_points.progress IS 'Progreso actual del punto de evaluación (0.00 - 100.00)';
COMMENT ON COLUMN epic_evaluation_points.weight IS 'Peso para promedio ponderado (futuro)';

-- TODO: Descomentar cuando exista tabla 'dailys'
-- COMMENT ON TABLE daily_evaluation_point_progress IS 'Tracking histórico de progreso de evaluation points en dailys';
-- COMMENT ON COLUMN daily_evaluation_point_progress.delta IS 'Diferencia entre new_progress y previous_progress';

-- ============================================================
-- Verificación post-migración
-- ============================================================
-- SELECT 'Migración 005 completada' AS status;
-- SELECT COUNT(*) FROM epic_evaluation_points;
