#!/bin/bash
set -e

ENVIRONMENT=${1:-production}
PROJECT_ID=${GCP_PROJECT_ID}
REGION=${GCP_REGION:-us-central1}
SERVICE_NAME="reroute-app"
GRAPHHOPPER_SERVICE="reroute-graphhopper"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ GCP_PROJECT_ID environment variable is required"
    exit 1
fi

echo "🌐 Deploying to Google Cloud Platform"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Environment: $ENVIRONMENT"

# Authenticate with gcloud (if not already authenticated)
if ! gcloud auth list --format="value(account)" | grep -q "@"; then
    echo "🔐 Authenticating with Google Cloud..."
    gcloud auth login
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    redis.googleapis.com

# Create Cloud SQL instance if it doesn't exist
if ! gcloud sql instances describe reroute-postgres --format="value(name)" 2>/dev/null; then
    echo "🗄️  Creating Cloud SQL PostgreSQL instance..."
    gcloud sql instances create reroute-postgres \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-size=10GB \
        --storage-type=SSD \
        --storage-auto-increase \
        --backup-start-time=02:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=03 \
        --deletion-protection
    
    # Create database
    gcloud sql databases create reroute --instance=reroute-postgres
    
    # Create user
    gcloud sql users create reroute-user \
        --instance=reroute-postgres \
        --password=$(openssl rand -base64 32)
    
    echo "✅ Cloud SQL instance created"
fi

# Create Redis instance if it doesn't exist
if ! gcloud redis instances describe reroute-redis --region=$REGION --format="value(name)" 2>/dev/null; then
    echo "🔴 Creating Redis instance..."
    gcloud redis instances create reroute-redis \
        --region=$REGION \
        --memory=1GB \
        --network=default
    
    echo "✅ Redis instance created"
fi

# Store secrets in Secret Manager
echo "🔐 Setting up secrets..."
secrets=(
    "SECRET_KEY:$(openssl rand -base64 64)"
    "OPENAI_API_KEY:${OPENAI_API_KEY}"
    "STRAVA_CLIENT_ID:${STRAVA_CLIENT_ID}"
    "STRAVA_CLIENT_SECRET:${STRAVA_CLIENT_SECRET}"
    "GRAPHHOPPER_API_KEY:${GRAPHHOPPER_API_KEY}"
)

for secret in "${secrets[@]}"; do
    key=$(echo $secret | cut -d: -f1)
    value=$(echo $secret | cut -d: -f2-)
    
    if [ -n "$value" ] && [ "$value" != "" ]; then
        echo $value | gcloud secrets create $key --data-file=- --replication-policy=automatic || \
        echo $value | gcloud secrets versions add $key --data-file=-
    fi
done

# Build and deploy GraphHopper service
echo "🚀 Deploying GraphHopper service..."
cd reroute-graphhopper-server

# Build container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$GRAPHHOPPER_SERVICE:latest .

# Deploy to Cloud Run
gcloud run deploy $GRAPHHOPPER_SERVICE \
    --image gcr.io/$PROJECT_ID/$GRAPHHOPPER_SERVICE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=1 \
    --timeout=900s \
    --concurrency=1000 \
    --min-instances=0 \
    --max-instances=10

cd ..

# Get GraphHopper service URL
GRAPHHOPPER_URL=$(gcloud run services describe $GRAPHHOPPER_SERVICE --region=$REGION --format="value(status.url)")
echo "✅ GraphHopper deployed at: $GRAPHHOPPER_URL"

# Build and deploy main application
echo "🚀 Deploying main application..."

# Create cloudbuild.yaml for the main app
cat > cloudbuild.yaml << EOF
steps:
  # Build frontend
  - name: 'node:20'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        cd frontend
        npm ci
        npm run build
    
  # Build backend container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME:latest', '.']
    
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/$SERVICE_NAME:latest']

images:
  - 'gcr.io/$PROJECT_ID/$SERVICE_NAME:latest'

options:
  machineType: 'E2_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY
EOF

# Build container image
gcloud builds submit --config cloudbuild.yaml .

# Get database connection details
DB_INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe reroute-postgres --format="value(connectionName)")
DB_PASSWORD=$(gcloud sql users describe reroute-user --instance=reroute-postgres --format="value(password)" 2>/dev/null || echo "CHANGE_ME")
REDIS_HOST=$(gcloud redis instances describe reroute-redis --region=$REGION --format="value(host)")

# Deploy main application to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --timeout=300s \
    --concurrency=1000 \
    --min-instances=0 \
    --max-instances=100 \
    --add-cloudsql-instances $DB_INSTANCE_CONNECTION_NAME \
    --set-env-vars="DATABASE_URL=postgresql://reroute-user:$DB_PASSWORD@localhost:5432/reroute?host=/cloudsql/$DB_INSTANCE_CONNECTION_NAME" \
    --set-env-vars="REDIS_URL=redis://$REDIS_HOST:6379" \
    --set-env-vars="GRAPHHOPPER_URL=$GRAPHHOPPER_URL" \
    --set-env-vars="ENVIRONMENT=production" \
    --set-secrets="SECRET_KEY=SECRET_KEY:latest" \
    --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest" \
    --set-secrets="STRAVA_CLIENT_ID=STRAVA_CLIENT_ID:latest" \
    --set-secrets="STRAVA_CLIENT_SECRET=STRAVA_CLIENT_SECRET:latest"

# Get main service URL
APP_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ GCP deployment completed!"
echo ""
echo "🌐 Application URLs:"
echo "   Main App: $APP_URL"
echo "   GraphHopper: $GRAPHHOPPER_URL"
echo ""
echo "📋 Next steps:"
echo "1. Set up custom domain mapping in Cloud Run"
echo "2. Configure Cloud SQL proxy for local development"
echo "3. Set up Cloud Monitoring and Logging"
echo "4. Configure Cloud CDN for static assets"

# Clean up
rm -f cloudbuild.yaml