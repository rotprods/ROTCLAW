#!/usr/bin/env bash
set -euo pipefail

STATE_ROOT="${ROTCLAW_STATE_ROOT:-$HOME/.local/share/rotclaw-node01}"
CONFIG_ROOT="${ROTCLAW_CONFIG_ROOT:-$HOME/.config/rotclaw}"
ENV_FILE="$CONFIG_ROOT/node01.env"
UNIT_ROOT="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT_FILE="$UNIT_ROOT/rotclaw-router.service"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY_RUN="${ROTCLAW_SERVICE_DRY_RUN:-0}"

command -v systemctl >/dev/null 2>&1 || { echo "systemctl is required" >&2; exit 2; }
[[ -f "$ENV_FILE" ]] || { echo "missing $ENV_FILE; run scripts/node01_bootstrap.sh first" >&2; exit 2; }
[[ -x "$STATE_ROOT/start-router.sh" ]] || { echo "missing $STATE_ROOT/start-router.sh; run bootstrap first" >&2; exit 2; }

mkdir -p "$UNIT_ROOT"
chmod 700 "$UNIT_ROOT" 2>/dev/null || true

cat > "$UNIT_FILE" <<EOF
[Unit]
Description=ROTCLAW Node01 model router
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$REPO_ROOT
ExecStart=$STATE_ROOT/start-router.sh
Restart=on-failure
RestartSec=3
TimeoutStopSec=15
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$STATE_ROOT $CONFIG_ROOT
RestrictSUIDSGID=true
LockPersonality=true

[Install]
WantedBy=default.target
EOF
chmod 600 "$UNIT_FILE"

if command -v systemd-analyze >/dev/null 2>&1; then
  systemd-analyze verify "$UNIT_FILE"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "NODE01_SERVICE_DRY_RUN_PASS $UNIT_FILE"
  exit 0
fi

systemctl --user daemon-reload
systemctl --user enable --now rotclaw-router.service
systemctl --user is-enabled rotclaw-router.service
systemctl --user is-active rotclaw-router.service

echo "installed and started $UNIT_FILE"
echo "status: systemctl --user status rotclaw-router.service"
echo "logs:   journalctl --user -u rotclaw-router.service"
