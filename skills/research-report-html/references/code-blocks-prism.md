# Code Blocks, PrismJS, And Copy Buttons

Use this reference when a generated research report includes code snippets,
algorithm walkthroughs, shell commands, config files, directory trees, or any
copyable technical block.

## Default Behavior

Use PrismJS as the default short-term code-rendering solution when the user has
not requested strict offline output. Keep all custom visual styling inline in
the page's single `<style>` block.

Place pinned PrismJS scripts near the end of `<body>`:

```html
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/prism.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-python.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-c.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-cpp.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-json.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-bash.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-javascript.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-typescript.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-yaml.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/plugins/toolbar/prism-toolbar.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.30.0/plugins/copy-to-clipboard/prism-copy-to-clipboard.min.js"></script>
```

Emit code blocks with explicit language metadata:

```html
<pre class="language-python" data-language="Python"><code class="language-python">...</code></pre>
```

Escape code content before insertion. Convert `&`, `<`, and `>` to HTML
entities so snippets cannot break the page markup.

## Language Mapping

| Source label | Prism class | Display label |
| --- | --- | --- |
| `python`, `py` | `language-python` | Python |
| `c++`, `cpp`, `cc`, `hpp` | `language-cpp` | C++ |
| `json` | `language-json` | JSON |
| `bash`, `shell`, `sh`, `zsh` | `language-bash` | Bash |
| `javascript`, `js` | `language-javascript` | JavaScript |
| `typescript`, `ts` | `language-typescript` | TypeScript |
| `html`, `xml`, `markup` | `language-markup` | HTML |
| `css` | `language-css` | CSS |
| `yaml`, `yml` | `language-yaml` | YAML |
| unknown, diagrams, directory trees | `language-plaintext` | Text |

## Styling

Use light code surfaces by default:

```css
pre[class*="language-"] {
  --code-accent: var(--accent-blue);
  position: relative;
  border-left: 4px solid var(--code-accent);
}

pre.language-python { --code-accent: #3776AB; }
pre.language-cpp { --code-accent: #659AD2; }
pre.language-json { --code-accent: #7C5CFF; }
pre.language-bash { --code-accent: #111827; }
pre.language-javascript { --code-accent: #D6A400; }
pre.language-typescript { --code-accent: #3178C6; }
pre.language-markup { --code-accent: #E34C26; }
pre.language-css { --code-accent: #264DE4; }
pre.language-yaml { --code-accent: #CB171E; }

div.code-toolbar { position: relative; }
div.code-toolbar > .toolbar {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  opacity: 0;
  transform: translateY(-2px);
  transition: opacity 0.18s ease, transform 0.18s ease;
}

div.code-toolbar:hover > .toolbar,
div.code-toolbar:focus-within > .toolbar {
  opacity: 1;
  transform: translateY(0);
}

.copy-to-clipboard-button {
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  padding: 0.32rem 0.62rem;
  background: rgba(255, 255, 255, 0.9);
  color: var(--figure-black);
  font-family: "JetBrains Mono", monospace;
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
}
```

Recommended token overrides:

```css
.token.comment,
.token.prolog,
.token.doctype,
.token.cdata { color: rgba(12, 12, 12, 0.42); }
.token.punctuation { color: rgba(12, 12, 12, 0.58); }
.token.keyword { color: #7C3AED; }
.token.function { color: #1D6FB8; }
.token.string { color: #16845B; }
.token.number,
.token.boolean,
.token.null { color: #C2410C; }
.token.operator { color: #9A3412; }
.token.class-name,
.token.builtin { color: #2563EB; }
```

## Local Fallback

For pages opened directly via `file://`, Clipboard API permissions may vary.
Add a tiny fallback after Prism scripts. It should add buttons only when Prism
Toolbar did not already wrap the block.

If strict offline output is requested, do not include CDN scripts. Still emit
language-labelled code blocks and token-style-ready CSS, then include a small
hand-written copy script. Mention that full syntax parsing is disabled unless
PrismJS is inlined or a build step is allowed.
