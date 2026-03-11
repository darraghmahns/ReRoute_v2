# MEMORY.md — Reroute

## Current Project Stage

**Active Development** — Core features built and deployed to Railway + Supabase.

## Session Startup Files

1. `memory/project-details.md`
2. `memory/MEMORY.md`
3. `memory/build-log.md`

## Confirmed Decisions

| Decision | Rationale | Date |
|---|---|---|
| Railway + Supabase for deployment | Simpler ops than GCP/self-hosted | 2025-03 |
| uv for Python dependency management | Faster than Poetry | 2025 |
| FastAPI-Users for auth | Full-featured, JWT + Alembic friendly | 2025 |
| Stripe for subscriptions | Industry standard, webhook support | 2025 |
| OpenAI GPT-4 for AI features | Best quality for training/route AI | 2025 |
| Custom GraphHopper server (separate service) | Montana-optimized routing profiles | 2025 |
| Frontend bundled into backend/static/ at build time | Single Railway service, no CORS issues | 2025-03 |
| GraphHopper moved into monorepo (`graphhopper/`) | Single git push deploys both services | 2026-03 |

## Pending Decisions

| Decision | Blocked by |
|---|---|
| Redis/Celery in production | Need to decide if Railway Redis addon is needed or simplify to sync tasks |
| Subscription tier pricing and feature gates | Product decision |

## Key Warnings / Gotchas

- README.md says "Poetry" but project uses `uv` — README is outdated
- `package.json` and `package-lock.json` at root are gitignored (dev convenience only)
- GraphHopper runs as a separate local service via docker-compose; in production it must be a separate Railway service or self-hosted
- `backend/reroute.db` is a SQLite dev artifact — not used in production (PostgreSQL only)
