---
name: research-report-html
description: Generate premium light single-file HTML research reports, paper reading maps, code walkthroughs, surveys, study guides, technical reports, and citation-heavy notes. Use for 科研报告 HTML, 论文解读, 代码研读, paper reading map, research survey, landmark paper list, technical documentation, robotics/embodied AI reports, and polished static HTML reading pages.
---

Create polished, researcher-facing single-file HTML documents from papers,
code notes, technical reports, literature surveys, reading lists, and study
guides. Default to a restrained light research report, not a product landing
page.

## Output Contract

- Produce one complete HTML document with all project CSS in one inline
  `<style>` block.
- Preserve the source material's meaning, section order, citations, code paths,
  paper titles, authors, years, links, and caveats unless the user asks for a
  rewrite.
- Use only light surfaces by default. Avoid dark cinematic pages, Claude-style
  cream/terracotta editorial pages, decorative blobs, generic gradient orbs, and
  copied brand assets.
- Use no JavaScript except for code highlighting/copy buttons, or explicit
  user-requested interactivity.
- Verify the final page at desktop and mobile widths when possible. The page
  must avoid horizontal scrolling, clipped text, overlapping cards, and cramped
  buttons at about `1440px` desktop and `390px` mobile.

## Variant Selection

- Use **Research Report Variant** by default for papers, code walkthroughs,
  repo notes, technical reports, research summaries, surveys, study guides,
  bibliographies, and landmark-paper timelines.
- Use **Product Robotics Variant** only when the user explicitly asks for a
  robotics product website, Figure-like homepage, launch page, product-led hero,
  hardware/software product page, or cinematic robotics documentation.

Read the relevant reference file before drafting:

- `references/research-report-style.md` for the default report structure,
  design tokens, responsive layout, typography, tables, timelines, and
  validation checklist.
- `references/code-blocks-prism.md` when the page contains code blocks,
  algorithms, config, shell commands, directory trees, or copy buttons.
- `references/robotics-product-variant.md` only for product-site or
  product-led robotics pages.

## Research Report Defaults

Structure most report pages as:

1. Sticky compact nav with report title, status/count, and anchor links.
2. Compact report cover with title, framing paragraph, and a useful reading map
   or abstract/scope panel.
3. Method, taxonomy, selection criteria, or contribution-axis summary.
4. Dense section body: chronological paper list, code map, algorithm walkthrough,
   experiment table, architecture flow, or implementation notes.
5. Minimal footer with date, scope note, or source caveat.

Visual stance:

- Warm paper background, white report cards, thin gray rules, and restrained
  blue/heat accents.
- Technical-heading scale, not billboard marketing type.
- Dense enough for repeated reading, with enough spacing to scan quickly.
- Small rectangular mono action links for papers, repos, and code references.

## Required Checks

Before finishing:

- Long paper titles, paths, author strings, venues, URLs, and code labels wrap
  cleanly with `min-width: 0` and `overflow-wrap: anywhere` where needed.
- The first screen exposes the reading structure; do not hide the document
  behind an oversized hero.
- Code blocks escape `&`, `<`, and `>` correctly and include explicit language
  classes.
- Motion is CSS-only and disabled under `prefers-reduced-motion: reduce`.
- The final HTML still works when opened directly via `file://`.
