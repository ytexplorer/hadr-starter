# GDACS

Global Disaster Alert and Coordination System (EU/UN). Multi-hazard: earthquakes,
cyclones, floods, volcanoes, drought, wildfires. Each event carries a colour-coded
alert level.

## Endpoint

GeoJSON event list (verified 6 Jul 2026):

    https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP

RSS alternative: `https://www.gdacs.org/xml/rss.xml`. Per-event detail hangs off
`url.details` inside each feature.

## Example response (truncated)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [141.845, 40.4353] },
      "properties": {
        "eventtype": "EQ",
        "eventid": 1550421,
        "episodeid": 1716583,
        "glide": "",
        "name": "Earthquake in Japan",
        "htmldescription": "Green M 4.6 Earthquake in Japan at: 06 Jul 2026 11:29:36.",
        "alertlevel": "Green",
        "alertscore": 1,
        "episodealertlevel": "Green",
        "episodealertscore": 0.0,
        "istemporary": "false",
        "iscurrent": "true",
        "country": "Japan",
        "fromdate": "2026-07-06T11:29:36",
        "todate": "2026-07-06T11:29:36",
        "datemodified": "2026-07-06T12:09:48",
        "iso3": "JPN",
        "source": "NEIC",
        "url": {
          "report": "https://www.gdacs.org/report.aspx?eventid=1550421&episodeid=1716583&eventtype=EQ",
          "details": "https://www.gdacs.org/gdacsapi/api/events/geteventdata?eventtype=EQ&eventid=1550421"
        }
      }
    }
  ]
}
```

> **Note — the list feed carries no population / exposure figure.** EVENTS4APP gives
> only the colour signal (`alertlevel` / `alertscore`). The truncated sample above has
> no population field, and none exists in the list feed — do not read exposure off it.
> Any affected-population number comes from the per-event **detail feed** below.

## Detail feed (`geteventdata`) — population exposure

Per-event detail hangs off `properties.url.details`:

    https://www.gdacs.org/gdacsapi/api/events/geteventdata?eventtype=EQ&eventid=1550421

The affected-population estimate is **GDACS's own** and is carried **verbatim** into the
contract's `affected` block (never recomputed — ADR 0007). Slice 2 captured detail fixtures
for the hazards active in the list feed this slice (EQ, TC, FL — see
`pipeline/tests/fixtures/gdacs_detail_<hazard>.json`) and pinned each hazard's exposure field.
The canonical map lives in `pipeline/pipeline/affected.py` (`_EXPOSURE_FIELDS` /
`extract_exposure`); reconcile to it if any field string below drifts. A hazard **absent** from
`_EXPOSURE_FIELDS` has no verified exposure field and ships `affected.estimate: null` with a
documented reason — never a hard-coded or guessed field (ADR 0007).

| Hazard | Exposure field (under detail `properties`)             | Notes                                  |
|--------|--------------------------------------------------------|----------------------------------------|
| EQ     | `earthquakedetails.rapidpop` (+ `rapidpopdescription`) | API-verified; population in an MMI exposure band (e.g. 43996 → "40 thousand in MMI IV"). Only hazard in `_EXPOSURE_FIELDS`. |
| TC     | none published — confirmed absent → `null` + reason    | `gdacs_detail_tc.json`: `severitydata` holds max wind speed (`severity`/`severitytext`/`severityunit`), not a population; `affectedcountries` is country names only, `images.populationmap` is a PNG URL. Omitted from `_EXPOSURE_FIELDS`. |
| FL     | none published — confirmed absent → `null` + reason    | `gdacs_detail_fl.json`: `severitydata` holds flood magnitude, not a population; `impacts`/`additionalinfos` empty. Omitted from `_EXPOSURE_FIELDS`. |
| VO     | none published — detail not captured this slice → `null` + reason | No active volcano in the list feed this slice; left out of `_EXPOSURE_FIELDS` (no unverified path, ADR 0007). Revisit when a VO detail can be captured. |
| DR     | none published — GDACS publishes no per-event count → `null` + reason | No active drought in the list feed this slice; not present in `_EXPOSURE_FIELDS`. |

Only **Orange/Red** events are detail-fetched (§7.5): they are the only ones that can clear the
`major` gate and be displayed. Any detail-fetch failure degrades to `affected.estimate: null`
plus a reason basis — it never blocks the build. Wording is always **"population exposed," never
"affected / casualties"**: `rapidpop` measures exposure, not impact (ADR 0007).

## Open questions

1. Every event carries `alertlevel`, `alertscore`, `episodealertlevel` and
   `episodealertscore`. Which of these is "the alert level" for reporting
   purposes — and can an event's colour change after you have already
   reported on it?
2. This event's `source` is `NEIC` — the same US agency behind the USGS feed.
   When the same physical earthquake arrives from two of your three feeds,
   what makes two records the same event?
3. GDACS publishes no rate limits and no uptime guarantees. What is a polite
   polling frequency, and what does your 08:30 report say on a morning the
   feed is down?
