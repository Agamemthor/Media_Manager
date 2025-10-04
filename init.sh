#!/bin/bash
set -e

# Run all migration files in order
for migration in /sql/migrations/*.sql; do
    echo "Running migration: $migration"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$migration"
done
c