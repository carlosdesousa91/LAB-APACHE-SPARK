#!/usr/bin/env bash
# Per-boot: start Docker daemon and bring up Spark + Elasticsearch labs.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  exec sudo -E bash "${BASH_SOURCE[0]}" "$@"
fi

# Prefer the Cloud Agent checkout root; fall back to repo-relative resolution.
if [ -d /workspace/SPARK ] && [ -d /workspace/ELASTICSEARCH ]; then
  ROOT=/workspace
elif [ -n "${CURSOR_WORKSPACE:-}" ] && [ -d "${CURSOR_WORKSPACE}/SPARK" ]; then
  ROOT="${CURSOR_WORKSPACE}"
else
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

mkdir -p /etc/docker
if [ ! -f /etc/docker/daemon.json ]; then
  cat > /etc/docker/daemon.json <<'EOF'
{
  "storage-driver": "fuse-overlayfs",
  "iptables": true,
  "ip6tables": false
}
EOF
fi

update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || true
update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy 2>/dev/null || true

chmod 666 /var/run/docker.sock 2>/dev/null || true

if ! docker info >/dev/null 2>&1; then
  pkill dockerd 2>/dev/null || true
  sleep 1
  log=/var/tmp/dockerd-start.log
  rm -f "$log"
  dockerd >"$log" 2>&1 &
  for _ in $(seq 1 60); do
    chmod 666 /var/run/docker.sock 2>/dev/null || true
    if docker info >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

chmod 666 /var/run/docker.sock 2>/dev/null || true

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon failed to start" >&2
  tail -50 /var/tmp/dockerd-start.log >&2 || true
  exit 1
fi

# Spark cluster
cd "$ROOT/SPARK"
docker compose up -d
for _ in $(seq 1 60); do
  running=$(docker compose ps --status running -q | wc -l)
  if [ "$running" -ge 4 ]; then
    break
  fi
  sleep 2
done

# Elasticsearch + Kibana
cd "$ROOT/ELASTICSEARCH"
docker compose up -d
for _ in $(seq 1 90); do
  if curl -sf http://127.0.0.1:9200 >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Labs ready:"
echo "  Spark Master UI: http://localhost:8080"
echo "  Elasticsearch:   http://localhost:9200"
echo "  Kibana:          http://localhost:5601"
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
