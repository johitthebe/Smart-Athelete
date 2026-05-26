-- Add profile_picture column to accounts_user table
-- Run this if migrations fail

-- Check if column exists first
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='accounts_user' 
        AND column_name='profile_picture'
    ) THEN
        -- Add the column
        ALTER TABLE accounts_user 
        ADD COLUMN profile_picture VARCHAR(100) NULL;
        
        RAISE NOTICE 'Column profile_picture added successfully';
    ELSE
        RAISE NOTICE 'Column profile_picture already exists';
    END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'accounts_user' 
AND column_name = 'profile_picture';
