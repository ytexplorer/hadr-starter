# Implementation notes

Kept by the agent, reviewed by you. One entry per working block.

## Decisions

## Open questions

## Deviations

<!-- Anything built that departs from the PRD or CLAUDE.md is recorded here,
     with the reason. An undocumented deviation is a bug. -->

### Slice 1 (Task 12)

- (a) `meta.feeds` health is present in the contract ahead of the gate/analytics slices.
  Reason: forward-compat seam — the field costs nothing to emit now and later slices
  (gate/analytics) will consume it, so it's added early rather than bolted on later.
- (b) Below-threshold (non-`major`) events are carried in the contract even though no
  "show all" filter exists yet in the front end. Reason: forward-compat seam — the front
  end already renders them (as provisional/minor markers), and dropping them at the
  pipeline layer would require re-adding the field later; kept for the eventual filter UI.
- (c) Issue #3's Definition of Done says "hosted"; no live Vercel deploy exists yet.
  Reason: the live Vercel deploy is a deliberate fast-follow (see the deploy heads-up in
  the Task 12 brief re: Vercel project root and `requirements.txt`/pyproject export), so
  Slice 1's DoD is local end-to-end + green test suites. This narrows the issue wording but
  does not change ADR 0006 (the JSON contract boundary still stands).
- (d) Map markers have no hazard glyph (colour = Severity, size = magnitude only).
  Reason: with a single hazard type (EQ) in this slice, the spec's `icon = hazard` encoding
  carries no disambiguating information — there is nothing to distinguish. Deferred until a
  second hazard type (e.g. GDACS) is ingested; forward-compat narrowing, not an ADR change.
- (e) mypy `strict` is scoped to the pipeline source packages (`pipeline`, `api`); the
  `tests.*` override relaxes several strict checks (untyped test helpers/fixtures).
  Reason: keeps the shipped source fully strict while not forcing type-annotation ceremony
  onto test fixtures that never ship; see `pipeline/pyproject.toml` `[[tool.mypy.overrides]]`.
- (f) Python is pinned to 3.12 (`pipeline/.python-version` + `requires-python ">=3.12,<3.13"`)
  per CLAUDE.md's runtime pin. In `web/`, two narrowly-scoped `eslint-disable` comments
  accommodate Next 16 rule changes with no logic change: the SSR mount-gate in
  `web/components/CrisisMap.tsx` (`react-hooks/set-state-in-effect`, needed because the map
  must mount client-side only) and the loosely-typed mock props in the Vitest test mocks for
  `react-leaflet`/`next/dynamic` (`@typescript-eslint/no-explicit-any`).
