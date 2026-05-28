# Research Report HTML

Turn dense research notes, paper summaries, code walkthroughs, surveys, and
technical reports into premium light single-file HTML documents.

This repository packages the `research-report-html` skill for Codex and Claude
Code. It is the generalized successor to a robotics-focused HTML style: robotics
and embodied AI still work beautifully, but the primary use case is now broader
research communication.

<p>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-black.svg?style=flat-square"></a>
  <a href="skills/research-report-html/SKILL.md"><img alt="Skill" src="https://img.shields.io/badge/skill-research--report--html-2457A6?style=flat-square"></a>
  <a href="examples/a-star-path-planning/a_star_explained.html"><img alt="Examples" src="https://img.shields.io/badge/examples-2-D85F2B?style=flat-square"></a>
</p>

## What It Makes

Use this skill when you want an AI coding agent to generate:

- paper reading maps and literature survey pages
- code walkthroughs with diagrams, snippets, and copyable blocks
- technical reports, study guides, and repo notes
- landmark paper timelines and bibliography-style reading lists
- robotics, embodied AI, computer vision, autonomy, and 3D vision reports

The output is a standalone HTML file with inline CSS. It favors warm paper
surfaces, compact reading maps, restrained blue accents, dense technical cards,
responsive tables, and PrismJS-powered code blocks when code is present.

It is not meant for marketing landing pages, dark cinematic launches, Claude
warm editorial pages, or generic decorative web art.

## Showcase

| Example | What it demonstrates |
| --- | --- |
| [A* grid path planning walkthrough](examples/a-star-path-planning/a_star_explained.html) | Code-first algorithm explanation with visual diagrams, cost function notes, and PrismJS copy buttons. |
| [LingBot-Map paper + code reading report](examples/lingbot-map/LINGBOT_MAP_PAPER_CODE_SUMMARY.html) | Paper/repo synthesis with reading map, module mapping, innovation summary, benchmark tables, and implementation caveats. |

Preview:

![Research Report HTML showcase](docs/screenshots/index-desktop.png)

Open the live showcase at [kbfx1234.github.io/research-report-html](https://kbfx1234.github.io/research-report-html/) or view [index.html](index.html) from the repo.

## Install In Codex

In Codex, ask:

```text
$skill-installer install https://github.com/kbfx1234/research-report-html/tree/main/skills/research-report-html
```

Codex's built-in skill installer can install skills from GitHub repository
paths. If the skill does not appear immediately, restart Codex.

Auditable local install:

```bash
git clone https://github.com/kbfx1234/research-report-html.git
cd research-report-html
bash scripts/install.sh --target codex
```

## Install In Claude Code

Claude Code personal skills live under `~/.claude/skills/<skill-name>/SKILL.md`.

```bash
git clone https://github.com/kbfx1234/research-report-html.git
mkdir -p ~/.claude/skills
cp -R research-report-html/skills/research-report-html ~/.claude/skills/
```

You can also ask Claude Code to install it:

```text
Clone https://github.com/kbfx1234/research-report-html and install the skill folder at skills/research-report-html into ~/.claude/skills/research-report-html. Then verify that /research-report-html is available.
```

## Universal Install Script

Install into both Codex and Claude Code:

```bash
git clone https://github.com/kbfx1234/research-report-html.git
cd research-report-html
bash scripts/install.sh
```

Install one target:

```bash
bash scripts/install.sh --target codex
bash scripts/install.sh --target claude
```

Update an existing install:

```bash
bash scripts/install.sh --target both --force
```

The script copies only `skills/research-report-html/`. It does not install the
example HTML files into your agent skill directories.

## Example Prompts

```text
Use research-report-html to turn this Markdown paper summary into a compact HTML reading map with implementation caveats and benchmark tables.
```

```text
Generate a single-file HTML code walkthrough for this path-planning module. Explain the main loop, data structures, edge cases, and final path reconstruction.
```

```text
Create a research survey HTML page from these paper notes. Use a chronological timeline, contribution taxonomy, and visible paper links.
```

```text
Make a polished technical report HTML for this repo README and architecture notes. Include a module map, data flow, risks, and reproduction checklist.
```

```text
Build a robotics research report page from this paper and code summary. Keep it light, dense, and researcher-facing, not a product homepage.
```

## Repository Layout

```text
skills/research-report-html/       # Installable Codex / Claude Code skill
examples/                          # Showcase outputs
docs/screenshots/                  # README preview screenshots
scripts/install.sh                 # Local installer for Codex and Claude Code
scripts/validate_repo.py           # Structural and privacy validation
```

## Validate

```bash
python3 scripts/validate_repo.py
```

The validator checks required files, skill frontmatter, HTML completeness,
allowed external URLs, example path scrubbing, and install-script simulation.

## Release Notes

`v0.1.0` is a direct skill-folder release for Codex and Claude Code. Marketplace
or plugin packaging can be added later if it becomes useful.

## License

MIT. See [LICENSE](LICENSE).
