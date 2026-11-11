#!/bin/bash
# ==============================================================================
# Script: setup_mongo_connection.sh
# Purpose: Create or update Airflow connection 'mongo_default' via Astro CLI
# Host: mongo, Port: 27017, Credentials sourced from .env
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [ -f .env ]; then
  # Sourcing .env
  set -a
  source .env
  set +a
fi

MONGO_HOST="${MONGO_HOST:-mongo}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_USER="${MONGO_INITDB_ROOT_USERNAME:-root}"
MONGO_PASSWORD="${MONGO_INITDB_ROOT_PASSWORD:-rootpassword}"
MONGO_DB="${MONGO_DB:-currency_db}"

echo "Configuring Airflow connection 'mongo_default'..."
echo "Host: $MONGO_HOST, Port: $MONGO_PORT, User: $MONGO_USER, DB: $MONGO_DB"

# Delete connection if already exists
astro dev run connections delete mongo_default 2>/dev/null || true

# Add connection via astro dev run connections add
astro dev run connections add 'mongo_default' \
    --conn-type 'mongodb' \
    --conn-host "$MONGO_HOST" \
    --conn-port "$MONGO_PORT" \
    --conn-login "$MONGO_USER" \
    --conn-password "$MONGO_PASSWORD" \
    --conn-schema "$MONGO_DB" \
    --conn-extra '{"authSource": "admin"}'

echo "Connection 'mongo_default' successfully configured:"
astro dev run connections get mongo_default
