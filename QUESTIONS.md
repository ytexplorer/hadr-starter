# QUESTIONS — grilling the Global Crisis Dashboard

> Scratch file for the grilling step. All known open questions are logged **upfront**
> here (grouped by theme) so you can answer many per turn. New questions get appended
> **as they arise**. Each has a **Lean** (my recommended default) so you can just say
> "accept the leans for section X" to move fast.
>
> Status legend: 🔵 open · 🟡 partially answered · ✅ answered · ⬜ deferred to later step
>
> Decided already (this session): primary user = newsroom/editorial analyst;
> delivery = hosted, read-only, auto-refreshing dashboard, no accounts. See `docs/adr/`.
>
> **Round 1 answers (2026-07-07):**
> - §B ✅ major event = severity + newsworthiness boost, from v1 (leans accepted). → ADR 0003
> - §N ✅ v1 includes **all four outputs** (map + report + analytics + insights). → ADR 0004
> - §I ✅ insights = **both** per-event angle **and** daily synthesis.
> - §H ✅ analytics metrics as proposed (events/day by hazard, severity mix, region, 7/30-day trend).
> - §C 🟡 de-dup via **semantic embeddings** requested → raises new questions, see §O.
> - §K/§M 🟡 **Python** backend, host on **Vercel**, **Tailwind + shadcn/ui** front end
>   → re-architects delivery, see §P.
>
> **Round 2 answers (2026-07-08):**
> - §P2 ✅ **(B)** all-on-Vercel: Python serverless functions + Vercel Cron + Vercel storage.
> - §P5 ✅ react-leaflet + OSM tiles.
> - §P7 ✅ all three feeds in v1, ReliefWeb via RSS.
> - §P3 ⚠️ "any of Gemini/OpenAI/Claude, viewer enters key on the webapp" → **contradicts the
>   unattended scheduled report**; reopened as §Q.
> - §O1/§O2 🔵 still open; §P2(B) makes a **local** embedder impractical → §Q.
>
> **Round 3 answers (2026-07-08):**
> - §Q1 ✅ **BYOK only (client-side)** → no unattended narrative report; LLM layer moves to the
>   front end; supersedes ADR 0002/0004 report model → reshape in §R.
> - §Q2 ✅ **all three** providers (Gemini/OpenAI/Claude), called client-side.
> - §Q3 ✅ two-layer dedup split → ADR 0005.
> - §Q4 ✅ hosted embedding API — **but this needs a server-side key, conflicting with Q1** → §R1.
>
> **Round 4 answers (2026-07-08):**
> - §R1 ✅ **server-side embedding key** (cheap dedup infra, separate from the BYOK LLM).
> - §R3/§R6 ✅ **daily Vercel Cron + on-demand refresh on page load**.
> - §R2/§R4/§R5 ✅ treated as confirmed (client-side on-demand report; keys stay in browser;
>   map/events/analytics work without a key).
> - Architecture settled → ADRs 0005, 0006, 0007.
>
> **⚠️ Superseded leans (ADRs are authoritative):** §F1 self-contained HTML → Next.js (ADR 0006);
> §I2 `claude -p` → client-side multi-provider BYOK (ADR 0007); §J1 JSON-in-repo → Vercel storage
> (ADR 0006); §K1 GitHub Pages → Vercel (ADR 0006); §L1 GitHub Actions cron → Vercel Cron
> (ADR 0006). §G1 "08:30" now means the **daily data-refresh cron time**, not a narrative publish.

---

## A. Users & usage

- **A1** 🔵 Besides the analyst, does anyone else read the output (editors, a public
  audience)? Does that change what we show or hide?
  **Lean:** analyst is the only user; editors may glance at the same read-only page. Public = no.
- **A2** 🔵 How is it used through the day — always-on second screen, checked at intervals,
  or mainly the morning report?
  **Lean:** always-on dashboard for ambient awareness + a morning report as the daily anchor.
- **A3** 🔵 What action does it drive? (pitch a story, brief an editor, dispatch a reporter,
  or pure situational awareness) — this sets how "decision-ready" each event card must be.
  **Lean:** "is this worth a story, and what do I need to pitch it" — so cards must carry
  what/where/severity/who-affected/sources at a glance.

## B. "Major event" — the definition (the crux)

- **B1** 🔵 What makes an event "major" enough to appear on the map/report — per-hazard
  thresholds, a unified severity score, or the feeds' own alert levels?
  **Lean:** start from feed alert levels (GDACS Orange/Red; USGS mag+`sig`+`alert`) mapped
  to one internal severity, tuned per hazard.
- **B2** 🔵 Earthquakes specifically: magnitude floor? (e.g. M≥5.5 globally, lower near
  population?) Use `felt`/`sig`/`alert` too?
  **Lean:** M≥5.5 globally, OR `sig`≥600, OR any non-null USGS `alert`.
- **B3** 🔵 Is "major" a **fixed editorial policy** or **analyst-tunable** via filters?
  **Lean:** fixed default threshold, with dashboard filters to widen/narrow.
- **B4** 🔵 For a newsroom, is "major" pure human impact, or also **newsworthiness**
  (near major cities / developed nations / unusual events even if low casualty)?
  **Lean:** severity is the base gate; add a light newsworthiness boost (proximity to
  population centres / capital cities). Flag if you want this in v1 or later.
- **B5** 🔵 Minor/Green events — hidden entirely, or shown de-emphasised (small grey dots)?
  **Lean:** hidden from default view; available behind a "show all" filter.

## C. Event identity & de-duplication

- **C1** 🔵 What makes two feed records "the same real-world event"? (shared GLIDE code /
  shared IDs / spatial+temporal proximity)
  **Lean:** match on GLIDE when present; else same hazard type + within ~100km + within a
  time window; USGS↔GDACS quakes via shared source IDs (`ids` / NEIC).
- **C2** 🔵 When the same quake arrives from USGS **and** GDACS, which is canonical, and how
  do we merge (severity, location, description)?
  **Lean:** merge into one record; prefer USGS for quake magnitude/location, GDACS for the
  human-impact alert level, keep both source links.
- **C3** 🔵 ReliefWeb entries are slower and curated — do we tie them to an existing event,
  or treat them as a separate "humanitarian confirmation" signal on the same event?
  **Lean:** attach as confirmation/enrichment to the matched event; don't create a duplicate.

## D. Event lifecycle (revisions, expiry, provisional data)

- **D1** 🔵 Events get **revised** (magnitude/location) or even **deleted** after we've shown
  them. What happens to a marker/report already published?
  **Lean:** update in place, keep a small revision trail, mark "revised" if it materially
  changed; if deleted upstream, mark "retracted" rather than silently vanish.
- **D2** 🔵 How long does an event stay on the map — a rolling active window (24h / 72h),
  or until it's no longer "current"?
  **Lean:** rolling 72h active window, plus GDACS `iscurrent`; older events drop off the map
  but stay in history for analytics.
- **D3** 🔵 USGS `status` is often `automatic` (unreviewed). Show provisional events
  immediately, or wait for review?
  **Lean:** show them, clearly badged "provisional/automatic" until reviewed.

## E. Feeds & ingestion

- **E1** 🔵 ReliefWeb API needs a **pre-approved appname** (may not arrive in time). Build
  against the RSS fallback meanwhile, and upgrade later?
  **Lean:** yes — RSS fallback for v1; design the parser so swapping to the API is easy.
- **E2** 🔵 Polling frequency per feed? (USGS regenerates every minute; GDACS/ReliefWeb are
  slower and publish no rate limits.)
  **Lean:** poll on each scheduled run + a modest intraday cadence (e.g. every 15–30 min);
  cache with conditional requests; be polite.
- **E3** 🔵 When a feed is **down**, what does the dashboard/report say?
  **Lean:** show a per-feed freshness/health indicator; report explicitly notes "GDACS feed
  unavailable this morning; picture may be incomplete."
- **E4** 🔵 Which USGS window(s) do we pull — `all_day`, `significant_*`, magnitude cut-offs?
  **Lean:** `all_day` for the live picture + `significant_week` for context.

## F. Map & dashboard UX

- **F1** 🔵 Any constraint that the dashboard be a **single self-contained HTML file**
  (the repo publishes `dashboard.html`)? That limits map libraries / tile sources.
  **Lean:** yes, self-contained `dashboard.html`; use a lightweight map that can run without
  external tile servers if needed (flag if offline-tiles matter).
- **F2** 🔵 What encodes on a marker — colour by severity, size by magnitude, icon by hazard
  type?
  **Lean:** colour = severity, icon = hazard type, size = magnitude/impact.
- **F3** 🔵 Marker click → what's in the detail view?
  **Lean:** title, hazard, severity, location, time, affected estimate, source feeds + links,
  revision status.
- **F4** 🔵 Which controls/filters — hazard type, severity, region, time window, search?
  **Lean:** hazard type + severity + time window to start.
- **F5** 🔵 Overall layout — map primary with a side list + tabs/panels for report, analytics,
  insights?
  **Lean:** map-primary with a right-hand event list; report/analytics/insights as tabs or
  scroll sections.

## G. Morning report

- **G1** 🔵 Timing/timezone — **08:30 Asia/Singapore** (from the repo) or the newsroom's
  timezone?
  **Lean:** 08:30 Asia/Singapore per the starter; confirm.
- **G2** 🔵 Format — ranked top-N events + a short narrative? What sections?
  **Lean:** "Overnight top events" (ranked), "New since yesterday", "Still developing",
  "Feed health".
- **G3** 🔵 "Stay quiet when nothing changed": the dashboard is always live, but does the
  **report** only (re)publish/notify when the deterministic gate detects change?
  **Lean:** yes — gate decides; on a no-change morning the report says "No major changes
  overnight" and no model call is made.
- **G4** 🔵 Where does the report live — a section of `dashboard.html`, a separate page, or
  emailed/pushed somewhere?
  **Lean:** a section/tab of the dashboard for v1; email/push later.
- **G5** 🔵 Is the report "what's **new** since yesterday" or the full standing picture?
  **Lean:** lead with new/changed; include a compact standing summary.

## H. Analytics (quantitative)

- **H1** 🔵 Confirm analytics = quantitative charts. Which specifically — counts by
  hazard/region/severity, escalation over time, historical comparison, a region heatmap?
  **Lean:** events-per-day by hazard, severity mix, region breakdown, 7/30-day trend.
- **H2** 🔵 Time ranges offered — today / 7d / 30d?
  **Lean:** 7d default, toggles for today and 30d.
- **H3** 🔵 Analytics need stored history (see J). Confirm we persist events for trends?
  **Lean:** yes.

## I. Insights (AI narrative)

- **I1** 🔵 Confirm insights = AI-generated "so what / why it matters / possible story angle"
  layered on the analytics + events.
  **Lean:** yes.
- **I2** 🔵 Powered by Claude (this is a HADR/Claude-Code starter)? Which model tier for the
  report/insights generation?
  **Lean:** Claude via headless `claude -p`; a capable model for the daily synthesis
  (cost is bounded — runs once/morning, only on change).
- **I3** 🔵 What does insights output — per-event angle, a daily overall synthesis, an
  escalation/"watch this" call, or all three?
  **Lean:** a short daily synthesis + per-top-event "why it matters / angle" lines.
- **I4** 🔵 Guardrails — must not fabricate numbers, must cite source feeds, must hedge
  uncertainty and never overstate casualties?
  **Lean:** yes, hard rule: insights may only interpret data present in the events; every
  claim traceable to a feed; explicit uncertainty language.

## J. Persistence & history

- **J1** 🔵 Do we store past events, and where — flat files (JSON) committed to the repo, or
  a small database?
  **Lean:** JSON state files in the repo (simple, diffable, works with GitHub Actions);
  revisit if volume grows.
- **J2** 🔵 Retention — how long do we keep event history? (dedup-across-days + revisions +
  analytics all depend on this)
  **Lean:** keep ~90 days of events for trends; keep identity keys longer for dedup.

## K. Delivery / hosting / infra

- **K1** 🔵 Where is the "online space" hosted — GitHub Pages (natural fit with Actions),
  or another static host?
  **Lean:** GitHub Pages publishing `dashboard.html`.
- **K2** 🔵 How does it update — the scheduled Action regenerates state + republishes the
  page on change?
  **Lean:** yes; matches the disabled `sitrep.yml` shape.
- **K3** 🔵 Privacy — is a truly public link fine, or should it be unlisted/protected? Any
  sensitivity in showing this data publicly?
  **Lean:** public but unlisted is fine (all sources are public data); confirm.
- **K4** 🔵 "Auto-refresh" — page meta-refresh every N minutes, or only refreshed content on
  the next scheduled publish?
  **Lean:** page auto-reloads every ~15 min; real freshness bounded by the publish cadence.

## L. Non-functional / operational

- **L1** 🔵 Scheduler — confirm **GitHub Actions cron** (per the starter) is the runner.
  **Lean:** yes.
- **L2** 🔵 If the pipeline breaks (feed change, parse failure), how do you find out?
  **Lean:** the Action fails loudly + a small "last successful run" stamp on the dashboard.
- **L3** 🔵 The deterministic **change-detection gate** lives in `scripts/` and must not call
  a model. What counts as "a change worth waking the model for"?
  **Lean:** a new major event, a severity upgrade, or a material revision to a shown event.

## M. Tech & tooling

- **M1** 🔵 Language/stack for the scripts (change-detection, ingestion)? Repo has no code
  yet and `CLAUDE.md` is unfilled.
  **Lean:** Node/TypeScript (fits GitHub Actions + a self-contained HTML dashboard) — confirm,
  or state a preference (Python?).
- **M2** 🔵 Dashboard build — hand-written self-contained HTML/JS, or a framework with a
  build step?
  **Lean:** hand-written / minimal, self-contained `dashboard.html` (no heavy build).
- **M3** 🔵 Any constraints to record in `CLAUDE.md` (language, test command, conventions)
  before we build?
  **Lean:** fill `CLAUDE.md` once M1/M2 are decided.

## N. Scope & MVP

- **N1** 🔵 Confirm out-of-scope for v1: real-time push, multi-user/collaboration, accounts,
  feeds beyond GDACS/USGS/ReliefWeb.
  **Lean:** confirmed out.
- **N2** 🔵 The README's "end state" is a Wednesday-afternoon working agent. What is the
  **true MVP** — which single slice must exist first?
  **Lean:** ingest USGS + GDACS → dedup → map with major events → morning report on change.
  ReliefWeb, analytics, and insights layer on after.
- **N3** 🔵 Of the four outputs (map / report / analytics / insights), which are **must-have
  for v1** vs. later?
  **Lean:** must-have: map + morning report. Later: analytics, insights.

---

## O. De-duplication with semantic embeddings (from §C answer)

> Tension to resolve: the starter is emphatic that the **change-detection gate** is
> deterministic and **never calls a model** ("anything that must give the same answer twice
> does not belong in a prompt"). Embedding similarity *is* a model call. So we must decide
> where embeddings sit relative to the gate.

- **O1** 🔵 Proposed split: **deterministic primary dedup** (GLIDE code / shared source IDs /
  same-hazard + ~100km + time window) drives the gate and the "is this a new event" decision;
  **semantic embeddings are an enrichment layer** that runs only in the model stage (only when
  the gate fires) to link fuzzy *text* records — chiefly ReliefWeb narratives — to an existing
  canonical event. Agree?
  **Lean:** yes — two layers; the gate stays deterministic, embeddings never gate a wake-up.
- **O2** 🔵 Embedding model/provider? Options: a **local** sentence-transformer in Python
  (e.g. `bge-small` / `all-MiniLM`), or a hosted embedder (Voyage, OpenAI).
  **Lean:** local sentence-transformer — no extra API key, cheap, runs in the Python pipeline;
  upgrade to hosted if match quality is poor.
- **O3** 🔵 Match scope + threshold — only compare candidates within the same hazard type and a
  space/time bucket, above a tuned cosine threshold, with the deterministic keys taking
  priority. OK?
  **Lean:** yes.
- **O4** 🔵 Do we persist vectors, or recompute for the (small) active set each run?
  **Lean:** recompute for the active window; persist only if volume makes it worthwhile.

## P. Stack & hosting (from §K/§M answer: Python + Vercel + Tailwind + shadcn/ui)

> shadcn/ui is React-based, so this replaces the earlier "self-contained `dashboard.html`"
> lean with a proper front-end app, and moves hosting off GitHub Pages. Several downstream
> decisions follow.

- **P1** 🔵 Front end = **Next.js + Tailwind + shadcn/ui on Vercel**; the pipeline emits
  structured JSON and the app renders it (map, report, analytics, insights). Confirm.
  **Lean:** yes. (Supersedes F1's self-contained-HTML lean.)
- **P2** 🔵 Where does the **scheduled Python pipeline** (ingest → dedup → gate → generate) run?
  - **(A)** GitHub Actions cron runs the Python pipeline, writes/commits data + triggers a
    Vercel redeploy/revalidate; Vercel just hosts the front end. *(Keeps the starter's
    unattended-cron shape; clean compute/host split; `claude`/embeddings run on a full runner.)*
  - **(B)** All on Vercel — Python serverless functions + **Vercel Cron**; state in Vercel
    storage. *(One platform, but serverless time limits + heavier state setup.)*
  **Lean:** (A) — GitHub Actions for scheduled compute, Vercel for hosting.
- **P3** 🔵 Report/insights generation via the **Anthropic Python SDK** (Claude) rather than the
  `claude -p` CLI, since the backend is Python. The deterministic gate still runs first,
  model-free. Confirm + pick a model tier.
  **Lean:** Anthropic Python SDK; a capable Claude model for the daily synthesis (bounded cost —
  once per morning, only on change).
- **P4** 🔵 Persistence for event history + dedup keys (+ optional vectors)?
  **Lean:** with P2-(A): JSON or SQLite committed to the repo (simple, diffable). With P2-(B):
  Vercel Postgres / Supabase.
- **P5** 🔵 Map library in React — **react-leaflet** (OSM tiles, no key) vs MapLibre/Mapbox
  (vector, needs key)?
  **Lean:** react-leaflet + OSM tiles for v1.
- **P6** 🔵 Confirm the clean boundary: the Python pipeline emits a **versioned JSON contract**
  (events + report + analytics + insights) that the Next.js app is the sole consumer of.
  **Lean:** yes.
- **P7** 🔵 Feeds in v1 — all three (ReliefWeb via the no-approval **RSS** fallback until an
  appname is granted)? You expanded outputs to all four; confirm feeds too.
  **Lean:** yes — GDACS + USGS + ReliefWeb(RSS) in v1.

## Q. AI generation model — who runs the model, when, and whose key (from §P3)

> Core tension: an **unattended 08:30 report "only on change"** needs a key available with no
> human present (a server/env key). **Viewer-entered keys** only exist when a human opens the
> page. These can't both be the *only* mechanism.

- **Q1** 🔵 Where/when is the report + insights generated?
  - **(A) Server key only** — scheduled pipeline generates with an env key; viewers read.
  - **(B) BYOK only (client-side)** — pipeline emits deterministic data only; all AI narrative
    generated in-browser with the viewer's key; **no unattended morning report**.
  - **(C) Hybrid** — server key generates the scheduled baseline report/insights unattended;
    viewers may optionally BYOK to regenerate / ask follow-ups live.
  **Lean:** (C) — keeps the morning report *and* honours viewer BYOK.
- **Q2** 🔵 How many providers in v1 — all three (Gemini/OpenAI/Claude) behind an abstraction,
  or one now + pluggable interface?
  **Lean:** one provider (Claude) behind a `Provider` interface for v1; add others later. If
  BYOK is client-side, browser→provider calls hit CORS/proxy issues that multiply per provider.
- **Q3** 🔵 Confirm the dedup split (§O1): deterministic gate + embedding *enrichment* that never
  gates a wake-up?
  **Lean:** yes.
- **Q4** 🔵 Given §P2(B) all-on-Vercel-serverless, how do embeddings run (a local model won't fit
  a serverless function)?
  - **(A)** Hosted embedding API (Voyage / OpenAI / Gemini).
  - **(B)** Reconsider §P2 — run the heavy pipeline on GitHub Actions, Vercel hosts only.
  - **(C)** Defer semantic dedup past v1; deterministic dedup only for now.
  **Lean:** (A) if staying all-Vercel; (B) is the most robust overall.

## R. Reshaped architecture after "BYOK only" (from §Q1)

> BYOK-only removes all server-side LLM calls. This reshapes the report, the scheduled job,
> and where the AI layer lives. Resolving these unblocks ADRs 0006–0008.

- **R1** ⚠️ Embedding key: a hosted embedding API in the Python pipeline needs a **server-side**
  key — it can't be BYOK (no viewer present). Options:
  - **(A)** Allow a small **server-side embedding key** (owner pays cents; separate from the
    pricey LLM narrative, which stays BYOK). — **Lean.**
  - **(B)** Do embeddings **client-side** too (viewer's key), so dedup enrichment only happens
    when a viewer is present. (Weakens server-side dedup.)
  - **(C)** **Defer** semantic embeddings past v1; deterministic dedup only server-side.
- **R2** 🔵 Confirm: the report + insights are **client-side, on-demand** — generated when the
  analyst opens the dashboard with a key. No unattended narrative; the scheduled job refreshes
  **data only**. **Lean:** yes.
- **R3** 🔵 What does the scheduled/server side actually do — a **Vercel Cron** job that refreshes
  feed data on a timer, or **on-demand** refresh (a serverless API route that re-fetches + caches
  when the page is opened)?
  **Lean:** Vercel Cron for a periodic data refresh + skip-if-unchanged; the front end reads the
  latest cached JSON.
- **R4** 🔵 Confirm the **BYOK security model**: provider abstraction lives in the front end;
  keys are stored only in the browser (localStorage), never sent to our backend; user can clear
  them; standard "your key is used directly from your browser" caveat shown.
  **Lean:** yes.
- **R5** 🔵 Confirm **graceful degradation**: without a key, the map + events + analytics
  (all deterministic) are fully visible; only the AI narrative/insights require a key.
  **Lean:** yes.
- **R6** 🔵 Note/constraint: **Vercel Hobby cron runs at most once/day**; intraday data refresh
  (§E2 wanted ~15–30 min) needs Vercel **Pro**, or accept daily refresh, or use on-demand (R3).
  Which? **Lean:** accept daily scheduled refresh for v1 + on-demand refresh when the page loads.
