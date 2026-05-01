BEGIN;
DELETE FROM users
WHERE email = 'maimahmoudhasan12345@gmail.com';
COMMIT;
-- -- -- -- SELECT email FROM users 
-- -- -- -- WHERE email = 'Sehamzakaria1974@gmail.com';
-- SELECT *
-- FROM doctors d
-- -- JOIN users u ON d.doctor_id = u.user_id
-- WHERE d.full_name = 'dr.basmala';



-- -- -- Enable UUID generation (usually already enabled in Supabase)
-- -- -- CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -- -- DO $$
-- -- -- DECLARE
-- -- --     new_user_id UUID;
-- -- -- BEGIN
-- -- --     -- Check if admin already exists
-- -- --     IF NOT EXISTS (
-- -- --         SELECT 1 FROM users WHERE email = 'admin@hospital.com'
-- -- --     ) THEN

-- -- --         -- Insert user
-- -- --         INSERT INTO users (
-- -- --             user_id,
-- -- --             email,
-- -- --             password_hash,
-- -- --             role,
-- -- --             full_name,
-- -- --             is_active,
-- -- --             email_verified
-- -- --         )
-- -- --         VALUES (
-- -- --             gen_random_uuid(),
-- -- --             'admin@hospital.com',
-- -- --             '$2b$12$/7DG5hFiQep6Q61kQKuP9uJDeGabTxL/XFEKa64VuO9DYTwjC.0Py', -- 🔴 replace this
-- -- --             'admin',
-- -- --             'System Admin',
-- -- --             TRUE,
-- -- --             TRUE
-- -- --         )
-- -- --         RETURNING user_id INTO new_user_id;

-- -- --         -- Insert admin profile
-- -- --         INSERT INTO admin (admin_id)
-- -- --         VALUES (new_user_id);

-- -- --         RAISE NOTICE 'Admin created successfully';

-- -- --     ELSE
-- -- --         RAISE NOTICE 'Admin already exists';
-- -- --     END IF;

-- -- -- END $$;





-- -- -- ─────────────────────────────────────────────
-- -- -- Seed Admin User
-- -- -- ─────────────────────────────────────────────

-- -- -- Step 1: Insert into users table
-- -- INSERT INTO users (
-- --     user_id,
-- --     email,
-- --     password_hash,
-- --     role,
-- --     full_name,
-- --     is_active,
-- --     email_verified
-- -- )
-- -- VALUES (
-- --     gen_random_uuid(),          -- PostgreSQL (or replace with your DB UUID function)
-- --     'admin@hospital.com',
-- --     '$2b$12$/7DG5hFiQep6Q61kQKuP9uJDeGabTxL/XFEKa64VuO9DYTwjC.0Py',
-- --     'admin',
-- --     'System Admin',
-- --     TRUE,
-- --     TRUE
-- -- );

-- -- -- Step 2: Insert into admin table
-- -- INSERT INTO admin (
-- --     admin_id
-- -- )
-- -- SELECT user_id
-- -- FROM users
-- -- WHERE email = 'admin@hospital.com';




-- -- ─────────────────────────────────────────────
-- -- Enable UUID support (needed for gen_random_uuid)
-- -- ─────────────────────────────────────────────
-- CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -- ─────────────────────────────────────────────
-- -- Create admin safely (only if not exists)
-- -- ─────────────────────────────────────────────
-- DO $$
-- DECLARE
--     new_user_id UUID;
-- BEGIN
--     -- Check if admin already exists
--     IF NOT EXISTS (
--         SELECT 1 FROM users WHERE email = 'admin@hospital.com'
--     ) THEN

--         -- Insert into users table
--         INSERT INTO users (
--             user_id,
--             email,
--             password_hash,
--             role,
--             full_name,
--             is_active,
--             email_verified,
--             created_at
--         )
--         VALUES (
--             gen_random_uuid(),
--             'admin@hospital.com',
--             '$2b$12$/7DG5hFiQep6Q61kQKuP9uJDeGabTxL/XFEKa64VuO9DYTwjC.0Py', -- 🔴 replace this
--             'admin',  -- must match enum value
--             'System Admin',
--             TRUE,
--             TRUE,
--             NOW()
--         )
--         RETURNING user_id INTO new_user_id;

--         -- Insert into admins table (1-1 relationship)
--         INSERT INTO admins (admin_id)
--         VALUES (new_user_id);

--         RAISE NOTICE '✅ Admin created successfully';

--     ELSE
--         RAISE NOTICE '⚠️ Admin already exists';
--     END IF;

-- END $$;