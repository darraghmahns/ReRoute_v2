from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Configuration - Development SQLite support
    USE_SQLITE: bool = False
    DATABASE_URL: str = ""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = "changeme"

    # Strava Configuration
    STRAVA_CLIENT_ID: str = "changeme"
    STRAVA_CLIENT_SECRET: str = "changeme"
    STRAVA_WEBHOOK_SECRET: str = "changeme"
    STRAVA_REDIRECT_URI: str = "changeme"

    # Stripe Configuration
    STRIPE_API_KEY: str = "changeme"
    STRIPE_WEBHOOK_SECRET: str = "changeme"
    STRIPE_PRO_PRICE_ID: str = "changeme"

    # Mapbox Configuration
    MAPBOX_API_KEY: str = "changeme"

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = "changeme"
    TWILIO_AUTH_TOKEN: str = "changeme"
    TWILIO_VERIFY_SERVICE_SID: str = "changeme"

    # SendGrid Configuration
    SENDGRID_API_KEY: str = "changeme"
    FROM_EMAIL: str = "noreply@reroute.training"
    FRONTEND_URL: str = "https://reroute.training"

    # S3 Configuration
    S3_ENDPOINT_URL: str = "changeme"
    S3_ACCESS_KEY: str = "changeme"
    S3_SECRET_KEY: str = "changeme"
    S3_BUCKET_NAME: str = "changeme"

    # Database Configuration
    POSTGRES_DB: str = "reroute_db"
    POSTGRES_USER: str = "reroute_user"
    POSTGRES_PASSWORD: str = "reroute_pass"
    # For Cloud Run, use Cloud SQL connection name; for local dev, use localhost
    POSTGRES_HOST: str = "/cloudsql/reroute-training:us-central1:reroute-db"
    POSTGRES_PORT: int = 5432

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # GraphHopper Configuration
    GRAPHHOPPER_BASE_URL: str = "https://reroute-graphhopper-server.onrender.com"
    # Set to False when using a local GH instance with graph.elevation.provider: void
    GRAPHHOPPER_ELEVATION_ENABLED: bool = True

    # Overpass API Configuration
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT_S: int = 30

    # Security Configuration
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SESSION_EXPIRE_HOURS: int = 1
    SESSION_REFRESH_THRESHOLD_MINUTES: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
