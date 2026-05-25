-- Fix CoachRequest table if needed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='accounts_coachrequest' AND column_name='created_at'
    ) THEN
        ALTER TABLE accounts_coachrequest RENAME COLUMN created_at TO requested_at;
    END IF;
END $$;

-- Create UserActivity table if not exists
CREATE TABLE IF NOT EXISTS accounts_useractivity (
    id BIGSERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id BIGINT NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS accounts_us_user_id_5e8b9a_idx ON accounts_useractivity (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS accounts_us_action__7c4f3e_idx ON accounts_useractivity (action_type, created_at DESC);
CREATE INDEX IF NOT EXISTS accounts_us_created_3f2a1b_idx ON accounts_useractivity (created_at DESC);

-- Create AthleteProfile table if not exists
CREATE TABLE IF NOT EXISTS accounts_athleteprofile (
    id BIGSERIAL PRIMARY KEY,
    age INTEGER NOT NULL,
    gender VARCHAR(20) NOT NULL,
    height DOUBLE PRECISION NOT NULL,
    height_unit VARCHAR(5) NOT NULL DEFAULT 'cm',
    weight DOUBLE PRECISION NOT NULL,
    weight_unit VARCHAR(5) NOT NULL DEFAULT 'kg',
    body_type VARCHAR(20) NOT NULL,
    fitness_level VARCHAR(20) NOT NULL,
    primary_sport VARCHAR(100) NOT NULL,
    years_training DOUBLE PRECISION NOT NULL,
    current_performance_baseline TEXT NOT NULL,
    primary_goal VARCHAR(20) NOT NULL,
    goal_timeframe VARCHAR(20) NOT NULL,
    target_event VARCHAR(200) DEFAULT '',
    target_event_date DATE,
    weekly_availability INTEGER NOT NULL,
    preferred_intensity VARCHAR(20) NOT NULL,
    preferred_training_time VARCHAR(20) NOT NULL,
    equipment_access JSONB DEFAULT '[]',
    injury_history TEXT DEFAULT '',
    medical_conditions TEXT DEFAULT '',
    current_activity_level VARCHAR(20) NOT NULL,
    motivation_level INTEGER NOT NULL,
    guidance_preference VARCHAR(20) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id BIGINT NOT NULL UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS accounts_at_user_id_idx ON accounts_athleteprofile (user_id);
CREATE INDEX IF NOT EXISTS accounts_at_fitness_idx ON accounts_athleteprofile (fitness_level);
CREATE INDEX IF NOT EXISTS accounts_at_goal_idx ON accounts_athleteprofile (primary_goal);

-- Mark migrations as applied
INSERT INTO django_migrations (app, name, applied)
VALUES 
    ('accounts', '0008_fix_requested_at_column', NOW()),
    ('accounts', '0009_athleteprofile', NOW()),
    ('accounts', '0010_useractivity', NOW())
ON CONFLICT DO NOTHING;
