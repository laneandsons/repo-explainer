---
name: html-guide-builder
description: Build a self-contained, light-mode HTML "guide" document from a structured list of items (resources, options, checklist entries) — Tailwind CDN styling, larger-than-average fonts, a sticky table-of-contents nav with anchor links, color-coded tiers/categories, and an optional full scoring table. Use whenever the user wants a resource evaluation, prioritized reading list, comparison guide, or reference doc as a standalone HTML file they can open in a browser (e.g. "make this an HTML guide," "output as an attractive HTML doc," "build me a guide like the one you made before").
---

# HTML Guide Builder

Produces a single self-contained HTML file in the house style established for Brian's resource/reading-list evaluations. Use this whenever the deliverable is a browsable reference document rather than a Word doc, markdown file, or slide deck.

## When to use this

- The user asks for an "HTML guide," "HTML document," or to turn an evaluation/checklist/comparison into something browsable.
- The user references "like the one you made before" for a resource evaluation, reading list, or tiered breakdown.
- The content naturally has: a title/intro, several categorized or tiered sections, and (optionally) a comparison/scoring table.

Do NOT use this for print-oriented deliverables (use the `docx` or `pdf` skill instead), or for content the user explicitly wants as markdown/plain text.

## Light mode is absolute — read this first

**Every pixel of the rendered page is light mode unless Brian explicitly asks for dark mode in that request.** This is not a default that yields to convention, aesthetics, or "how this element is normally styled on the web." It applies to *every* element without exception:

- page background and body text
- cards, callouts, badges, borders
- table headers, rows, and hover states
- sticky nav
- **code blocks (`<pre>` / `<code>`) — this is the one that gets violated.** The near-universal web convention is a dark "code editor" background (`#0f172a`, `#1e1e1e`, `bg-slate-900`, etc.). That convention does NOT apply here. Dark code blocks on a light page are a dark-mode element and are a defect.

Approved light code-block styling:

```css
pre {
  background: #f1f5f9;      /* slate-100 */
  color: #1e293b;           /* slate-800 */
  border: 1px solid #e2e8f0; /* slate-200 */
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
  overflow-x: auto;
  font-size: 0.92rem;
  line-height: 1.6;
}
/* Inline code inside prose */
p code, li code, td code {
  background: #eef2ff;      /* indigo-50 */
  color: #4338ca;           /* indigo-700 */
  padding: 0.1rem 0.4rem;
  border-radius: 0.35rem;
}
```

**Banned anywhere in the file** (unless dark mode was explicitly requested): `#0f172a`, `#1e293b` or darker as a *background*, `#1e1e1e`, `#282c34`, `#000`, any `bg-slate-800/900`, `bg-gray-800/900`, `bg-zinc-800/900`, `bg-neutral-800/900`, `bg-black`, and any `prefers-color-scheme: dark` block. Dark values are fine as *text* color on a light background; they are never a background.

If a dark element seems genuinely necessary for legibility, ask Brian first — do not decide unilaterally.

## Step 1 — Gather the config

Before writing HTML, nail down these inputs (ask the user only if genuinely ambiguous — otherwise infer from the conversation and state your assumptions):

1. **Title + one-paragraph subtitle** describing what the guide covers and why.
2. **Tiers or categories.** Most of these guides group items into ranked tiers (e.g. "Read Now" / "Scan" / "Defer") or plain categories (e.g. by topic). Each tier/category needs: a short label, a one-line description of what belongs in it, and a color:
   - Green (`emerald`) = top priority / do this first / highest confidence
   - Blue = second priority / useful reference
   - Amber = conditional / lower confidence / "ask an AI instead of reading"
   - Slate/gray = defer, skip, or low value
   (Reuse this palette unless the user's content calls for a different scheme — keep it to 3–4 tiers max, more becomes visual noise.)
3. **Items within each tier.** Each item needs: a title, optional link, and a 1–2 sentence rationale (why it's in this tier, not just what it is).
4. **Optional: a full comparison/scoring table** across ALL items with a few consistent numeric or categorical columns (e.g. 1–5 scores). Include this when the user's evaluation criteria are explicit and comparable across items (as with the reading-list evaluation this skill was built from — criteria were: plan clarity, source trust, scannability, necessity-now-vs-later).
5. **A closing "bottom line" callout** — 2–4 sentences synthesizing the recommendation, in a highlighted box.

If the user hands you unstructured material (a list of links, a messy doc), do the analysis/scoring yourself first — this skill only covers the *output format*, not the evaluation itself. Research and judgment come first; formatting comes last.

## Step 2 — Build the HTML

Copy `reference/template.html` as the starting point and fill in the placeholders. Key structural rules, non-negotiable:

- **Single file.** All CSS and JS inline or via CDN `<script>`/`<style>` tags — no external stylesheets to manage.
- **Tailwind via the official Play CDN**: `<script src="https://cdn.tailwindcss.com"></script>`. Do NOT use `cdnjs.cloudflare.com/ajax/libs/tailwindcss/...` — that path does not expose the `tailwind` runtime global and throws `ReferenceError: tailwind is not defined` in the browser console. Always test that the CDN script tag is exactly `https://cdn.tailwindcss.com` unless the user asks for a compiled/offline build.
- **Light mode only, every element** (`bg-slate-50 text-slate-800`) — see the absolute rule above. Code blocks included.
- **Larger-than-average type**: base body text ~`1.15rem`–`1.2rem` (set via inline `<style>` on `body`, since Tailwind's default `text-base` reads small for a reading document), headers scaled up accordingly (`text-3xl`–`text-6xl`).
- **Sticky nav** at the top (`sticky top-0 z-20`) with anchor links (`<a href="#section-id">`) to every major section — this is the "internal page navigation" Brian asks for by default on these documents.
- **Tier/category color-coding**: give each section (or each row in a table) a left border or background tint matching its tier color, plus a small rounded "badge" label (see template) so tiers are scannable at a glance without reading text.
- **Card-based item layout**: each item is a rounded-corner card (`rounded-xl border shadow-sm`) with title, optional link (`text-indigo-600 hover:underline`), and rationale text — not a bare bullet list.
- **Code samples** (for technical guides): use the light `pre`/`code` styling given above. Escape `<` and `>` as `&lt;`/`&gt;` inside `<pre>` so JSX and generics render instead of being parsed as HTML.
- **Comparison table** (if included): `overflow-x-auto` wrapper, `sticky`-friendly header row (`bg-slate-100`), zebra/hover row states, tier-colored row tints matching the section colors above.
- **Bottom-line callout**: a distinct colored box (e.g. `bg-indigo-50 border-indigo-100`) at the end, larger text, synthesizing the recommendation.
- Include a short footer line with context (what this is, date) if useful, but keep it minimal.

## Step 3 — Verify before delivering

Run these checks mechanically, not by eyeballing:

1. **Dark-mode scan (do this first).** Grep the finished file for banned dark values and fail on any hit:

   ```bash
   grep -nEi 'background:\s*#(0f172a|1e1e1e|282c34|111|000)|bg-(slate|gray|zinc|neutral)-(800|900)|bg-black|prefers-color-scheme:\s*dark' guide.html
   ```

   Any match means the guide is not shippable as-is. Fix, then re-run.
2. **Tailwind CDN check.** Confirm the script tag is exactly `https://cdn.tailwindcss.com`.
3. **Anchor check.** Every `href="#..."` resolves to a real `id` on the page. Extract both sets and diff them rather than spot-checking.
4. **Visual consistency.** Tier colors match between section headers and table rows; body text is visibly larger than a typical webpage, not just headers.
5. **Deliver** via `SendUserFile`, then write it to Brian's guides folder via the device bridge (see below) and confirm the path in plain language. If it's a guide he'll revisit (a reference doc, not a one-off), also `create_artifact` per the standard persisted-artifacts guidance.

## Notes specific to Brian's setup

- Brian's guides folder is connected to Cowork sessions as `/Users/brianlane/HTMLGuides`. Save new guides there by default unless told otherwise. (Older versions of this skill said `~/Documents/HTML Guides`; use the connected-folder path shown in the session's folder list, and prefer that over any path hardcoded here.)
- He also has a local static file server (see the `_server-setup` subfolder there) that serves that folder to devices on his home network — new guides saved into that folder become browsable from his iPad automatically, no extra step needed.