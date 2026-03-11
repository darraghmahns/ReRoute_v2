# Reroute - AI-Powered Cycling Training Platform

A cycling training platform combining AI-powered route generation, training plan creation, performance tracking, and Strava integration.

## Quick Start

```bash
./dev.sh
```

This starts:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **GraphHopper**: http://localhost:8989

## Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Docker (for GraphHopper routing service)

### First Time Setup

1. **Set up map data** (required for routing):
   ```bash
   ./setup-maps.sh
   ```

2. **Install dependencies:**
   ```bash
   npm run install:all
   ```

3. **Set up environment variables:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

4. **Start development servers:**
   ```bash
   ./dev.sh
   ```

## Project Structure

```
reroute/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/             # Route handlers
│   │   ├── core/            # Configuration & security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   ├── alembic/             # Database migrations
│   └── tests/               # Backend tests
├── frontend/                # React frontend
│   └── src/
│       ├── components/      # UI components
│       ├── hooks/           # Custom React hooks
│       ├── pages/           # Page components
│       ├── services/        # API service layer
│       ├── store/           # State management (Zustand)
│       └── types/           # TypeScript types
├── dev.sh                   # Start all dev services
├── docker-compose.yml       # GraphHopper local service
└── railway.json             # Railway deployment config
```

## Key Features

- **Route Generation** — Montana-optimized routing via custom GraphHopper, multi-profile support (Road, Gravel, Mountain)
- **Training Plans** — AI-generated personalized plans with Strava data integration and progressive periodization
- **Performance Analytics** — FTP, TSS, Normalized Power, heart rate zones, recovery scores
- **Strava Integration** — OAuth, activity sync, real-time dashboard
- **AI Chat Agent** — Conversational interface for training and route queries
- **Subscription Tiers** — Free/paid tiers enforced via Stripe

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (Supabase in production) with SQLAlchemy 2.0 + Alembic
- **Auth**: FastAPI-Users with JWT
- **AI**: OpenAI GPT-4
- **Payments**: Stripe
- **Package manager**: uv

### Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite 5
- **UI**: Tailwind CSS + shadcn/ui (Radix UI)
- **State**: TanStack Query + Zustand
- **Maps**: Mapbox GL JS
- **Charts**: Recharts

## Development Commands

```bash
# Start all services
./dev.sh

# Install all dependencies
npm run install:all

# Build frontend (production)
npm run build

# Lint frontend
npm run lint

# Backend only
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Frontend only
cd frontend && npm run dev
```

## Environment Variables

### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql://user:pass@localhost/reroute
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
STRAVA_CLIENT_ID=your-strava-client-id
STRAVA_CLIENT_SECRET=your-strava-client-secret
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
SENDGRID_API_KEY=your-sendgrid-key
GRAPHHOPPER_URL=http://localhost:8989
```

### Frontend (auto-configured in dev)
```env
VITE_API_URL=http://localhost:8000
VITE_MAPBOX_TOKEN=your-mapbox-token
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Current user |
| POST | `/routes/generate` | Generate route |
| GET | `/routes` | List routes |
| POST | `/training/plans` | Generate training plan |
| GET | `/training/plans` | List plans |
| GET | `/strava/auth-url` | Strava OAuth URL |
| POST | `/strava/callback` | Strava OAuth callback |
| POST | `/strava/sync` | Sync Strava activities |
| POST | `/chat/message` | AI chat message |
| GET | `/analytics/...` | Performance analytics |

## License

MIT
