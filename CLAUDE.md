# CLAUDE.md

Working conventions for the **Global Crisis Dashboard**. This file records *how we build*;
`docs/adr/` records *what we decided* (authoritative, append-only). The shaped feature is
PRD issue #2.

## Language & tooling

Two halves joined **only** by the versioned **JSON contract** (ADR 0006). No shared runtime
code crosses that boundary — the contract schema is the shared artefact.

**Pipeline (Python)** — runs as Vercel Python serverless functions; ingest → dedup → severity
→ analytics → gate → emit contract.
- Python 3.12 (pin to a Vercel-supported runtime in `vercel.json` at setup).
- Dependencies + venv via **uv** (`pyproject.toml` + committed `uv.lock`).
- Lint & format: **ruff**. Types: **mypy** (type hints on public functions).
- HTTP via `httpx`; keep the GDACS/USGS (GeoJSON) and ReliefWeb (RSS) parsers separate and
  swappable — ReliefWeb RSS→API later must be a contained change (ADR 0006).

**Front end (TypeScript)** — Next.js App Router + Tailwind + shadcn/ui; map via
**react-leaflet + OSM tiles** (no key). Sole, read-only consumer of the JSON contract.
- Package manager: **pnpm** (committed `pnpm-lock.yaml`); Node pinned via `.nvmrc`.
- TypeScript **strict**. Lint/format: ESLint (next config) + Prettier.
- The BYOK `Provider` abstraction and browser key handling live here, never in the Pipeline
  (ADR 0007).

## Test command

Test **external behaviour at the highest seam** (see the PRD's Testing Decisions):
- **Pipeline** — `uv run pytest`. Drive feed fixtures in, assert the emitted JSON contract out.
- **Front end** — `pnpm test` (**Vitest** + React Testing Library). Feed a contract fixture in,
  assert what renders — including graceful degradation with no key.

Mock **only** at the three network edges (feeds, Embedder, LLM `Provider`); *control* the
State/history store and a fixed clock for stateful and time-relative cases. Never test private
internals.

## Conventions

1. **Determinism is model-free.** Anything that must give the same answer twice does not belong
   in a prompt. The change-detection gate and all pipeline *decisions* are deterministic; the
   only model call is the hosted Embedder for semantic enrichment, which **never** gates a
   wake-up (ADR 0005; `scripts/README.md`).
2. **One boundary — the versioned JSON contract.** The front end reads feed data only via the
   contract and the LLM only via the viewer's key. Bump the schema version on any breaking
   change; the two halves evolve independently (ADR 0006).
3. **Two key types, never crossed.** A server-side embedding key (owner-paid) for the Pipeline;
   client-side BYOK LLM keys (localStorage, never sent to our backend, clearable) for the front
   end. No server-side LLM key exists (ADR 0007). Secrets live in `.env` (gitignored) — never
   commit or print a key.
4. **Grounded AI only.** Insights/report may interpret only data present in the contract; every
   claim traceable to a source feed; explicit uncertainty; no fabricated numbers (ADR 0007).
5. **Ship vertical slices.** Work is cut into thin end-to-end slices (issue template
   `slice.md`), each observable and checkable. First slice: USGS + GDACS → dedup → map of Major
   events → report view.
6. **ADRs are authoritative and append-only.** Respect the ADRs in any area you touch; to change
   a decision, add a superseding ADR — don't rewrite one.

## Deviations policy

Anything built that departs from the PRD or this file is recorded in `implementation-notes.md`
with the reason — an undocumented deviation is a bug. A deviation that changes an architecture
decision becomes a new ADR that supersedes the old one.
