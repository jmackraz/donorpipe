#!/usr/bin/env bash
# One-time bootstrap for a fresh Lightsail instance.
# Prerequisites (done manually before running):
#   - Static IP attached, ports 80+443 open in Lightsail firewall
#   - DNS A record donorpipe.trickybit.com → static IP (propagated)
#   - SSH key access as ubuntu@<host>
#   - prod_config.json and .env ready locally

set -euo pipefail

HOST="${1:?Usage: provision.sh <host>}"

# 1. Install Docker + certbot
ssh ubuntu@$HOST "curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker ubuntu && sudo apt-get install -y certbot"

# 2. Dirs and config
ssh ubuntu@$HOST "mkdir -p ~/donorpipe/nginx ~/donorpipe/data"
scp prod_config.json ubuntu@$HOST:~/donorpipe/config.json
scp .env ubuntu@$HOST:~/donorpipe/.env          # DONORPIPE_JWT_SECRET

# 3. Get TLS cert (certbot standalone; no containers running yet)
ssh ubuntu@$HOST "sudo certbot certonly --standalone -d donorpipe.trickybit.com"

# 4. Initial deploy
PROD=1 DPIPE_HOST=ubuntu@$HOST ./scripts/deploy.sh

# 5. Renewal cron
ssh ubuntu@$HOST "echo '0 3 * * * root certbot renew --quiet && docker compose -f ~/donorpipe/docker-compose.yml -f ~/donorpipe/docker-compose.prod.yml exec nginx nginx -s reload' | sudo tee /etc/cron.d/certbot-renew"

echo "Done. Visit https://donorpipe.trickybit.com"
