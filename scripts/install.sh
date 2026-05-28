#!/usr/bin/env bash
set -euo pipefail

target="both"
force="false"
codex_dir="${CODEX_HOME:-$HOME/.codex}/skills"
claude_dir="$HOME/.claude/skills"

usage() {
  printf '%s\n' "Usage: scripts/install.sh [--target codex|claude|both] [--force] [--codex-dir DIR] [--claude-dir DIR]"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      target="${2:-}"
      shift 2
      ;;
    --force)
      force="true"
      shift
      ;;
    --codex-dir)
      codex_dir="${2:-}"
      shift 2
      ;;
    --claude-dir)
      claude_dir="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$target" in
  codex|claude|both) ;;
  *)
    printf 'Invalid --target: %s\n' "$target" >&2
    usage >&2
    exit 2
    ;;
esac

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH= cd -- "$script_dir/.." && pwd)"
source_dir="$repo_root/skills/research-report-html"

if [ ! -f "$source_dir/SKILL.md" ]; then
  printf 'Could not find skill source at %s\n' "$source_dir" >&2
  exit 1
fi

install_one() {
  destination_root="$1"
  destination="$destination_root/research-report-html"

  mkdir -p "$destination_root"

  if [ -e "$destination" ]; then
    if [ "$force" != "true" ]; then
      printf 'Destination exists: %s\n' "$destination" >&2
      printf 'Re-run with --force to replace it.\n' >&2
      exit 1
    fi
    rm -rf "$destination"
  fi

  cp -R "$source_dir" "$destination"
  printf 'Installed research-report-html to %s\n' "$destination"
}

if [ "$target" = "codex" ] || [ "$target" = "both" ]; then
  install_one "$codex_dir"
fi

if [ "$target" = "claude" ] || [ "$target" = "both" ]; then
  install_one "$claude_dir"
fi

printf 'Done. Restart Codex or Claude Code if the new skill is not visible yet.\n'
