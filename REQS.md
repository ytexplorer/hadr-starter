# REQS — Global Crisis Dashboard for Newsrooms

> Raw idea capture. This is the starting point for the product-planning process
> (grill → PRD → shaping → breadboarding), not a finished spec. My structuring and
> interpretations are marked **_(to confirm)_**; the **Open questions** at the bottom
> are deliberately left for the grilling step to resolve.

## The idea (as first described)

> I want a crisis management dashboard, showing global disasters on a map. If there
> is any major event it should show on the map.
>
> For a media analyst.
>
> Morning report + dashboard + analytics + insights.
>
> I want a crisis online space if possible.

## What it is, in one line

A map-first global crisis dashboard that plots major disasters live on a world map,
so a newsroom analyst can see — at a glance — what happened, where, how bad, and who
is affected, and decide what is worth covering right now.

## Who it's for

- **Primary user: a newsroom / editorial media analyst.** Someone who monitors global
  crises to decide what to cover, brief editors, and surface story angles.
- Their core question is **newsworthiness**: *is this a story — where, how big, who's
  affected, and is it worth acting on now?*
- **_(to confirm)_** Single analyst / small desk to start; no per-user accounts.

## What it produces

Four connected outputs, one underlying pipeline:

1. **Live map dashboard** — a world map with markers for current major events. The
   primary surface. Click a marker → event detail (what/where/severity/affected/sources).
2. **Morning report** — a once-a-day situation summary of what matters, published on a
   schedule. **_(to confirm)_** aligns with the repo's stated 08:30 Singapore-time report.
3. **Analytics** — the quantitative view: counts, trends, severity/region breakdowns,
   how the picture is changing over time. **_(to confirm)_**
4. **Insights** — the qualitative "so what": why an event matters, escalation, and
   possible story angles for the newsroom. **_(to confirm)_** likely AI-generated
   narrative on top of the analytics.

## How it's delivered

- A **hosted, always-on web page** anyone with the link can open — deployed online, not
  just a local file.
- **Auto-refreshes** as the feeds update.
- **Read-only, no accounts** for now.
- Runs **unattended on a schedule**, and **stays quiet when nothing has changed** (from
  the repo's end-state; this product should keep that discipline).

## Data sources

The three feeds already documented in `feeds/`:

- **GDACS** — multi-hazard (quakes, cyclones, floods, volcanoes, drought, wildfires),
  colour-coded alert levels. GeoJSON event list.
- **USGS** — real-time earthquakes, GeoJSON, regenerated every minute.
- **ReliefWeb** — UN OCHA, curated/slower; a disaster appears once humans decide it
  matters. API needs a **pre-approved appname**; RSS fallback needs none.

## What "good" looks like

- The map shows the **major** events and doesn't drown the analyst in minor noise.
- The morning report is **worth reading** — signal, not a raw feed dump.
- The same real-world event arriving from multiple feeds shows up **once**, not three times.
- The analyst trusts it enough to act on it before checking the raw feeds themselves.

## Known hard problems (surfaced by the feeds themselves)

- **De-duplication across feeds** — the same earthquake can arrive from GDACS, USGS, and
  ReliefWeb under three different IDs on different days. What makes two records "the same
  event"?
- **Events get revised or deleted** — magnitude/location change; `status` moves from
  automatic to reviewed. What happens to a report/marker already published when the event
  changes underneath it?
- **Alert-level semantics** — GDACS carries several alert fields (`alertlevel`,
  `alertscore`, episode variants); USGS has its own `alert`. Which is "the" severity, and
  how do they map to a single "major event" threshold?
- **ReliefWeb access** — approved appname may not arrive in time; RSS is the fallback but
  lacks structure the API gives. What do we build against meanwhile?
- **Feed downtime & polite polling** — no published rate limits/uptime. What's a polite
  poll frequency, and what does the morning report say on a morning a feed is down?

## Open questions (for the grilling step)

1. **"Major event" threshold** — what precisely qualifies an event to appear on the map
   and in the report? Per hazard type? A unified severity score? Analyst-tunable?
2. **Analytics vs. insights** — confirm the split above. What specific analytics matter to
   a newsroom (frequency, region heatmap, escalation, historical comparison)?
3. **Geographic scope** — truly global, or is there a home region / editorial priority
   weighting?
4. **Report timing & timezone** — is 08:30 Singapore time right for this audience, or
   should it follow the newsroom's timezone?
5. **How "live" is live** — refresh interval for the hosted dashboard (minutes? on each
   scheduled run?). Real-time push is explicitly **out of scope for now**.
6. **Sources & credibility** — should each event show its source feeds and link out, so the
   analyst can verify before reporting?
7. **History & persistence** — do we keep past events for trend analytics, and for how long?
8. **Hosting** — where does the "online space" live, and how is it deployed/updated?

## Explicitly out of scope (for now)

- Real-time push / streaming "situation room" beyond scheduled auto-refresh.
- Multi-user collaboration, annotations, story-claiming, accounts.
- Feeds beyond GDACS / USGS / ReliefWeb.
