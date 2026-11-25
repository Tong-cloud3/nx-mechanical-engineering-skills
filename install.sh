#!/usr/bin/env bash
set -euo pipefail

TARGET="all"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target|-t)
      TARGET="${2:-}"
      shift 2
      ;;
    *)
      echo "Usage: $0 [--target antigravity|codex|claude|all]"
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_SKILLS="$SCRIPT_DIR/skills"

install_to() {
  local label="$1"
  local dest="$2"
  mkdir -p "$dest"
  for sdir in "$REPO_SKILLS"/*/; do
    local sname
    sname="$(basename "$sdir")"
    rm -rf "$dest/$sname"
    cp -R "$sdir" "$dest/$sname"
  done
  echo "[OK] Installed skills for $label -> $dest"
}

case "$TARGET" in
  antigravity) install_to "Antigravity" "$HOME/.gemini/config/skills" ;;
  codex)       install_to "Codex"       "$HOME/.codex/skills" ;;
  claude)      install_to "Claude Code" "$HOME/.claude/skills" ;;
  all)
    install_to "Antigravity" "$HOME/.gemini/config/skills"
    install_to "Codex"       "$HOME/.codex/skills"
    install_to "Claude Code" "$HOME/.claude/skills"
    ;;
  *)
    echo "Invalid target: $TARGET (expected: antigravity|codex|claude|all)"
    exit 1
    ;;
esac

echo "Done! Start a new conversation to load the installed skills."
