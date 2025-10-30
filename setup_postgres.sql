-- PostgreSQL Setup Script
-- Run this as the postgres superuser

-- Create the database
CREATE DATABASE django_ai_journal;

-- Create the user
CREATE USER django_user WITH PASSWORD 'django_pass_2024';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE django_ai_journal TO django_user;

-- Make the user a superuser (for Django migrations)
ALTER USER django_user CREATEDB;

-- Connect to the new database and grant schema privileges
\c django_ai_journal;
GRANT ALL ON SCHEMA public TO django_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO django_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO django_user;

-- Show confirmation
SELECT 'Database and user created successfully!' as status;