-- Insert admin user based on provided JSON object
-- User details from auth response:
-- id: [auth_user_id_placeholder]
-- email: corinette.arthab3t@gmail.com
-- name: coordinateur.atta3aouen
-- profile_type: admin
-- profile_id: f81b44cb-4da4-4385-8e21-0dcc37659940
-- created_at: 2025-05-18T18:58:52.188522+00:00

-- Note: Replace [auth_user_id_placeholder] with the actual auth.users.id value

INSERT INTO admins (id, user_id, email, created_at, updated_at)
VALUES (
    'f81b44cb-4da4-4385-8e21-0dcc37659940',
    '[auth_user_id_placeholder]',  -- Replace with actual auth user ID
    'corinette.arthab3t@gmail.com',
    '2025-05-18T18:58:52.188522+00:00'::timestamptz,
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    user_id = EXCLUDED.user_id,
    updated_at = NOW();