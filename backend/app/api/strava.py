from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User, Profile
import requests
from typing import Optional
import json
import logging

router = APIRouter(prefix="/strava", tags=["strava"])

@router.get("/auth-url")
def get_auth_url():
    """Get Strava OAuth URL"""
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={settings.STRAVA_CLIENT_ID}&response_type=code&redirect_uri={settings.STRAVA_REDIRECT_URI}&approval_prompt=force&scope=read,activity:read_all,profile:read_all"
    return {"auth_url": auth_url}

@router.post("/callback")
async def handle_callback(request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Handle OAuth callback"""
    try:
        # Get the authorization code from the request
        body = await request.json()
        code = body.get("code")
        
        if not code:
            logging.error("No authorization code received in callback.")
            raise HTTPException(status_code=400, detail="Authorization code required")
        
        # Exchange code for access token
        token_url = "https://www.strava.com/oauth/token"
        token_data = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code != 200:
            logging.error(f"Failed to exchange code for token: {response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        token_info = response.json()
        
        # Get athlete info
        athlete_response = requests.get(
            "https://www.strava.com/api/v3/athlete",
            headers={"Authorization": f"Bearer {token_info['access_token']}"}
        )
        
        if athlete_response.status_code == 200:
            athlete_data = athlete_response.json()
            
            # Update user's profile with Strava info
            profile = db.query(Profile).filter(Profile.id == current_user.id).first()
            if not profile:
                profile = Profile(id=current_user.id)
                db.add(profile)
            
            profile.strava_user_id = str(athlete_data.get("id"))
            profile.strava_access_token = token_info.get("access_token")
            profile.strava_refresh_token = token_info.get("refresh_token")
            # Note: Strava tokens don't expire, but we'll store the expiry just in case
            profile.strava_token_expires_at = None
            
            db.commit()
            
            return {
                "message": "Strava connected successfully",
                "athlete": {
                    "id": athlete_data.get("id"),
                    "firstname": athlete_data.get("firstname"),
                    "lastname": athlete_data.get("lastname"),
                    "username": athlete_data.get("username")
                }
            }
        else:
            logging.error(f"Failed to get athlete info: {athlete_response.text}")
            raise HTTPException(status_code=400, detail="Failed to get athlete info")
            
    except Exception as e:
        logging.exception("Error connecting to Strava:")
        raise HTTPException(status_code=500, detail=f"Error connecting to Strava: {str(e)}")

@router.post("/sync")
def sync_activities(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Sync activities from Strava"""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()
        
        if not profile or not profile.strava_access_token:
            raise HTTPException(status_code=400, detail="Strava not connected")
        
        # Get recent activities
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {profile.strava_access_token}"}
        
        response = requests.get(activities_url, headers=headers, params={"per_page": 30})
        
        if response.status_code == 200:
            activities = response.json()
            
            # Here you would typically save activities to your database
            # For now, we'll just return the count
            return {
                "message": f"Synced {len(activities)} activities",
                "activities_count": len(activities),
                "activities": activities[:5]  # Return first 5 for preview
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch activities")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing activities: {str(e)}")

@router.get("/activities")
def get_activities(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get cached activities"""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()
        
        if not profile or not profile.strava_access_token:
            raise HTTPException(status_code=400, detail="Strava not connected")
        
        # Get activities from Strava
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {profile.strava_access_token}"}
        
        response = requests.get(activities_url, headers=headers, params={"per_page": 10})
        
        if response.status_code == 200:
            raw_activities = response.json()
            activities = []
            for act in raw_activities:
                activities.append({
                    "id": act.get("id"),
                    "name": act.get("name"),
                    "distance_m": act.get("distance", 0),
                    "moving_time_s": act.get("moving_time", 0),
                    "total_elevation_gain_m": act.get("total_elevation_gain", 0),
                    "type": act.get("type"),
                    "average_heartrate": act.get("average_heartrate"),
                    "calories": act.get("calories"),
                    "map": act.get("map"),
                    "start_date": act.get("start_date"),
                    # add more fields as needed
                })
            return {
                "activities": activities,
                "count": len(activities)
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch activities")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting activities: {str(e)}")

@router.post("/zones")
def fetch_zones(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Fetch athlete zones"""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()
        
        if not profile or not profile.strava_access_token:
            raise HTTPException(status_code=400, detail="Strava not connected")
        
        # Get athlete zones
        zones_url = "https://www.strava.com/api/v3/athlete/zones"
        headers = {"Authorization": f"Bearer {profile.strava_access_token}"}
        
        response = requests.get(zones_url, headers=headers)
        
        if response.status_code == 200:
            zones = response.json()
            return {
                "zones": zones
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch zones")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching zones: {str(e)}")

@router.delete("/disconnect")
def disconnect(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Disconnect Strava"""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()
        
        if profile:
            profile.strava_user_id = None
            profile.strava_access_token = None
            profile.strava_refresh_token = None
            profile.strava_token_expires_at = None
            db.commit()
        
        return {"message": "Strava disconnected successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting Strava: {str(e)}") 