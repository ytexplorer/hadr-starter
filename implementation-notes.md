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

### Slice 2 (Tasks 1–18)

- **ADR 0003 boost gap CLOSED (bookkeeping — no ADR change).** The newsworthiness
  boost was accepted "from v1" in ADR 0003 but was **absent and unlogged** through
  Slice 1. Slice 2 lands it: `severity.score = base_signal + boost.applied` and an
  auditable `severity.boost` object (`pipeline/pipeline/boost.py`,
  `MAX_BOOST/CAPITAL_BONUS/BOOST_CAP/BOOST_RADIUS_KM`). ADR 0003 is now *honored*,
  not changed — no superseding ADR needed. (Spec §10.1, §7.2; ADR 0003.)
- **Deviation (d) hazard glyph CLOSED.** Slice 1 (d) deferred the map glyph "until a
  second hazard type is ingested." GDACS (EQ/TC/FL/VO/DR) makes that true, so the
  2-letter hazard glyph on `CrisisMap` markers + the new `MapLegend` now ship.
  (Spec §10.2, §8.)
- **New — GDACS detail fetch for `affected`.** Departs from Slice 1's list-only
  ingest: the EVENTS4APP list carries no population, so `pipeline/api/contract.py`
  makes bounded per-event `geteventdata` GETs (Orange/Red only — the sole events that
  can clear `major` and be displayed) to source the verbatim exposure figure via
  `affected.py:extract_exposure`. Per-hazard *physical* metrics (wind/flood-area/VEI)
  stay deferred. Grounded, never computed. (Spec §10.3, §7.5; ADR 0007.)
- **New — `severity.inputs` reshaped under the 2.0.0 bump.** Gained `alert_score`;
  `mag`/`sig`/`alert` are now all nullable and always-present (keys
  `{"mag","sig","alert","alert_score"}`). EQ identity is preserved **semantically**
  (level, `major`, and the values of mag/sig/alert), not as literal byte-identity of
  the v1 object — legitimate under a breaking bump; locked decision 3 freezes only the
  4-value `level` band. (Spec §10.4, §4.1.)
- **New — top-level `magnitude` is now `number|null`, always present** (null for
  TC/FL/VO/DR) rather than the v1 EQ-only required number. Uniform with the
  always-present `boost`/`affected`; the front end guards null and sizes markers off
  `severity.score` (`markerRadius`). (Spec §10.5, §4.1.)
- **Contained tension logged — v1 "green EQ → major" quirk preserved (blast radius
  corrected by final review).** EQ `base_signal` is constructed so
  `base_signal ≥ 60 ⇔ old is_major` (`severity.py` `_EQ_ALERT_ARM` maps green→60.0 =
  `MAJOR_CUTOFF`), which keeps the v1 quirk that a green-alert EQ can be `major`. This
  conflicts with ADR 0003's "hide green" applied to GDACS-sourced green colours on the
  non-EQ path (`colour_base` green = 45 < `MAJOR_CUTOFF` 60). **Blast radius (final
  whole-branch review):** the earlier "a green-alert EQ *can* be major" wording
  understated it. v1's `alert` was USGS PAGER, which is *null for the vast majority of
  quakes*, so the quirk rarely fired; but `merge.py` takes `alert` from the GDACS member
  on merge and GDACS `alertlevel` is *always* present, so in live data effectively
  **every** GDACS-listed EQ (green included) scores ≥ 60 and clears the `major` gate, and
  any modest USGS quake (e.g. M4.8, PAGER null → not major in v1) that tier-3-merges with
  a green GDACS row flips to `major` — diluting the Major default view. `test_eq_regression`
  cannot catch this (it runs USGS-only feeds). **If kept long-term this needs a superseding
  ADR;** Slice 2 only logs it. **Scheduled:** the ADR 0003 tuning pass is the first order of
  business next slice — distinguish alert provenance (keep `_EQ_ALERT_ARM` for genuine PAGER
  alerts; route GDACS-sourced colour on EQs through `colour_base`, i.e.
  `max(mag_arm, sig_arm, pager_arm, colour_base_arm)`), quantified against live GDACS data
  before deciding urgency; if the behaviour is kept deliberately, write the superseding ADR.
  (Spec §10.6, §7.3; ADR 0003.)
- **New — canonical `id` can churn `gdacs:… → usgs:…`.** A GDACS-only event that later
  gains a USGS match flips its canonical `id` to the USGS one
  (`merge.py:FEED_PRIORITY = ("usgs","gdacs")`, present-wins). Acceptable this slice
  because revisions / history / id-stability across runs are out of scope. (Spec
  §10.7, §7.4.)
- **`feeds/gdacs.md` updated.** Documented the `geteventdata` detail feed's per-hazard
  exposure fields and corrected the truncated sample's implication that population
  lives in the EVENTS4APP list feed (it does not). (Spec §10.8, §7.5.)
- **v1 fixture retirement extended.** Retiring `contract/fixtures/contract.v1.*.json`
  (Task 17) orphaned the pipeline v1 fixture-validation tests in
  `pipeline/tests/test_contract_schema.py` (no task covered that file). The
  fixture-dependent tests were removed at merge time (commit `ca72695`) so the merged
  tree stays green; `contract.v1.schema.json` remains frozen in-repo with its
  standalone schema-validity test intact.
- **ADR 0005 layer-2 dedup deferred.** Slice 2 ships only the deterministic layer-1
  dedup; the semantic-embedding layer-2 remains deferred (no server-side embedding key
  introduced). Logged per the deviations policy. (ADR 0005.)
- **`severity.py` type widening (Task 5).** The plan's verbatim code fails mypy strict
  on the installed mypy (2.1.0) at the two GDACS `inputs.get("alert")` lookups;
  `_COLOUR_BASE`/`_COLOUR_LEVEL` key types were widened `str → str | None` (mirroring
  `_EQ_ALERT_ARM`), a behavior-preserving change disclosed in the Task 5 report.
- **ruff format debt (Task 11 observation).** `ruff format --check` flags ~11 pipeline
  files including plan-verbatim code (compact grouped-argument style with magic
  trailing commas, pre-existing repo-wide). Substantive gates (`ruff check` lint, mypy,
  tests) are clean; a dedicated repo-wide formatting pass is deferred rather than
  reformatting plan-verbatim files piecemeal.
