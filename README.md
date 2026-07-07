# HADR Monitor

A monitoring agent for humanitarian assistance and disaster response (HADR).

## The end state

By Wednesday afternoon this repository contains an agent that:

- watches live disaster feeds — GDACS, USGS and ReliefWeb (see `feeds/`)
- filters out the noise and assesses what remains: what happened, where, how bad, who is affected
- publishes a morning situation report to `dashboard.html` at 08:30 Singapore time
- runs on a schedule, unattended, and stays quiet when nothing has changed

How it does any of that is not specified anywhere in this repository. That is the course.

## The three days

1. **Plan** — interrogate the feeds, write the PRD, cut it into vertical slices
2. **Autonomy** — build the first slice, write a skill, wire up the 08:30 routine, launch the overnight loop
3. **Trust** — review code you didn't write, harden the pipeline, demo

## Artefacts expected by the end

`prd.html` · `system-view.html` · `implementation-notes.md` · `dashboard.html` · `goal.md` · at least one skill

## Day 1 setup

1. Sign in to Claude Code with your Team seat
2. Create your own repository from this template, then clone it
3. Run `/install-github-app` so @claude reviews your pull requests from Day 2
4. Install OpenCode and sign in with your Go key

Fill in `CLAUDE.md` before your first prompt.

## Run Slice 1 locally

Slice 1 (USGS → contract → map/list/detail) runs entirely on your machine — no deploy
required. Two terminals:

```bash
# Terminal 1 — pipeline: serves the contract route on http://localhost:8000/api/contract
cd pipeline
uv run python serve_local.py
```

```bash
# Terminal 2 — front end: dashboard on http://localhost:3000
cd web
pnpm dev
```

The front end reads the contract URL from `web/.env.local` (gitignored — create it
yourself, it is not committed):

```
NEXT_PUBLIC_CONTRACT_URL=http://localhost:8000/api/contract
```

With both running, `http://localhost:3000` renders live USGS earthquake markers on the
map and a synced event list — no API key needed for this slice.
