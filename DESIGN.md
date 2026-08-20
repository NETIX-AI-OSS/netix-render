# NETIX Design Skill

Design guidance for generating NETIX-branded HTML. Served to agents as an MCP resource
(`netix://design/DESIGN.md`) alongside `netix://design/tokens.json`. When building HTML for
NETIX — emails, reports, dashboards, one-off pages — follow this file instead of inventing
colors or type.

## Tokens (source of truth: `netix_render/tokens.json`)

| Token | Value | Use |
| --- | --- | --- |
| `color.primary` | `#196594` | Brand blue: header bands, buttons, links, emphasis |
| `color.primary_soft` | `#e1edf4` | Tinted fills behind primary-colored text |
| `color.accent` | `#30bce4` | Wordmark suffix and small highlights only — never body text |
| `color.ink` | `#2d2e2f` | Body text |
| `color.ink_soft` / `ink_faint` | `#5d7482` / `#8298a4` | Secondary text, labels, footers |
| `color.surface` / `surface_soft` | `#ffffff` / `#f4f6f8` | Card / page canvas |
| `color.line` | `#e5eaf0` | Borders, table rules |
| `color.status.ok/warn/crit/muted` | `#12914d` / `#da9901` / `#ff3838` / `#a1b0ba` | Semantic state only — never decoration |
| `color.status_soft.*` | tinted equivalents | Pill and band backgrounds |
| `color.print.navy` | `#1F4E78` | Print/docx documents only |

Typography: `'Inter', 'Segoe UI', Arial, sans-serif`. Web pages may load Inter; email must
rely on the fallback stack — never link webfonts in email. Uppercase labels get
`letter-spacing: 0.8px` at 10–11px. Body text 13–14px, line-height 1.6.

## Voice

Sign-off is always "NETIX.AI · CAFM Platform" (`email.sign_off`). The wordmark is
`NETIX` + accent-colored `.AI`. Never write "IFM Facilities Management" or other legacy
sign-offs. Automated mail always carries the do-not-reply note. Semantic color states are
ok / warn / crit — pick by meaning, not appearance.

## Email constraints (hard rules)

- 600px max frame, table layout, no flexbox/grid, no `<svg>`, no external CSS/JS/fonts.
- All CSS inlined (`css_inline.inline` does this — author in a `<style>` block).
- Only absolute `https` URLs for images (per-org logo); no data: URIs.
- Keep rendered HTML under 100KB (Gmail clips at 102KB).
- `lang` + `dir` on `<html>`; Arabic is RTL — table alignment must follow `dir`.
- Every email has a plain-text alternative carrying the same facts.

## Composition

Emails: header band (primary, wordmark or org logo) → white sheet with the content →
centered faint footer. One `h1`-equivalent per email; key-value tables for structured
facts; a single primary CTA button; status pills/bands for state.

Reports: use the `ReportDocument` section vocabulary (kpi_grid, check_table, trend_pair,
data_table, rings, …) rather than freeform layout — the renderer guarantees consistency.

## Don'ts

Don't hardcode hex values that exist as tokens. Don't introduce new colors for states the
status palette covers. Don't center body copy. Don't use more than one accent moment per
email. Don't emit `<script>` anywhere.
