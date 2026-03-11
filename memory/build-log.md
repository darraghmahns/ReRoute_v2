# Build Log — Reroute

## Session: 2026-03-11 — Repo Setup

### What was done
- Set up project per global CLAUDE.md standards
- Created `memory/` directory with MEMORY.md, build-log.md, project-details.md
- Created `docs/` directory
- Created project `CLAUDE.md`
- Symlinked Claude's auto-memory directory to `memory/`

### Decisions made

| Decision | Rationale |
|---|---|
| Keep standard dev files at repo root (dev.sh, railway.json, docker-compose.yml, etc.) | These are standard project files, not documentation — moving them would break tooling |
| README.md stays at root | GitHub convention; displays on repo home page |

### Files updated

| File | What changed | Why |
|---|---|---|
| memory/MEMORY.md | Created | Session startup quick reference |
| memory/build-log.md | Created | Session history tracking |
| memory/project-details.md | Created | Full project context |
| CLAUDE.md | Created | Project-specific AI instructions |
| docs/ | Created (empty) | Documentation home |

### Current state

Project is structured per global CLAUDE.md. Memory system is active and symlinked. No code was changed — this was a documentation/structure-only session.

---

## Session: 2026-03-11 — Fix Deployment Blockers

### What was done

Implemented all items from the "Fix Deployment Blockers" audit plan:

1. **Rate limiting** — Added `slowapi` dependency; created `backend/app/core/limiter.py` with shared `Limiter` instance; added `SlowAPIMiddleware` + exception handler to `main.py`; added `@limiter.limit(...)` decorators to route generation (5/min), chat (20/min), and training plan generation (3/min) endpoints.

2. **Subscription enforcement gaps** — Added `check_and_log_usage(db, current_user, "route_generation", limit_free=3)` to 5 previously-unchecked endpoints: `POST /routes/generate`, `POST /routes/loops`, `POST /routes/generate-workout`, `POST /routes/simulate-race`, `GET /routes/{route_id}/suggestions`. Refactored `/loops` to call service directly (avoiding double-count with `/generate`).

3. **Config startup validation** — Added `validate_production_config()` to `Settings` in `config.py`; added FastAPI `startup` event handler in `main.py` that calls it (skipped when `USE_SQLITE=True`); removed `Base.metadata.create_all()` fallback block.

4. **Removed `GET /chat/debug`** — Unauthenticated endpoint calling OpenAI deleted from `chat.py`.

5. **Removed debug console.logs** — 9 `console.log('Training Debug: ...')` statements removed from `Training.tsx`; kept 2 `console.error()` calls.

6. **Error boundary** — Created `frontend/src/components/ErrorBoundary.tsx`; wrapped `<App>` in `main.tsx`.

### Decisions made

| Decision | Rationale |
|---|---|
| Shared limiter in `app/core/limiter.py` | Avoids circular imports; importable from any route module |
| `/loops` calls service directly (not `generate_route` fn) | Prevents double-counting subscription usage |
| Use `http_request: Request` parameter name in training.py | `request` was already taken by `GeneratePlanRequest` body param |

### Files updated

| File | What changed | Why |
|---|---|---|
| `backend/pyproject.toml` | Added `slowapi>=0.1.9` | Rate limiting dependency |
| `backend/app/core/limiter.py` | Created | Shared slowapi Limiter instance |
| `backend/app/main.py` | Rate limiting middleware, startup validation, removed `create_all()` | Deployment blocker fixes |
| `backend/app/core/config.py` | Added `validate_production_config()` | Catch missing prod secrets at startup |
| `backend/app/api/routes.py` | Rate limits + subscription checks on 5 endpoints | Security/billing enforcement |
| `backend/app/api/chat.py` | Rate limit on `/message`, removed `/debug` | Security |
| `backend/app/api/training.py` | Rate limit on `/plans/generate` | Prevent abuse |
| `frontend/src/components/ErrorBoundary.tsx` | Created | React error boundary |
| `frontend/src/main.tsx` | Wrapped app with ErrorBoundary | Catch unhandled React errors |
| `frontend/src/pages/Training.tsx` | Removed 9 debug console.log statements | Clean production logs |

### Current state

All deployment blockers closed. App ready for production charging. Pending: install `slowapi` via `uv` in the backend environment before next deploy.

---

## Session: 2026-03-11 — Monorepo + Railway Deployment

### What was done

Moved GraphHopper from sibling repo into monorepo and wired up deployment config.

1. **`graphhopper/` directory** — copied Dockerfile, Dockerfile.local, config.gcp.yml, config.yml, config.local.yml, bike.json, gravel.json, mountain.json from `../reroute-graphhopper-server/`
2. **`docker-compose.yml`** — updated build context from `../reroute-graphhopper-server` to `./graphhopper`
3. **`backend/app/core/config.py`** — changed `GRAPHHOPPER_BASE_URL` default to `http://localhost:8989`; added localhost guard to `validate_production_config()`
4. **`backend/requirements.txt`** — added `slowapi==0.1.9` (was in pyproject.toml but not requirements.txt used by Dockerfile)
5. **`backend/app/main.py`** — added `GET /health` endpoint (railway.json healthcheck target)
6. **`memory/project-details.md`** — updated repo structure to include `graphhopper/`

### Decisions made

| Decision | Rationale |
|---|---|
| Move GraphHopper into monorepo | Single git push deploys both services; simpler ops |
| `GRAPHHOPPER_BASE_URL` default → localhost:8989 | Was pointing at old Render URL; local dev should work out of the box |

### Files updated

| File | What changed | Why |
|---|---|---|
| `graphhopper/` | Created (8 files) | Moved from sibling repo |
| `docker-compose.yml` | Build context → `./graphhopper` | Monorepo path |
| `backend/app/core/config.py` | Default URL + localhost production guard | Correct default; catch missing Railway env var |
| `backend/requirements.txt` | Added `slowapi==0.1.9` | Dockerfile uses pip -r requirements.txt, not pyproject.toml |
| `backend/app/main.py` | Added `GET /health` | railway.json healthcheck |
| `memory/project-details.md` | Added `graphhopper/` to repo structure | Accuracy |

### Current state

All code changes done. Next step: Railway UI setup per the plan (Part 2). GraphHopper service needs to be created as a second Railway service pointing at the same repo with root directory `graphhopper`.

---

## Previous Development History (from git log)

| Commit | Summary |
|---|---|
| f235948 | Add deployment config for Railway + Supabase |
| c89ba95 | Clean up repo: remove unused files and GCP-specific configs |
| 382affa | Implement Phase 1 & 2: Fix AI Agent and add subscription tier enforcement |
| 68d9ead | Add detailed debugging to workout update function |
| adabc75 | Fix multiple active training plans issue |
