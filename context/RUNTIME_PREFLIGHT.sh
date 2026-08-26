#!/usr/bin/env bash
set -euo pipefail
printf 'captured_at_utc=%s\n' "$(date -u +%FT%TZ)"
printf 'hostname=%s\n' "$(hostname)"
printf 'kernel=%s\n' "$(uname -a)"
printf 'cpu_visible=%s\n' "$(nproc --all)"
printf 'cpu_max=%s\n' "$(cat /sys/fs/cgroup/cpu.max 2>/dev/null || echo unknown)"
printf 'memory_max=%s\n' "$(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo unknown)"
printf 'memory_current=%s\n' "$(cat /sys/fs/cgroup/memory.current 2>/dev/null || echo unknown)"
printf 'disk=%s\n' "$(df -h / | tail -1 | tr -s ' ')"
printf 'git=%s\n' "$(git --version 2>/dev/null || echo missing)"
printf 'python=%s\n' "$(python3 --version 2>/dev/null || echo missing)"
printf 'node=%s\n' "$(node --version 2>/dev/null || echo missing)"
printf 'npm=%s\n' "$(npm --version 2>/dev/null || echo missing)"
printf 'docker=%s\n' "$(command -v docker || echo missing)"
printf 'openclaw=%s\n' "$(command -v openclaw || echo missing)"
grep -E 'CapEff|NoNewPrivs|Seccomp' /proc/self/status || true
