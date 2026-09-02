# Deploy Hermes AI-DLC on a VPS

This deployment runs the complete Hermes Agent process in Docker. The project directory is mounted read-only, the rules pack is mounted read-only, and generated harness state is stored separately.

## Recommended baseline

- Ubuntu 24.04 LTS or another current Linux distribution.
- Docker Engine with Compose v2.
- At least 8 vCPU, 32 GB RAM, and 100 GB SSD for CPU inference with `qwen3.5:9b`.
- A supported NVIDIA GPU is optional but strongly improves latency. Size the GPU and model after testing the real workload.
- SSH access by key; disable password login after recovery access has been verified.

## Prepare

```bash
cd deploy/vps
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
# Put the generated value in API_SERVER_KEY, then edit PROJECTS_DIR.
chmod +x prepare.sh
./prepare.sh
```

Review `data/hermes/config.yaml` before starting. The API binds only to VPS loopback, not the public internet.

## Start and verify

```bash
docker compose --env-file .env -f compose.yaml up -d
docker compose --env-file .env -f compose.yaml ps
docker compose --env-file .env -f compose.yaml logs --tail=100 hermes
curl -H "Authorization: Bearer $API_SERVER_KEY" http://127.0.0.1:8642/v1/models
```

From the local PC, create an SSH tunnel:

```bash
ssh -L 8642:127.0.0.1:8642 vps-user@vps-host
```

Do not open ports `8642` or `11434` in the public firewall. Ollama is reachable only on the internal Docker network; Hermes is reachable through the SSH tunnel.

## Optional Telegram

Create a Telegram bot with BotFather and obtain your numeric Telegram user ID. Put `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USERS` in `.env`, then change `platforms.telegram.enabled` to `true` in `data/hermes/config.yaml` and restart Hermes.

Never use `GATEWAY_ALLOW_ALL_USERS=true` on an agent that can inspect real projects.

## Credentials

Required:

1. VPS SSH host/IP, SSH port, non-root sudo username, and the matching private key on the administrator's PC.
2. `API_SERVER_KEY`, generated on the VPS with `openssl rand -hex 32`.
3. Read-only Git deploy keys or fine-grained tokens only if the VPS must clone private repositories.

Optional:

- Telegram bot token plus allowed numeric user IDs.
- OpenRouter API key for a cloud fallback.
- Domain/DNS provider credentials only if a public HTTPS endpoint is intentionally added later.
- S3-compatible access key and secret for encrypted off-site backups.
- Container registry token only if replacing the public images with private custom images.

Ollama requires no API credential while it remains on the private Docker network. Do not place SSH private keys, Git tokens, `.env`, or backup secrets inside this repository.

## Production gates still requiring the operator

- Pin image tags or digests after testing instead of leaving `latest`.
- Confirm VPS hardware and model latency.
- Configure encrypted backups and test restoration.
- Apply OS security updates, firewall policy, SSH hardening, monitoring, and disk alerts.
- Run a read-only analysis against a copied/non-critical project before mounting the full project collection.
