# cities.csv — provenance & license

`cities.csv` is a trimmed, column-reduced extract of the **GeoNames** `cities15000` gazetteer.

- **Source:** https://download.geonames.org/export/dump/cities15000.zip
  (all populated places with population ≥ 15,000; one tab-separated file `cities15000.txt`).
- **License:** Creative Commons Attribution 4.0 (**CC BY 4.0**) —
  https://creativecommons.org/licenses/by/4.0/. © GeoNames (https://www.geonames.org/).
  This project redistributes a filtered, column-reduced extract under the same license;
  attribution is retained here.

## Trim recipe (exactly reproducible)

From `cities15000.txt` (19 tab-separated GeoNames columns, no header line):

1. Keep a row when **population (col 14) ≥ 100000 OR feature_code (col 7) == "PPLC"**
   (PPLC = national capital).
2. Emit six columns: `name` (asciiname, col 2), `country` (country code, col 8),
   `lat` (col 4), `lon` (col 5), `population` (col 14),
   `capital` (`1` when feature_code == "PPLC", else `0`).
3. Sort rows by `(name, country)` for a stable, diff-friendly file; prepend the header row.

Produced by the one-off builder in the Slice-2 plan (Task 4, Step 1). No runtime code
downloads GeoNames — `boost.py` reads only this committed file, so the boost stays
deterministic and offline (CLAUDE.md conv. 1; spec §7.2).
