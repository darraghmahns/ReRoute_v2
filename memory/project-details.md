# Reroute — Project Details

## Mission

AI-powered cycling training platform combining route generation, training plan creation, performance tracking, and Strava integration.

## Current Stage

**Active Development** — Core features built, deployed to Railway + Supabase. AI agent and subscription tiers recently implemented.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (Supabase in production) with SQLAlchemy 2.0 + Alembic migrations
- **Auth**: FastAPI-Users with JWT
- **AI**: OpenAI GPT-4 (`openai` SDK)
- **Task Queue**: Celery + Redis
- **Package manager**: `uv` (not Poetry — README is outdated)
- **Payments**: Stripe (subscription tiers)
- **Email**: SendGrid
- **Maps/Routing**: Custom GraphHopper server (separate service)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite 5
- **UI**: Tailwind CSS 3.4 + shadcn/ui (Radix UI)
- **State**: TanStack Query + Zustand
- **Forms**: React Hook Form + Zod
- **Maps**: Mapbox GL JS
- **Charts**: Recharts

### Deployment
- **Platform**: Railway (backend + frontend built into backend static/)
- **Database**: Supabase PostgreSQL
- **Config**: `railway.json` at repo root
- **Build**: Frontend built during Railway deploy, output to `backend/static/`

## Repo Structure

```
reroute/
├── CLAUDE.md                   # Project AI instructions
├── memory/                     # Claude's memory (git-tracked, symlinked)
│   ├── MEMORY.md
│   ├── build-log.md
│   └── project-details.md
├── docs/                       # Project documentation
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/                # Route handlers: auth, chat, profiles, routes, strava, subscription, training, analytics
│   │   ├── core/               # Config & security
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # Business logic (ai_agent, graphhopper, openai_chat, route_generator, strava, training_plan_generator, usage_service, etc.)
│   ├── alembic/                # DB migrations
│   └── tests/                  # Backend tests
├── frontend/                   # React frontend
│   └── src/
│       ├── components/         # UI components (Navigation, RouteMap, StravaConnection, etc.)
│       ├── hooks/              # Custom hooks
│       ├── pages/              # Page components
│       ├── services/           # API service layer
│       ├── store/              # Zustand stores
│       ├── types/              # TypeScript types
│       └── utils/
├── graphhopper/                # GraphHopper service (Dockerfiles + routing profiles)
│   ├── Dockerfile              # Production — downloads Montana OSM at build, port 8080
│   ├── Dockerfile.local        # Local dev — expects mounted /data volume, port 8989
│   ├── config.gcp.yml          # Production config (copied as config/config.yml in Dockerfile)
│   ├── config.yml              # Local dev config
│   ├── config.local.yml        # Local dev config for Dockerfile.local
│   ├── bike.json               # Road bike routing profile
│   ├── gravel.json             # Gravel bike routing profile
│   └── mountain.json           # Mountain bike routing profile
├── dev.sh                      # Start all dev services
├── dev-logs.sh                 # View dev logs
├── docker-compose.yml          # GraphHopper local service
├── railway.json                # Railway deployment config
└── setup-maps.sh               # GraphHopper map data setup
```

## Key Features

- **Route Generation**: Montana-optimized routing via custom GraphHopper + Mapbox display
- **Training Plans**: AI-generated personalized plans (OpenAI GPT-4)
- **Strava Integration**: OAuth, activity sync, performance metrics
- **Analytics**: FTP, TSS, Normalized Power, training zones, recovery scores
- **AI Chat Agent**: Conversational interface for training/route queries
- **Subscription Tiers**: Free/paid tiers enforced via Stripe + usage_service

## API Endpoints (key)

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `POST /routes/generate`, `GET /routes`, `GET /routes/{id}`
- `POST /training/plans`, `GET /training/plans`
- `GET /strava/auth-url`, `POST /strava/callback`, `POST /strava/sync`
- `POST /chat/message`, `GET /chat/history`
- `GET /analytics/...`

## Environment Variables

### Backend
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT secret
- `OPENAI_API_KEY`
- `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `SENDGRID_API_KEY`
- `GRAPHHOPPER_URL`

### Frontend
- `VITE_API_URL`
- `VITE_MAPBOX_TOKEN`

## Team

- **Darragh Mahns** — Solo developer (darraghmahns@gmail.com)
