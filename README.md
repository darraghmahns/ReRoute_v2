# Reroute - AI-Powered Cycling Training Platform

A comprehensive cycling training platform that combines AI-powered route generation, training plan creation, performance tracking, and Strava integration.

## 🚀 Quick Start

### Option 1: Using the shell script (Recommended)
```bash
./dev.sh
```

### Option 2: Using npm
```bash
npm run dev
```

Both methods will start:
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Poetry (for backend dependencies)

### First Time Setup

1. **Install all dependencies:**
   ```bash
   npm run install:all
   ```

2. **Set up environment variables:**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   
   # Frontend
   cp frontend/.env.example frontend/.env.local
   # Edit frontend/.env.local with your API URL
   ```

3. **Start development servers:**
   ```bash
   ./dev.sh
   # or
   npm run dev
   ```

## 📁 Project Structure

```
reroute/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Configuration & security
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── alembic/            # Database migrations
│   └── tests/              # Backend tests
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── store/          # State management
│   │   └── types/          # TypeScript types
│   └── public/             # Static assets
└── dev.sh                  # Development script
```

## 🎯 Key Features

### AI-Powered Route Generation
- Montana-optimized routing with highway avoidance
- Custom GraphHopper server integration
- Multi-profile support (Road, Gravel, Mountain)
- SRTM elevation data integration

### Training Plan Generation
- AI-powered personalized training plans
- Strava data integration for plan optimization
- Progressive training with periodization
- Equipment and schedule consideration

### Performance Analytics
- Power-based metrics (FTP, TSS, Normalized Power)
- Heart rate analysis and training zones
- Weekly activity summaries and trends
- Recovery score and training intensity tracking

### Strava Integration
- OAuth authentication flow with popup window
- Activity synchronization and caching
- Real-time dashboard with actual cycling data
- Performance metrics and analytics
- Settings page for connection management

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with PostGIS
- **ORM**: SQLAlchemy 2.0 with Alembic
- **Authentication**: JWT with FastAPI-Users
- **AI**: OpenAI GPT-4 integration
- **Task Queue**: Celery with Redis

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 5
- **UI Library**: Tailwind CSS 3.4+
- **Component Library**: shadcn/ui (Radix UI)
- **State Management**: TanStack Query + Zustand
- **Forms**: React Hook Form with Zod validation
- **Maps**: Mapbox GL JS
- **Charts**: Recharts

## 🔧 Development Commands

```bash
# Start development servers
./dev.sh                    # Shell script
npm run dev                 # npm script

# Install dependencies
npm run install:all         # Install all dependencies

# Build frontend
npm run build               # Build for production

# Lint frontend
npm run lint                # Run ESLint

# Backend only
cd backend
poetry install              # Install Python dependencies
uvicorn app.main:app --reload --port 8002

# Frontend only
cd frontend
npm install                 # Install Node dependencies
npm run dev                 # Start Vite dev server
```

## 🌐 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Current user info

### Routes
- `POST /routes/generate` - Generate new route
- `GET /routes` - List user routes
- `GET /routes/{id}` - Get specific route

### Training
- `POST /training/plans` - Generate training plan
- `GET /training/plans` - List user plans

### Strava
- `GET /strava/auth-url` - Get OAuth URL
- `POST /strava/callback` - Handle OAuth callback
- `POST /strava/sync` - Sync activities from Strava
- `GET /strava/activities` - Get cached activities
- `POST /strava/zones` - Fetch athlete zones
- `DELETE /strava/disconnect` - Disconnect Strava

### Chat
- `POST /chat/message` - Send chat message
- `GET /chat/history` - Get conversation history

## 🔐 Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost/reroute
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
STRAVA_CLIENT_ID=your-strava-client-id
STRAVA_CLIENT_SECRET=your-strava-client-secret
```

### Frontend (.env.local)
```env
VITE_API_URL=http://localhost:8002
VITE_MAPBOX_TOKEN=your-mapbox-token
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 🚴 Strava Setup

For detailed instructions on setting up Strava integration, see [STRAVA_SETUP.md](STRAVA_SETUP.md).

## 📄 License

MIT License - see LICENSE file for details. 