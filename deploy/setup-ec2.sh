#!/bin/bash
# CurfewBot — EC2 first-time setup script
# Target: Amazon Linux 2023 (AL2023) on t2.micro free tier
#
# Usage:
#   chmod +x deploy/setup-ec2.sh
#   ./deploy/setup-ec2.sh

set -euo pipefail

echo "=== CurfewBot EC2 Setup ==="
echo ""

# 1. Update system packages
echo "[1/5] Updating system packages..."
sudo dnf update -y

# 2. Install Docker
echo "[2/5] Installing Docker..."
sudo dnf install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# 3. Install Docker Compose plugin
echo "[3/5] Installing Docker Compose plugin..."
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Verify installation
sudo docker compose version

# 4. Install git (if not present)
echo "[4/5] Ensuring git is installed..."
sudo dnf install -y git

# 5. Create .env file
echo "[5/5] Setting up environment..."
echo ""

if [ ! -f .env ]; then
    echo "No .env file found. Let's create one."
    echo ""
    read -rp "Enter your Discord BOT_TOKEN: " bot_token
    read -rp "Enter your Discord GUILD_ID: " guild_id

    printf 'BOT_TOKEN=%s\nGUILD_ID=%s\n' "$bot_token" "$guild_id" > .env
    chmod 600 .env

    echo ".env file created (permissions set to owner-only)."
else
    echo ".env file already exists, skipping."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "IMPORTANT: Log out and back in for docker group to take effect:"
echo "  exit"
echo "  ssh -i your-key.pem ec2-user@<your-ec2-ip>"
echo ""
echo "Then start the bot:"
echo "  cd $(pwd)"
echo "  docker compose up -d"
echo ""
echo "Check logs:"
echo "  docker compose logs -f"
echo ""
echo "Verify health:"
echo "  curl http://localhost:8080/health"
