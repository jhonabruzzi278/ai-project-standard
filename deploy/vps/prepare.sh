#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "Missing deploy/vps/.env. Copy .env.example and insert real values." >&2
  exit 1
fi

set -a
source ./.env
set +a

: "${PROJECTS_DIR:?PROJECTS_DIR is required}"
: "${API_SERVER_KEY:?API_SERVER_KEY is required}"

if [[ ${#API_SERVER_KEY} -lt 32 ]] || [[ "$API_SERVER_KEY" == replace-* ]]; then
  echo "API_SERVER_KEY must be a random secret of at least 32 characters." >&2
  exit 1
fi

if [[ ! -d "$PROJECTS_DIR" ]]; then
  echo "PROJECTS_DIR does not exist: $PROJECTS_DIR" >&2
  exit 1
fi

mkdir -p "${HERMES_DATA_DIR:-./data/hermes}" "${HERMES_STATE_DIR:-./data/state}" "${OLLAMA_DATA_DIR:-./data/ollama}"

config_target="${HERMES_DATA_DIR:-./data/hermes}/config.yaml"
if [[ ! -f "$config_target" ]]; then
  install -m 600 config.yaml.example "$config_target"
fi

docker compose --env-file .env -f compose.yaml config --quiet

echo "VPS configuration is valid. Start with: docker compose --env-file .env -f compose.yaml up -d"
echo "Connect securely with an SSH tunnel: ssh -L 8642:127.0.0.1:${HERMES_API_PORT:-8642} user@vps"
