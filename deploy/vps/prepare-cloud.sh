#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env.cloud ]]; then
  echo "Missing .env.cloud. Copy .env.cloud.example and insert the real values." >&2
  exit 1
fi

set -a
source ./.env.cloud
set +a

: "${PROJECTS_DIR:?PROJECTS_DIR is required}"
: "${OPENROUTER_API_KEY:?OPENROUTER_API_KEY is required}"
: "${API_SERVER_KEY:?API_SERVER_KEY is required}"

if [[ "$OPENROUTER_API_KEY" != sk-or-* ]]; then
  echo "OPENROUTER_API_KEY does not have the expected OpenRouter prefix." >&2
  exit 1
fi

if [[ ${#API_SERVER_KEY} -lt 32 ]]; then
  echo "API_SERVER_KEY must contain at least 32 random characters." >&2
  exit 1
fi

if [[ ! -d "$PROJECTS_DIR" ]]; then
  echo "PROJECTS_DIR does not exist: $PROJECTS_DIR" >&2
  exit 1
fi

mkdir -p "${HERMES_DATA_DIR:-./data/hermes-cloud}" "${HERMES_STATE_DIR:-./data/state-cloud}" ../../.hermes

config_target="${HERMES_DATA_DIR:-./data/hermes-cloud}/config.yaml"
if [[ ! -f "$config_target" ]]; then
  install -m 600 config-cloud.yaml.example "$config_target"
fi

docker compose --env-file .env.cloud -f compose-cloud.yaml config --quiet

echo "Cloud VPS configuration is valid."
echo "Start: sudo docker compose --env-file .env.cloud -f compose-cloud.yaml up -d"
echo "Access: ssh -L 8642:127.0.0.1:${HERMES_API_PORT:-8642} hermesadmin@VPS_IP"
