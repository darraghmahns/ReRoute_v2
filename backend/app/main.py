import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import app.models.route as route_models  # ensure Route models are registered
import app.models.strava as strava_models  # ensure StravaActivity is registered
from app.api import (
    analytics,
    auth,
    chat,
    profiles,
    routes,
    strava,
    subscription,
    training,
)
from app.core.database import Base, engine

app = FastAPI(title="Reroute - AI-Powered Cycling Training Assistant", version="1.0.1")

# CORS settings for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(routes.router)
app.include_router(training.router)
app.include_router(strava.router)
app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(subscription.router)


# Try to create database tables, fall back gracefully if database is not available
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")
    print("Application will continue without database functionality")

# Mount static files (React frontend)
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(static_dir, "index.html"))

    # Serve static assets with correct MIME types
    @app.get("/assets/{file_path:path}")
    async def serve_assets(file_path: str):
        asset_path = os.path.join(static_dir, "assets", file_path)
        if os.path.exists(asset_path):
            return FileResponse(asset_path)
        return {"error": "Asset not found"}

    # Specific route for strava assets
    @app.get("/strava/{file_path:path}")
    async def serve_strava_assets(file_path: str):
        asset_path = os.path.join(static_dir, "strava", file_path)
        if os.path.exists(asset_path):
            return FileResponse(asset_path)
        return {"error": "Strava asset not found"}

    # Catch-all route for React Router (must be last)
    # This serves the React app for all non-API, non-static routes
    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        # If it's a static asset, try to serve it
        if "." in full_path:
            asset_path = os.path.join(static_dir, full_path)
            if os.path.exists(asset_path):
                return FileResponse(asset_path)

        # For all other routes (including /auth, /profile, /strava-callback, etc.)
        # serve the React app and let React Router handle the routing
        return FileResponse(os.path.join(static_dir, "index.html"))

else:

    @app.get("/")
    def root():
        return {
            "message": "Welcome to Reroute - AI-Powered Cycling Training Assistant API"
        }
