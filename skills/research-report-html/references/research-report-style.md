# Research Report Style Reference

Use this reference for the default `research-report-html` output: papers,
surveys, code walkthroughs, study guides, reading notes, technical reports, and
research timelines.

## Design Tokens

Always define the core variables in the page. Use this set unless the user's
existing design system gives a stronger local convention:

```css
:root {
  --figure-black: #111111;
  --heading-main: #171717;
  --figure-white: #F7F6F0;
  --surface-white: #FFFFFF;
  --surface-mist: #FBFAF5;
  --surface-stone: #E4E1D7;
  --text-main: #202020;
  --text-muted: rgba(28, 28, 28, 0.66);
  --text-soft: rgba(28, 28, 28, 0.44);
  --line-soft: rgba(17, 17, 17, 0.1);
  --line-strong: rgba(17, 17, 17, 0.22);
  --accent-blue: #2457A6;
  --surface-blue: #EFF4FA;
  --accent-heat: #D85F2B;
  --font-display: "Space Grotesk", "Inter", sans-serif;
  --font-sans: "Inter", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  --font-mono: "JetBrains Mono", "SFMono-Regular", "Menlo", "Consolas", monospace;
}
```

Use this font link unless the user asks for strict offline output:

```html
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

## Layout

The page should feel like a serious technical report with a designed reading
surface.

- Use a compact report cover, not a full-viewport product hero.
- Put a reading map, abstract, scope, method card, code map, or contribution
  axes near the title.
- Make section headers readable and calm. Avoid ultra-heavy display headings.
- Keep nav compact and sticky when the report has more than three major
  sections.
- Use cards only for repeated items, callouts, code maps, tables, and reading
  panels. Do not put cards inside cards.

Recommended defaults:

```css
.container {
  width: calc(100% - 32px);
  max-width: 1120px;
  margin: 0 auto;
}

.report-hero {
  padding: 70px 0 58px;
  min-height: auto;
}

h1 {
  max-width: 820px;
  font-size: clamp(2.8rem, 4.65vw, 5.2rem);
  line-height: 0.98;
  font-weight: 500;
  letter-spacing: 0;
}

h2 {
  font-size: clamp(1.9rem, 2.8vw, 3.35rem);
  line-height: 1.1;
  font-weight: 500;
  letter-spacing: 0;
}
```

For long report lists:

```css
.paper-row {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) 132px;
  gap: 0;
}

.paper-row > * {
  min-width: 0;
}

.paper-title,
.paper-meta,
.paper-link,
.path,
.url {
  overflow-wrap: anywhere;
}

@media (max-width: 760px) {
  .paper-row {
    grid-template-columns: 1fr;
  }
}
```

## Components

- **Reading map**: a dense list of sections with short labels and anchor links.
  It should help the reader decide where to start.
- **Code map**: table or grid mapping modules, functions, files, and concepts.
  Keep file paths monospace and wrap them on mobile.
- **Paper timeline**: compact rows with year, title, venue, contribution, and
  link. Reveal many entries without feeling cramped.
- **Callout**: white or mist surface with a slim blue/heat rail, not an
  oversized quote block.
- **Tables**: thin grid lines, compact row height, monospace headers, horizontal
  overflow only inside the table wrapper on mobile.
- **Action links**: small rectangular mono buttons, radius around `5px`, with
  visible link text.

## Motion And Responsiveness

- Add motion only after the static layout works. Use subtle CSS transitions,
  underline reveal, small hover lifts, or soft status pulses.
- Include `@media (prefers-reduced-motion: reduce)` and disable ambient
  animation there.
- Do not use viewport-width font scaling. Use fixed media-query type sizes when
  mobile headings need adjustment.
- Fixed-format visuals need `aspect-ratio`, `min-height`, or both.
- Verify no horizontal scrolling at about `390px` wide.

## Validation Checklist

- `<!DOCTYPE html>`, language attribute, charset, viewport meta, title, and
  complete closing tags are present.
- The first screen contains title, framing, and reading structure.
- Long metadata wraps rather than clipping.
- Tables and code blocks remain readable on mobile.
- No unrelated brand assets, logos, videos, dark cinematic background, generic
  blobs, or Claude-style warm editorial treatment.
