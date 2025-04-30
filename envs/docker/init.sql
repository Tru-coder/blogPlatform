-- init.sql
\set ON_ERROR_STOP on

SELECT 'CREATE DATABASE test_blog_platform'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test_blog_platform')\gexec