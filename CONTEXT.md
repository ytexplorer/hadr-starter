# CONTEXT — shared language for the Global Crisis Dashboard

> The team's shared vocabulary. One agreed meaning per term, so the PRD, shaping, and code
> all use words the same way. Terms marked **_(provisional)_** are not yet confirmed — they
> firm up as `QUESTIONS.md` is answered. Built during the grilling step.

## The product

- **Global Crisis Dashboard** — working name. A map-first web dashboard that plots major
  global disasters live, for a newsroom analyst deciding what's worth covering.
- **HADR** — Humanitarian Assistance and Disaster Response; the domain this monitors.

## People

- **Analyst** — the primary (and, for v1, only) user: a **newsroom / editorial** media
  analyst. Their driving question is **newsworthiness**: *what happened, where, how bad,
  who's affected — and is it worth a story now?*

## Events

- **Event** — one real-world disaster occurrence (an earthquake, cyclone, flood, etc.),
  regardless of how many feeds report it.
- **Feed record** — a single feed's representation of an event. Multiple feed records can
  describe one Event.
- **Canonical event** — the single merged Event we store and display after de-duplicating
  feed records. **_(provisional — merge rules in QUESTIONS C)_**
- **De-duplication** — collapsing multiple feed records of the same real-world occurrence
  into one canonical event. Two layers:
  - **Deterministic dedup** — key/geo/time matching (GLIDE, shared IDs, same-hazard +
    proximity + time window). Runs in the model-free gate; decides "is this a new event".
  - **Semantic dedup (enrichment)** — embedding-similarity matching of fuzzy *text* records
    (esp. ReliefWeb narratives) to a canonical event. Runs only in the model stage, only when
    the gate has already fired. Never gates a wake-up. **_(design in QUESTIONS §O)_**
- **Hazard type** — the kind of disaster: earthquake, cyclone, flood, volcano, drought,
  wildfire (GDACS taxonomy).
- **Major event** — an event severe/newsworthy enough to show by default. Gated by
  **Severity** above a fixed default threshold (analyst filters can widen/narrow). See ADR 0003.
- **Severity** — a single internal measure derived from feed alert levels + hazard-specific
  signals (GDACS colour; USGS `mag`/`sig`/`alert`), tuned per hazard. See ADR 0003.
- **Newsworthiness boost** — an uplift to Severity for events near population centres /
  capital cities, so editorially significant events aren't buried by raw magnitude. In v1.
- **Alert level** — a feed's own severity marker: GDACS colour (Green/Orange/Red);
  USGS `alert` and `mag`/`sig`. These are inputs to our Severity, not our final word.
- **Revision** — an upstream change to an already-seen event (magnitude, location, status).
- **Retraction** — an event deleted upstream after we showed it. **_(provisional handling)_**
- **Active window** — how long an event stays on the live map before dropping to history
  only. **_(provisional — QUESTIONS D2)_**
- **Provisional event** — a USGS `automatic` (unreviewed) event, shown but badged.

## Outputs

- **Dashboard** — the always-on, hosted, read-only, auto-refreshing web page. The primary
  surface. Publishes as `dashboard.html`.
- **Morning report** / **sitrep** — the once-daily situation summary (target 08:30
  Asia/Singapore), regenerated **only when something changed**.
- **Analytics** — the quantitative view: counts and trends by hazard / region / severity
  over time. **_(scope in QUESTIONS H)_**
- **Insights** — the AI-generated qualitative view: *why it matters* and possible story
  angles, layered on the events + analytics, strictly grounded in feed data.
  **_(scope in QUESTIONS I)_**

## Data sources

- **GDACS** — EU/UN multi-hazard feed with colour-coded alert levels (GeoJSON).
- **USGS** — US Geological Survey real-time earthquake feed (GeoJSON, per-minute).
- **ReliefWeb** — UN OCHA curated humanitarian feed; API needs an approved **appname**,
  RSS is the no-approval fallback.
- **GLIDE** — a global disaster identifier that can appear across feeds; a candidate key
  for cross-feed de-duplication.

## Pipeline & operations

- **Change-detection gate** — a deterministic script (`scripts/`) that decides *whether
  anything changed* since the last run. It **never calls a model**. "The model never
  decides whether to wake up."
- **Sitrep run** — the scheduled job: run the gate; only if it reports change, invoke
  headless Claude (`claude -p`) via a `/sitrep` skill to regenerate the report + dashboard.
- **Quiet-when-nothing-changed** — on a no-change cycle, nothing is regenerated or notified.
- **Scheduler** — GitHub Actions cron (per the starter's `sitrep.yml`). **_(provisional —
  QUESTIONS L1)_**
- **State/history** — stored past events used for de-dup across days, revision tracking, and
  analytics, held in **Vercel-hosted storage** (Postgres or KV/Blob; exact choice at spec time).

## Stack (see ADR 0006 / 0007)

- **Pipeline** — the **Python** program that ingests feeds, de-duplicates, runs the gate, and
  (on change) generates the report + insights. Emits a versioned **JSON contract**.
- **Front end** — a **Next.js + Tailwind + shadcn/ui** app on **Vercel**; the sole consumer of
  the JSON contract; renders map, report, analytics, insights. Read-only.
- **Runner** — the pipeline runs on **Vercel** (serverless functions; state in Vercel storage) —
  §P2(B). Refresh = **daily Vercel Cron + on-demand refresh on page load** (§R3/§R6).
- **Embedder** — a **hosted embedding API** (not a local model) used for semantic dedup
  enrichment; needs a **server-side embedding key** (§R1). Distinct from the LLM keys below.
- **BYOK (bring your own key)** — the LLM layer is **client-side only**: the viewer supplies
  their own **Gemini / OpenAI / Claude** key on the webapp; it is stored in the browser
  (localStorage), used to call the provider directly from the browser, and never sent to our
  backend. The provider abstraction lives in the **front end**, not the Python pipeline.
- **On-demand generation** — because there is no server-side LLM, the report + insights are
  generated **client-side when the analyst opens the dashboard with a key**. There is no
  unattended narrative report; the scheduled job refreshes **data only**.
- **Graceful degradation** — map + events + analytics (all deterministic) render **without** a
  key; only the AI narrative requires one.
- **JSON contract** — the single, versioned data hand-off from pipeline → front end. The
  front end talks to feeds/LLM only via this contract (data) and the viewer's key (LLM).
