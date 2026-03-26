-- Migration 003: Sistema de Usuarios y Equipos
-- Autor: Shosanna 🔥
-- Fecha: 2026-03-25
-- Descripción: Agrega tablas Team, User y relación M2M User<->Agent

-- 1. Crear tabla teams
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX idx_teams_project_id ON teams(project_id);

-- 2. Crear tabla users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(200) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_team_id ON users(team_id);
CREATE INDEX idx_users_active ON users(active);

-- 3. Crear tabla de asociación M2M user_agent_assignments
CREATE TABLE IF NOT EXISTS user_agent_assignments (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, agent_id)
);

CREATE INDEX idx_user_agent_user_id ON user_agent_assignments(user_id);
CREATE INDEX idx_user_agent_agent_id ON user_agent_assignments(agent_id);

-- 4. Agregar columna assigned_to_user_id a agents (nullable)
ALTER TABLE agents ADD COLUMN IF NOT EXISTS assigned_to_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_agents_assigned_to_user_id ON agents(assigned_to_user_id);

-- 5. Seedear equipo Operations
DO $$
DECLARE
    ops_project_id INTEGER;
    ops_team_id INTEGER;
BEGIN
    -- Obtener project_id de Operations
    SELECT id INTO ops_project_id FROM projects WHERE slug = 'operations' LIMIT 1;
    
    IF ops_project_id IS NOT NULL THEN
        -- Crear equipo Operations si no existe
        INSERT INTO teams (name, description, project_id)
        VALUES ('Operations', 'Equipo de operaciones y desarrollo del dashboard', ops_project_id)
        ON CONFLICT DO NOTHING
        RETURNING id INTO ops_team_id;
        
        -- Si ya existía, obtener su ID
        IF ops_team_id IS NULL THEN
            SELECT id INTO ops_team_id FROM teams WHERE name = 'Operations' AND project_id = ops_project_id LIMIT 1;
        END IF;
        
        -- Seedear usuarios si el equipo existe
        IF ops_team_id IS NOT NULL THEN
            INSERT INTO users (username, email, full_name, hashed_password, role, team_id, active)
            VALUES 
                ('padawan', 'padawan@ops.dev', 'Padawan', 'admin123', 'admin', ops_team_id, TRUE),
                ('hanslanda', 'hans@ops.dev', 'Hans Landa', 'leader123', 'leader', ops_team_id, TRUE),
                ('marcel', 'marcel@ops.dev', 'Marcel', 'member123', 'member', ops_team_id, TRUE),
                ('shosanna', 'shosanna@ops.dev', 'Shosanna', 'member123', 'member', ops_team_id, TRUE)
            ON CONFLICT (username) DO NOTHING;
        END IF;
    END IF;
END $$;

COMMIT;
