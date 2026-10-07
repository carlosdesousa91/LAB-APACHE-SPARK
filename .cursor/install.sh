#!/usr/bin/env bash
# Idempotent Cloud Agent install: ensure Docker tooling and pre-pull lab images.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

ensure_docker_packages() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "Docker already installed: $(docker --version)"
    return 0
  fi

  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg \
    -o Dpkg::Options::="--force-confnew"
  apt-get install -y -qq fuse-overlayfs iptables \
    -o Dpkg::Options::="--force-confnew" || true

  install -m 0755 -d /etc/apt/keyrings
  if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
  fi

  if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable" \
      > /etc/apt/sources.list.d/docker.list
  fi

  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
}

configure_docker() {
  mkdir -p /etc/docker
  cat > /etc/docker/daemon.json <<'EOF'
{
  "storage-driver": "fuse-overlayfs",
  "iptables": true,
  "ip6tables": false
}
EOF
  update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || true
  update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy 2>/dev/null || true
  usermod -aG docker ubuntu 2>/dev/null || true
}

ensure_dockerd() {
  chmod 666 /var/run/docker.sock 2>/dev/null || true
  if docker info >/dev/null 2>&1; then
    return 0
  fi

  # Start daemon only long enough to refresh images; start.sh owns per-boot lifecycle.
  pkill dockerd 2>/dev/null || true
  sleep 1
  local log=/var/tmp/dockerd-install.log
  rm -f "$log"
  dockerd >"$log" 2>&1 &
  for _ in $(seq 1 60); do
    chmod 666 /var/run/docker.sock 2>/dev/null || true
    if docker info >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Failed to start dockerd during install" >&2
  tail -50 "$log" >&2 || true
  exit 1
}

if [ "$(id -u)" -ne 0 ]; then
  exec sudo -E bash "${BASH_SOURCE[0]}" "$@"
fi

ensure_docker_packages
configure_docker
ensure_dockerd

docker pull apache/spark:3.5.5-python3
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.17.0
docker pull docker.elastic.co/kibana/kibana:8.17.0

echo "Install complete."
docker --version
docker compose version
