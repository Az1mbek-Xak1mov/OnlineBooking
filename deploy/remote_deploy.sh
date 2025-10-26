#!/usr/bin/env bash
set -euo pipefail

# Usage: remote_deploy.sh <image> <compose_dir>
# Expects that the remote host has docker and docker-compose installed and that
# the caller has SSH access.

IMAGE=${1:-}
REMOTE_DIR=${2:-/opt/onlinebooking}

if [ -z "$IMAGE" ]; then
  echo "Usage: $0 <image> [remote_dir]"
  exit 2
fi

echo "Creating remote dir and pulling image"
ssh -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "
  mkdir -p $REMOTE_DIR && cd $REMOTE_DIR
  docker pull $IMAGE
  cat > docker-compose.yml <<'YAML'
version: '3.8'
services:
  web:
    image: $IMAGE
    restart: always
    ports:
      - '8000:8000'
    environment:
      - DJANGO_DEBUG=False
      - POSTGRES_HOST=db
YAML
  docker compose up -d --remove-orphans
"

echo "Deployed $IMAGE to $SSH_HOST:$REMOTE_DIR"
