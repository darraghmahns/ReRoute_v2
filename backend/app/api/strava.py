import json
import logging
from datetime import datetime
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_active_user_by_session
from app.models.strava import StravaActivity
from app.models.user import Profile, User

router = APIRouter(prefix="/strava", tags=["strava"])


def refresh_strava_token(profile: Profile, db: Session) -> bool:
    """Refresh Strava access token if expired. Returns True if successful."""
    try:
        if not profile.strava_refresh_token:
            return False

        # Check if token is expired or will expire soon (within 1 hour)
        if profile.strava_token_expires_at:
            time_until_expiry = profile.strava_token_expires_at - datetime.utcnow()
            if time_until_expiry.total_seconds() > 3600:  # More than 1 hour left
                return True  # Token is still valid

        # Refresh the token
        refresh_data = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": profile.strava_refresh_token,
        }

        response = requests.post(
            "https://www.strava.com/oauth/token", data=refresh_data
        )

        if response.status_code == 200:
            token_info = response.json()
            profile.strava_access_token = token_info.get("access_token")
            profile.strava_refresh_token = token_info.get("refresh_token")
            if token_info.get("expires_at"):
                profile.strava_token_expires_at = datetime.fromtimestamp(
                    token_info["expires_at"]
                )
            db.commit()
            logging.info("Strava token refreshed successfully")
            return True
        else:
            logging.error(f"Failed to refresh Strava token: {response.text}")
            return False

    except Exception as e:
        logging.error(f"Error refreshing Strava token: {e}")
        return False


def get_valid_strava_token(profile: Profile, db: Session) -> Optional[str]:
    """Get a valid Strava access token, refreshing if necessary."""
    if not profile or not profile.strava_refresh_token:
        return None

    if refresh_strava_token(profile, db):
        return profile.strava_access_token

    return None


@router.get("/auth-url")
def get_auth_url():
    """Get Strava OAuth URL"""
    redirect_uri = "https://reroute.training/"
    logging.info(
        f"Strava config - Client ID: {settings.STRAVA_CLIENT_ID}, Redirect URI: {redirect_uri}"
    )
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={settings.STRAVA_CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=read,activity:read_all,profile:read_all"
    return {"auth_url": auth_url}


@router.post("/callback")
async def handle_callback(
    request: Request,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Handle OAuth callback"""
    try:
        logging.info("=== STRAVA CALLBACK START ===")
        logging.info(f"Request headers: {dict(request.headers)}")
        # For debugging - temporarily bypass authentication
        auth_header = request.headers.get("Authorization", "")
        logging.info(
            f"Auth header present: {bool(auth_header)}, starts with Bearer: {auth_header.startswith('Bearer ')}"
        )

        # Get the authorization code from the request
        body = await request.json()
        logging.info(
            f"Request body keys: {list(body.keys()) if body else 'Empty body'}"
        )
        code = body.get("code")

        if not code:
            logging.error("No authorization code received in callback.")
            raise HTTPException(status_code=400, detail="Authorization code required")

        logging.info(f"Received authorization code (first 10 chars): {code[:10]}...")

        # TODO: For now, just test token exchange without user association
        # profile = db.query(Profile).filter(Profile.id == current_user.id).first()
        # if profile and profile.strava_access_token:
        #     # Check if token is still valid
        #     access_token = get_valid_strava_token(profile, db)
        #     if access_token:
        #         logging.info("User already has valid Strava connection")
        #         return {
        #             "message": "Strava already connected successfully",
        #             "athlete": {
        #                 "id": profile.strava_user_id,
        #                 "note": "Already connected",
        #             },
        #         }

        # Exchange code for access token
        token_url = "https://www.strava.com/oauth/token"
        token_data = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        }

        logging.info(
            f"Attempting token exchange with client_id: {settings.STRAVA_CLIENT_ID}"
        )
        response = requests.post(token_url, data=token_data)

        if response.status_code != 200:
            error_detail = response.text
            logging.error(
                f"Failed to exchange code for token. Status: {response.status_code}, Response: {error_detail}"
            )

            # Check for specific error types
            if "invalid" in error_detail.lower() and "code" in error_detail.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Authorization code is invalid or expired. This usually happens if you've already connected or tried multiple times. Please disconnect first, then try connecting to Strava again.",
                )
            elif "used" in error_detail.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Authorization code has already been used. Please disconnect and reconnect to Strava.",
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to connect to Strava. Please try again. Error: {error_detail[:100]}",
                )

        token_info = response.json()

        # Get athlete info
        athlete_response = requests.get(
            "https://www.strava.com/api/v3/athlete",
            headers={"Authorization": f"Bearer {token_info['access_token']}"},
        )

        if athlete_response.status_code == 200:
            athlete_data = athlete_response.json()
            logging.info(
                f"Successfully got athlete data: {athlete_data.get('id', 'unknown_id')}"
            )

            # Update user's profile with Strava info
            profile = db.query(Profile).filter(Profile.id == current_user.id).first()
            if not profile:
                profile = Profile(id=current_user.id)
                db.add(profile)

            profile.strava_user_id = str(athlete_data.get("id"))
            profile.strava_access_token = token_info.get("access_token")
            profile.strava_refresh_token = token_info.get("refresh_token")
            # Strava tokens DO expire - store the expiry time
            if token_info.get("expires_at"):
                profile.strava_token_expires_at = datetime.fromtimestamp(
                    token_info["expires_at"]
                )

            db.commit()

            return {
                "message": "Strava connected successfully",
                "athlete": {
                    "id": athlete_data.get("id"),
                    "firstname": athlete_data.get("firstname"),
                    "lastname": athlete_data.get("lastname"),
                    "username": athlete_data.get("username"),
                },
            }
        else:
            logging.error(f"Failed to get athlete info: {athlete_response.text}")
            raise HTTPException(status_code=400, detail="Failed to get athlete info")

    except HTTPException as http_exc:
        logging.error(f"HTTP Exception in Strava callback: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logging.exception("Error connecting to Strava:")
        logging.error(f"Exception type: {type(e).__name__}")
        logging.error(f"Exception details: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error connecting to Strava: {str(e)}"
        )


@router.post("/sync")
def sync_activities(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Sync activities from Strava, including streams. Gets up to 200 recent activities."""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Profile not found")

        # Get valid token (auto-refreshes if needed)
        access_token = get_valid_strava_token(profile, db)
        if not access_token:
            raise HTTPException(
                status_code=400, detail="Strava not connected or token invalid"
            )

        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}

        all_activities = []
        page = 1
        per_page = 50  # Strava's max per page

        # Get up to 200 activities (4 pages) for better historical coverage
        while len(all_activities) < 200 and page <= 4:
            response = requests.get(
                activities_url,
                headers=headers,
                params={"per_page": per_page, "page": page},
            )

            if response.status_code == 401:
                # Token might be expired, try refreshing once
                logging.warning(f"Got 401 on page {page}, attempting token refresh")
                if refresh_strava_token(profile, db):
                    headers = {"Authorization": f"Bearer {profile.strava_access_token}"}
                    response = requests.get(
                        activities_url,
                        headers=headers,
                        params={"per_page": per_page, "page": page},
                    )

            if response.status_code != 200:
                logging.error(
                    f"Failed to fetch Strava activities page {page}: {response.status_code} - {response.text}"
                )
                break

            activities = response.json()
            if not activities:  # No more activities
                logging.info(f"No more activities found at page {page}")
                break

            all_activities.extend(activities)
            logging.info(
                f"Fetched {len(activities)} activities from page {page} (total: {len(all_activities)})"
            )
            page += 1

        # Process all collected activities
        if all_activities:
            # First, log what we're about to sync
            logging.info(f"Processing {len(all_activities)} activities from Strava")
            activity_dates = [
                act.get("start_date", "Unknown")[:10] for act in all_activities[:5]
            ]
            logging.info(f"Sample activity dates: {activity_dates}")

            upserted = 0
            updated = 0
            new_activities = 0

            for act in all_activities:
                act_id = act.get("id")
                if not act_id:
                    continue

                act_date = act.get("start_date", "Unknown")[:10]
                act_name = act.get("name", "Unnamed")

                # Upsert activity summary
                db_act = (
                    db.query(StravaActivity)
                    .filter(
                        StravaActivity.id == act_id,
                        StravaActivity.user_id == current_user.id,
                    )
                    .first()
                )
                if not db_act:
                    db_act = StravaActivity(
                        id=act_id,
                        user_id=current_user.id,
                        name=act.get("name"),
                        summary=act,
                        streams=None,
                    )
                    db.add(db_act)
                    new_activities += 1
                    logging.info(f"Adding new activity: {act_name} ({act_date})")
                else:
                    # Always update existing activities with fresh data
                    db_act.name = act.get("name")
                    db_act.summary = act
                    updated += 1
                    logging.info(f"Updating existing activity: {act_name} ({act_date})")

                # Always try to fetch/update streams for better data quality
                streams_url = (
                    f"https://www.strava.com/api/v3/activities/{act_id}/streams"
                )
                stream_keys = "watts,heartrate,latlng,altitude,time,distance,cadence,temp,grade_smooth,velocity_smooth"

                # Use the refreshed token for streams
                streams_resp = requests.get(
                    streams_url,
                    headers=headers,
                    params={"keys": stream_keys, "key_by_type": "true"},
                )
                if streams_resp.status_code == 200:
                    streams_data = streams_resp.json()
                    db_act.streams = streams_data
                    # Log what streams we got
                    available_streams = (
                        list(streams_data.keys()) if streams_data else []
                    )
                    logging.info(
                        f"Fetched streams for {act_name}: {', '.join(available_streams)}"
                    )
                elif streams_resp.status_code == 404:
                    # No streams available for this activity
                    logging.info(f"No streams available for activity: {act_name}")
                    db_act.streams = {}
                else:
                    logging.warning(
                        f"Failed to fetch streams for {act_name}: {streams_resp.status_code}"
                    )

                db_act.updated_at = datetime.utcnow()
                upserted += 1

            db.commit()

            logging.info(
                f"Sync complete: {new_activities} new, {updated} updated, {upserted} total"
            )

            return {
                "message": f"Synced {upserted} activities: {new_activities} new, {updated} updated (with streams)",
                "activities_count": upserted,
                "new_activities": new_activities,
                "updated_activities": updated,
                "activities": all_activities[:5],  # Return first 5 for preview
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch activities")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error syncing activities: {str(e)}"
        )


@router.post("/sync/refresh")
def refresh_all_activities(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Full refresh: Clear all activities and re-sync from Strava. Use when data seems stale."""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Profile not found")

        # Get valid token (auto-refreshes if needed)
        access_token = get_valid_strava_token(profile, db)
        if not access_token:
            raise HTTPException(
                status_code=400, detail="Strava not connected or token invalid"
            )

        # Clear all existing activities for this user
        deleted_count = (
            db.query(StravaActivity)
            .filter(StravaActivity.user_id == current_user.id)
            .delete()
        )
        logging.info(
            f"Cleared {deleted_count} existing activities for user {current_user.id}"
        )

        # Now perform a full sync
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}

        all_activities = []
        page = 1
        per_page = 50

        # Get up to 200 activities (4 pages) for better historical coverage
        while len(all_activities) < 200 and page <= 4:
            response = requests.get(
                activities_url,
                headers=headers,
                params={"per_page": per_page, "page": page},
            )

            if response.status_code != 200:
                logging.error(
                    f"Failed to fetch Strava activities page {page}: {response.status_code} - {response.text}"
                )
                break

            activities = response.json()
            if not activities:
                logging.info(f"No more activities found at page {page}")
                break

            all_activities.extend(activities)
            logging.info(
                f"Fetched {len(activities)} activities from page {page} (total: {len(all_activities)})"
            )
            page += 1

        # Add all activities as new
        if all_activities:
            added_count = 0
            for act in all_activities:
                act_id = act.get("id")
                if not act_id:
                    continue

                db_act = StravaActivity(
                    id=act_id,
                    user_id=current_user.id,
                    name=act.get("name"),
                    summary=act,
                    streams=None,
                )
                db.add(db_act)
                added_count += 1

            db.commit()
            logging.info(f"Added {added_count} fresh activities")

            return {
                "message": f"Full refresh complete: Cleared {deleted_count} old activities, added {added_count} fresh activities",
                "deleted_count": deleted_count,
                "added_count": added_count,
                "sample_activities": all_activities[:3],
            }
        else:
            db.rollback()
            raise HTTPException(
                status_code=400, detail="Failed to fetch activities for refresh"
            )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error during full refresh: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error refreshing activities: {str(e)}"
        )


@router.get("/activities")
def get_activities(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get cached activities"""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()

        if not profile:
            raise HTTPException(status_code=400, detail="Profile not found")

        # Get valid token (auto-refreshes if needed)
        access_token = get_valid_strava_token(profile, db)
        if not access_token:
            raise HTTPException(
                status_code=400, detail="Strava not connected or token invalid"
            )

        # Get activities from Strava
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(
            activities_url, headers=headers, params={"per_page": 10}
        )

        if response.status_code == 200:
            raw_activities = response.json()
            activities = []
            for act in raw_activities:
                activities.append(
                    {
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
                    }
                )
            return {"activities": activities, "count": len(activities)}
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch activities")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting activities: {str(e)}"
        )


@router.post("/zones")
def fetch_zones(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Fetch athlete zones"""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()

        if not profile:
            raise HTTPException(status_code=400, detail="Profile not found")

        # Get valid token (auto-refreshes if needed)
        access_token = get_valid_strava_token(profile, db)
        if not access_token:
            raise HTTPException(
                status_code=400, detail="Strava not connected or token invalid"
            )

        # Get athlete zones
        zones_url = "https://www.strava.com/api/v3/athlete/zones"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(zones_url, headers=headers)

        if response.status_code == 200:
            zones = response.json()
            return {"zones": zones}
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch zones")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching zones: {str(e)}")


@router.delete("/disconnect")
def disconnect(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Disconnect Strava"""
    try:
        profile = db.query(Profile).filter(Profile.id == current_user.id).first()

        if profile:
            was_connected = profile.strava_access_token is not None
            profile.strava_user_id = None
            profile.strava_access_token = None
            profile.strava_refresh_token = None
            profile.strava_token_expires_at = None
            db.commit()

            if was_connected:
                logging.info(f"Disconnected Strava for user {current_user.id}")
                return {"message": "Strava disconnected successfully"}
            else:
                return {"message": "Strava was not connected"}
        else:
            return {"message": "No profile found"}

    except Exception as e:
        logging.error(f"Error disconnecting Strava: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error disconnecting Strava: {str(e)}"
        )


@router.get("/activities/db")
def get_activities_db(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get all Strava activities for the user from the database, including streams."""
    acts = (
        db.query(StravaActivity)
        .filter(StravaActivity.user_id == current_user.id)
        .order_by(StravaActivity.created_at.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "name": a.name,
            "summary": a.summary,
            "has_streams": a.streams is not None,
            "streams": a.streams if a.streams else None,
        }
        for a in acts
    ]


@router.get("/activities/{activity_id}/streams")
def get_activity_streams(
    activity_id: int,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get the streams for a specific activity (if present)."""
    act = (
        db.query(StravaActivity)
        .filter(
            StravaActivity.id == activity_id, StravaActivity.user_id == current_user.id
        )
        .first()
    )
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not act.streams:
        raise HTTPException(
            status_code=404, detail="No streams found for this activity"
        )
    return act.streams
