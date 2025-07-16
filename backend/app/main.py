from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, profiles, routes, training, strava, chat, analytics, subscription

app = FastAPI(title="Reroute - AI-Powered Cycling Training Assistant")

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

@app.get("/")
def root():
    return {"message": "Welcome to Reroute - AI-Powered Cycling Training Assistant API"}
