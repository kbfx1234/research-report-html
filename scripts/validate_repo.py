#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "research-report-html"

REQUIRED_PATHS = [
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "index.html",
    "skills/research-report-html/SKILL.md",
    "skills/research-report-html/LICENSE.txt",
    "skills/research-report-html/agents/openai.yaml",
    "skills/research-report-html/references/research-report-style.md",
    "skills/research-report-html/references/code-blocks-prism.md",
    "skills/research-report-html/references/robotics-product-variant.md",
    "examples/a-star-path-planning/a_star_explained.html",
    "examples/lingbot-map/LINGBOT_MAP_PAPER_CODE_SUMMARY.html",
    "examples/lingbot-map/LINGBOT_MAP_PAPER_CODE_SUMMARY.md",
    "scripts/install.sh",
    ".github/workflows/validate.yml",
]

SENSITIVE_PATTERNS = [
    r"/Users/mi",
    r"/private/",
    r"localhost",
    r"127\.0\.0\.1",
    r"GITHUB_TOKEN",
    r"ANTHROPIC_API_KEY",
    r"OPENAI_API_KEY",
    r"api[_-]?key\s*[:=]",
    r"password\s*[:=]",
    r"secret\s*[:=]",
]

ALLOWED_EXTERNAL_PREFIXES = (
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
    "https://cdn.jsdelivr.net/npm/prismjs@1.30.0/",
    "https://github.com/",
    "https://img.shields.io/",
    "https://developers.openai.com/",
    "https://code.claude.com/",
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_paths() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("Missing required paths:\n" + "\n".join(f"- {path}" for path in missing))


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        fail("SKILL.md frontmatter is not closed")
    raw = text[4:end]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            fail(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def check_skill() -> None:
    skill = read_text(SKILL_DIR / "SKILL.md")
    frontmatter = parse_frontmatter(skill)
    if frontmatter.get("name") != "research-report-html":
        fail("SKILL.md frontmatter name must be research-report-html")
    description = frontmatter.get("description", "")
    if "paper reading maps" not in description or "代码研读" not in description:
        fail("SKILL.md description is missing core trigger phrases")
    if set(frontmatter) != {"name", "description"}:
        fail("SKILL.md frontmatter should contain only name and description")
    if len(skill.splitlines()) > 180:
        fail("SKILL.md is no longer compact; move detail into references/")
    for reference in [
        "references/research-report-style.md",
        "references/code-blocks-prism.md",
        "references/robotics-product-variant.md",
    ]:
        if reference not in skill:
            fail(f"SKILL.md does not link {reference}")


def check_html(path: Path) -> None:
    html = read_text(path)
    lower = html.lower()
    if "<!doctype html" not in lower:
        fail(f"{path.relative_to(ROOT)} is missing <!DOCTYPE html>")
    if '<meta name="viewport"' not in lower:
        fail(f"{path.relative_to(ROOT)} is missing viewport meta")
    if "<style" not in lower or "</style>" not in lower:
        fail(f"{path.relative_to(ROOT)} is missing inline style")
    if "</html>" not in lower:
        fail(f"{path.relative_to(ROOT)} is missing closing </html>")

    urls = re.findall(r"https?://[^\"'()\s<>]+", html)
    for url in urls:
        if not url.startswith(ALLOWED_EXTERNAL_PREFIXES):
            fail(f"{path.relative_to(ROOT)} has non-whitelisted external URL: {url}")


def check_sensitive_patterns() -> None:
    scan_extensions = {".md", ".html", ".yaml", ".yml", ".sh", ".py", ".txt"}
    for path in ROOT.rglob("*"):
        if path.is_dir() or ".git" in path.parts:
            continue
        if path == ROOT / "scripts" / "validate_repo.py":
            continue
        if path.suffix not in scan_extensions:
            continue
        text = read_text(path)
        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                fail(f"Sensitive or local pattern {pattern!r} found in {path.relative_to(ROOT)}")


def check_install_script() -> None:
    script = ROOT / "scripts" / "install.sh"
    if not os.access(script, os.X_OK):
        fail("scripts/install.sh must be executable")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        codex_dir = tmp_path / "codex-skills"
        claude_dir = tmp_path / "claude-skills"
        subprocess.run(
            [
                str(script),
                "--target",
                "both",
                "--codex-dir",
                str(codex_dir),
                "--claude-dir",
                str(claude_dir),
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for base in (codex_dir, claude_dir):
            installed = base / "research-report-html"
            for relative in [
                "SKILL.md",
                "references/research-report-style.md",
                "agents/openai.yaml",
            ]:
                if not (installed / relative).exists():
                    fail(f"Install script did not copy {relative} into {base}")

        if shutil.which("bash") is None:
            fail("bash is required for scripts/install.sh")


def main() -> None:
    check_required_paths()
    check_skill()
    for relative in [
        "index.html",
        "examples/a-star-path-planning/a_star_explained.html",
        "examples/lingbot-map/LINGBOT_MAP_PAPER_CODE_SUMMARY.html",
    ]:
        check_html(ROOT / relative)
    check_sensitive_patterns()
    check_install_script()
    print("validate_repo.py: ok")


if __name__ == "__main__":
    main()
