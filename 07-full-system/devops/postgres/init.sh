#!/bin/bash
set -e

# Create auth database (tables created by alembic at auth_service startup)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE auth;
EOSQL

# Create movies database and load content schema + data
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE movies;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname movies < /docker-entrypoint-initdb.d/database_dump.sql
