# Hermes free-cloud profile for a 4 GB VPS

This is the recommended test deployment for a VPS with 2 vCPU, 4 GB RAM and 80 GB disk. Ollama is not installed on the VPS. Hermes Agent uses OpenRouter's free-model router and keeps project files mounted read-only.

The container is limited to 768 MB RAM, 0.75 CPU, 256 processes, a 128 MB `/tmp`, 64 MB `/var/tmp`, an executable 64 MB `/run` for s6-overlay, and three rotated 10 MB Docker log files. The host should have at least 2 GB of swap configured before starting this profile when it shares the VPS with production services.

## Free model routing

The configured model is `openrouter/free`. OpenRouter selects an available free model that supports the request's required capabilities, including tool calling. Selection can change between requests.

The configuration has no paid fallback. Provider routing rejects providers that declare data collection. This privacy filter can reduce availability; do not weaken it for repositories containing private code without reviewing the provider policy.

Free models have low rate limits, variable latency and no production availability guarantee. Use this profile for initial testing and low-volume analysis. A deep AI-DLC run can consume several model requests because each tool round is a separate inference call.

## Required credential replacement

If an OpenRouter key has been pasted into chat, code, logs or a ticket, revoke it immediately and create a new dedicated key. Never reuse the exposed key.

Required credentials:

1. SSH key for the `hermesadmin` VPS user.
2. A fresh dedicated `OPENROUTER_API_KEY` from `https://openrouter.ai/keys`.
3. Random `API_SERVER_KEY` generated on the VPS with `openssl rand -hex 32`.

Optional credentials:

- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USERS`.
- Read-only Git deploy key for private repositories.
- S3-compatible credentials for encrypted backups.

## Deploy after the host is hardened

```bash
cd deploy/vps
cp .env.cloud.example .env.cloud
chmod 600 .env.cloud
nano .env.cloud
chmod +x prepare-cloud.sh
sudo ./prepare-cloud.sh
sudo docker compose --env-file .env.cloud -f compose-cloud.yaml up -d
sudo docker compose --env-file .env.cloud -f compose-cloud.yaml ps
sudo docker compose --env-file .env.cloud -f compose-cloud.yaml logs --tail=100 hermes
```

The Hermes API is bound to VPS loopback only. Reach it from the local PC with an SSH tunnel:

```powershell
ssh -o IdentitiesOnly=yes -i "<SSH_KEY_PATH>" -p <SSH_PORT> -L 8642:127.0.0.1:8642 hermesadmin@VPS_IP
```

Do not open ports 8642 or 11434 in either the provider firewall or UFW.
