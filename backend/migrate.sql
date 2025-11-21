-- Migration: Add missing columns to employees and skill_events tables

-- Add position column to employees table
ALTER TABLE employees ADD COLUMN IF NOT EXISTS position VARCHAR(100);

-- Add notes column to skill_events table
ALTER TABLE skill_events ADD COLUMN IF NOT EXISTS notes TEXT;

-- Add unique constraint to skill_events
ALTER TABLE skill_events DROP CONSTRAINT IF EXISTS skill_events_employee_id_skill_id_event_date_key;
ALTER TABLE skill_events ADD CONSTRAINT skill_events_employee_id_skill_id_event_date_key UNIQUE (employee_id, skill_id, event_date);

SELECT 'Migration complete!' AS status;
