-- Create database and user for local development
-- Run this with: psql -U postgres -f create_local_db.sql

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE juris_ia'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'juris_ia')\gexec

-- Create user if it doesn't exist
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'juris_ia_user') THEN
      CREATE USER juris_ia_user WITH PASSWORD 'changeme123';
   END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE juris_ia TO juris_ia_user;

-- Show result
\echo 'Database setup complete!'
\echo 'Database: juris_ia'
\echo 'User: juris_ia_user'
\echo 'Password: changeme123'
