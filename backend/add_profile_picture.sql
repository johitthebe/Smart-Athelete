-- Add profile_picture field to accounts_user table
ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(100) NULL;

-- Mark migration as applied
INSERT INTO django_migrations (app, name, applied)
VALUES ('accounts', '0011_user_profile_picture', NOW())
ON CONFLICT DO NOTHING;
