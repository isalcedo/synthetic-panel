#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_LINK="${HOME}/.cursor/skills/synthetic-panel"

mkdir -p "${HOME}/.cursor/skills"

if [[ -e "${SKILL_LINK}" && ! -L "${SKILL_LINK}" ]]; then
  echo "error: ${SKILL_LINK} exists and is not a symlink." >&2
  echo "Move or remove it, then re-run install.sh." >&2
  exit 1
fi

ln -sfn "${REPO_DIR}" "${SKILL_LINK}"
echo "Installed: ${SKILL_LINK} -> ${REPO_DIR}"
echo "Invoke in Cursor with: /synthetic-panel"
