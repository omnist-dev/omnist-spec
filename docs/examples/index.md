# Real-world examples

Four real, external formats — none designed for Omnist — each with an OSD
schema and real fixture data, imported directly into this repository so the
spec is self-contained: no reader needs to clone a different project to
follow one of these.

| Example | Format | Spec rigor | `any` fraction | Gap category |
|---|---|---|---|---|
| [pyproject.toml](pyproject/pyproject.osd) | TOML | Multiple PEPs (517/621/639/794) | 7 of 20 fields | Union, open key set, cross-field constraint |
| [package.json](package-json/package.osd) | JSON | None — prose docs only, third-party schema | 8 of 16 fields | Union, open key set |
| [GitHub Actions workflow](github-actions/workflow.osd) | YAML | None — prose docs only, third-party schema | 6 of 8 fields | Union (3-way), open key set, shape-depends-on-sibling-key |
| [sitemap.xml](sitemap/sitemap.osd) | XML | One small, official XSD-equivalent spec | 0 of 4 fields | Value refinement (enum/range) |

Ordered by how much formal ground truth each format has: **pyproject.toml**
(several PEPs, each enumerating exact field shapes) → **sitemap.xml** (one
small, official, narrow spec) → **GitHub Actions workflows** (a
community-maintained schema only, never an official GitHub artifact) →
**package.json** (no spec and no official schema at all — years of accreted
convention). The `any` fraction tracks this spectrum, not schema size:
pyproject.toml has the most fields and the lowest `any` fraction; the
workflow schema is the smallest of the four by field count and still comes
out worst, because `jobs:` alone is irreducibly open and carries most of a
workflow's real content.

## The four gap categories, one worked example of each

1. **Union** — a field that's legitimately more than one shape. `pyproject.toml`'s
   `license` (a string *or* a table) is the simplest case;
   `github-actions/workflow.osd`'s `on` (string, array, *or* map) is the
   sharpest — a genuine three-way union. A field's OSD type is always exactly
   one scalar or one `Ref` — there's no "A or B" combinator (§3.2).
2. **Open key set** — a record where the label set isn't fixed by the
   format, it's chosen by whoever writes the file: `[tool]` in
   pyproject.toml, `dependencies` in package.json, `jobs` in a workflow.
   OSD records are closed by design (§3.2).
3. **Cross-field constraint** — a rule spanning sibling fields, like
   pyproject.toml's `version` being required unless `"version"` appears in
   `dynamic`. OSD's cardinality is per-field only.
4. **Value refinement** — a field with the right *type* but a restricted
   *value* set or range. Only `sitemap.osd` surfaces this:
   [`invalid-values.xml`](sitemap/invalid-values.xml) has `changefreq: sometimes`
   (not one of the spec's 7 allowed values) and `priority: 1.5`/`-0.2`
   (outside the spec's `[0.0, 1.0]` range) — both validate cleanly, since
   `string`/`number` scalars check type, not value.

## pyproject.toml

Three fixtures, each exercising a different corner of the schema:

- [`omnist.toml`](pyproject/omnist.toml) — first-party: this ecosystem's own
  `pyproject.toml`. Exercises the legacy `license = {text=...}` table form and
  two real `[tool.*]` sections.
- [`spam-eggs.toml`](pyproject/spam-eggs.toml) — the official "full example"
  from the Python Packaging User Guide, verbatim. Exercises partial author
  entries, the current SPDX-string `license`, `optional-dependencies` extras,
  and a custom `entry-points` group.
- [`invented-dynamic-version.toml`](pyproject/invented-dynamic-version.toml) —
  synthetic, written to exercise `dynamic = ["version"]`, the one case the
  other two fixtures don't touch.

## GitHub Actions workflow

- [`test.yml`](github-actions/test.yml) — first-party: one of this
  ecosystem's own real CI workflow files, using the ordinary, unquoted `on:`
  key that almost every real workflow uses. **This fixture fails to even
  read** — see the codec-level finding below.
- [`test-quoted-on.yml`](github-actions/test-quoted-on.yml) — `test.yml`
  with the key quoted as `"on":`, a synthetic derivative built specifically
  to demonstrate schema validation succeeding once past the codec issue.

**A real codec-level finding, not a schema one.** YAML 1.1's core schema
resolves `on`/`off`/`yes`/`no`/`true`/`false` as booleans, not strings — the
classic case is `NO` parsing as `false`; `on` is a less-famous instance of
the same rule. A bare `on:` key parses to the boolean `true`, not the string
`"on"`. Since a Document label MUST be a string (§2.2.2), a reader MUST
refuse to build a Document from a boolean-keyed mapping — `test.yml` fails
at that point, before validation is ever reached. This is correct behavior
given what the YAML parser handed it; the problem is one level up, and it
collides with the one top-level key almost every real workflow file needs.

## package.json

- [`npm-init-default.json`](package-json/npm-init-default.json) — the
  official `npm init --yes` output from npm's own documentation, verbatim.
  `repository`/`bugs` in object form, `author` as an empty string.
- [`invented-widget-cli.json`](package-json/invented-widget-cli.json) —
  synthetic, deliberately the *opposite* shape (`repository`/`bugs` as
  strings, `author` as an object), showing the union goes both ways. Also
  exercises `bin` as a multi-command open map.

## sitemap.xml

- [`minimal.xml`](sitemap/minimal.xml) — the official example from the
  sitemaps.org protocol page, verbatim. Fully spec-valid.
- [`invalid-values.xml`](sitemap/invalid-values.xml) — synthetic,
  demonstrating the value-refinement gap directly: `changefreq: sometimes`
  and `priority: 1.5`/`-0.2` both validate despite being invalid per the
  sitemaps.org spec.

## If you're designing a format for OSD

Lessons drawn from all four:

1. **Avoid same-key polymorphism.** `readme`/`license` (pyproject.toml) and
   `author`/`bugs`/`repository` (package.json) being a string *or* a table
   under one key is the single biggest source of unchecked surface across
   this set. If a format needs both a short and a long form of something,
   use different keys, not one polymorphic key.
2. **Hoist open keys into their own namespace.** `[tool]` in pyproject.toml
   does this correctly — all openness lives in one dedicated, clearly-open
   section. Open keys scattered through an otherwise-closed structure
   (workflow's `jobs`/`env`/`defaults` alongside closed fields like `name`)
   don't.
3. **Avoid conditional requiredness across sibling fields** ("at least one
   of A or B," "A required unless B says otherwise"). Pick one canonical,
   always-required field instead.
4. **Avoid meta-referential fields** — a field whose *value* names other
   fields and changes their shape or requiredness. pyproject.toml's
   `dynamic` and a workflow step's shape depending on whether `uses:` or
   `run:` is present are both instances. No static schema language can
   express this; it requires runtime interpretation of the data.
5. **If you need restricted values, expect most schema languages — OSD
   included — to enforce only the type, not the restriction.** sitemap.xml's
   `changefreq`/`priority` show this isn't about open-endedness at all — a
   small, fully closed format can still have unchecked value constraints.
6. **Silent forward-extension of a closed section is a versioning problem,
   not a modeling one.** If a section needs to grow over time, decide
   upfront whether it's genuinely closed (growth needs an explicit version
   marker) or genuinely open (give it its own namespace from day one).

The common thread: OSD models cleanly whatever a format's design keeps
structurally uniform, value-restricted where it matters, and unconditional.
