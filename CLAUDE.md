# Reroute — Project Instructions for Claude

## Session Startup

Read these files at the start of every substantive session:
1. `memory/project-details.md`
2. `memory/MEMORY.md`
3. `memory/build-log.md`

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + Alembic + FastAPI-Users
- **Database**: PostgreSQL (Supabase in production), SQLite for local dev
- **Package manager**: `uv` (NOT Poetry — README.md is outdated on this)
- **Frontend**: React 18 + TypeScript + Vite + Tailwind + shadcn/ui
- **AI**: OpenAI GPT-4 via `openai` SDK
- **Payments**: Stripe
- **Deployment**: Railway (single service — frontend built into backend/static/)
- **Routing**: Custom GraphHopper server (separate service, local via docker-compose)

## Docs Structure

```
docs/
└── (planning docs, research, architecture notes)
```

## Domain-Specific Security Rules

In addition to the global security rules:

- **Stripe webhooks**: always verify webhook signatures before processing
- **Strava OAuth**: never log or store raw access/refresh tokens in plaintext
- **JWT**: use short expiry; refresh token rotation required
- **Subscription enforcement**: check subscription tier server-side on every restricted endpoint — never trust client claims about tier

## Quality Gates (additions to global)

A feature is also done when:
- Subscription enforcement has been verified (restricted endpoints return 403 for free tier)
- Strava-dependent features gracefully handle disconnected state
- AI calls have timeout handling (OpenAI can be slow)

## Commit Message Convention

Format: `<type>: <what and why>`
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

## Notes

- `graphhopper-data/` is gitignored (large map files, generated locally)
- `backend/reroute.db` is a SQLite dev artifact — never commit, never use in production
- In production, Redis/Celery may be simplified — check MEMORY.md pending decisions
