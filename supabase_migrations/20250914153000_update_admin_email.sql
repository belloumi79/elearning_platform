-- Update admin email to match the provided user JSON object

UPDATE admins
SET email = 'corinette.arthab3t@gmail.com',
    updated_at = NOW()
WHERE id = 'f81b44cb-4da4-4385-8e21-0dcc37659940';