# Robotics Product Variant

Use this reference only when the user explicitly asks for a robotics product
site, Figure-like homepage, launch page, product-led hero, product software
page, or cinematic hardware/software documentation.

The default `research-report-html` output is a research report. Do not switch to
this variant for ordinary papers, surveys, study guides, or code walkthroughs.

## Visual Direction

Translate current robotics/startup homepage patterns into a reusable light
documentation system:

- warm white surfaces and black minimalist navigation
- large mechanical display typography
- product-first hero imagery or CSS-generated product/media panel
- pill or outline CTAs with restrained hover states
- diagonal-arrow actions when useful
- small gradient accents only as signal marks, rules, status dots, or hover
  details

Do not copy brand assets, logos, videos, proprietary fonts, or exact layouts
from Figure AI, 1X, Runway, or other companies.

## Structure

1. Sticky top navigation with compact black links and a light translucent
   surface.
2. Bright product hero with warm white background, large mechanical title,
   concise support copy, and a topic-specific media panel.
3. Light documentation sections with white/mist bands, thin dividers, wide
   content, and technical panels that preserve source order.
4. Minimal black/white footer.

## Media Panel Rules

When no real user-provided product imagery exists, create CSS visuals rather
than generic decoration:

- warm white video-frame or glass panel
- sensor grid, trajectory grid, robot planning map, or pipeline traces related
  to the topic
- telemetry chips with thin black borders
- slow scan or sheen overlay
- stable `aspect-ratio`, bounded chips, and mobile-safe dimensions

Avoid generic orbs, bokeh, stock-like backgrounds, and decorative blob fields.

## Typography And Motion

- Display headings may be larger than the research variant, but letter spacing
  stays `0`.
- Body text remains technical and concise.
- Use CSS-only motion, short UI transitions, and `prefers-reduced-motion`.
- The page must remain coherent with animation disabled and when opened via
  `file://`.
