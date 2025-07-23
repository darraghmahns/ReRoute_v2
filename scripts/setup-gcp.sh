#!/bin/bash
set -e

# GCP Infrastructure Setup Script
# Usage: ./setup-gcp.sh [project-id] [region]

PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}
REGION=${2:-us-central1}
DOMAIN=${3}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Please provide a GCP project ID:"
    echo "Usage: ./setup-gcp.sh <project-id> [region] [domain]"
    echo "Example: ./setup-gcp.sh my-reroute-project us-central1 reroute.app"
    exit 1
fi

echo "🌐 Setting up GCP infrastructure for Reroute"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
if [ -n "$DOMAIN" ]; then
    echo "   Domain: $DOMAIN"
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Authenticate if needed
if ! gcloud auth list --format="value(account)" | grep -q "@"; then
    echo "🔐 Please authenticate with Google Cloud..."
    gcloud auth login
fi

# Set project
echo "🔧 Setting up project configuration..."
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# Create .env.gcp file
cat > .env.gcp << EOF
# GCP Configuration
GCP_PROJECT_ID=$PROJECT_ID
GCP_REGION=$REGION

# Generated during setup - will be updated by deployment script
GRAPHHOPPER_URL=
DATABASE_URL=
REDIS_URL=

# Required - set these values
OPENAI_API_KEY=
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
GRAPHHOPPER_API_KEY=

# Optional
DOMAIN=$DOMAIN
EOF

echo "✅ Created .env.gcp configuration file"

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
REQUIRED_APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "sql-component.googleapis.com"
    "sqladmin.googleapis.com"
    "secretmanager.googleapis.com"
    "redis.googleapis.com"
    "container.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
    "cloudtrace.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    echo "   Enabling $api..."
    gcloud services enable $api
done

echo "✅ All required APIs enabled"

# Create service account for deployment
echo "🔐 Creating service account..."
SERVICE_ACCOUNT="reroute-deploy@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT &>/dev/null; then
    gcloud iam service-accounts create reroute-deploy \
        --display-name="Reroute Deployment Service Account" \
        --description="Service account for Reroute application deployment"
    
    # Grant necessary roles
    ROLES=(
        "roles/run.admin"
        "roles/sql.admin"
        "roles/redis.admin"
        "roles/secretmanager.admin"
        "roles/cloudbuild.builds.editor"
        "roles/storage.admin"
        "roles/iam.serviceAccountUser"
    )
    
    for role in "${ROLES[@]}"; do
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="$role"
    done
    
    echo "✅ Service account created and configured"
else
    echo "✅ Service account already exists"
fi

# Setup Cloud Build trigger (if GitHub repo is connected)
if git remote get-url origin &>/dev/null; then
    REPO_URL=$(git remote get-url origin)
    echo "📋 Git repository detected: $REPO_URL"
    echo ""
    echo "To set up automatic deployment:"
    echo "1. Connect your GitHub repository to Cloud Build:"
    echo "   https://console.cloud.google.com/cloud-build/triggers"
    echo "2. Create a trigger using gcp/cloudbuild.yaml"
    echo "3. Set up the following substitution variables:"
    echo "   _REGION: $REGION"
    echo "   _DB_INSTANCE_CONNECTION_NAME: $PROJECT_ID:$REGION:reroute-postgres"
fi

# Setup domain mapping (if domain provided)
if [ -n "$DOMAIN" ]; then
    echo "🌐 Domain configuration for: $DOMAIN"
    echo ""
    echo "After deployment, you can map your domain:"
    echo "1. Verify domain ownership:"
    echo "   gcloud domains verify $DOMAIN"
    echo ""
    echo "2. Map domain to Cloud Run service:"
    echo "   gcloud run domain-mappings create --service=reroute-app --domain=$DOMAIN --region=$REGION"
    echo ""
    echo "3. Update your DNS records:"
    echo "   - Add CNAME record pointing $DOMAIN to ghs.googlehosted.com"
    echo "   - SSL certificate will be automatically provisioned"
fi

# Create initial secrets (empty, to be filled later)
echo "🔐 Setting up Secret Manager..."
SECRETS=(
    "SECRET_KEY"
    "OPENAI_API_KEY"
    "STRAVA_CLIENT_ID"
    "STRAVA_CLIENT_SECRET"
    "GRAPHHOPPER_API_KEY"
)

for secret in "${SECRETS[@]}"; do
    if ! gcloud secrets describe $secret &>/dev/null; then
        echo "placeholder" | gcloud secrets create $secret --data-file=- --replication-policy=automatic
        echo "   Created secret: $secret (placeholder value)"
    else
        echo "   Secret already exists: $secret"
    fi
done

echo ""
echo "✅ GCP infrastructure setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Update the secrets in Secret Manager with your actual values:"
echo "   gcloud secrets versions add SECRET_KEY --data-file=-"
echo "   gcloud secrets versions add OPENAI_API_KEY --data-file=-"
echo "   # ... etc"
echo ""
echo "2. Update .env.gcp with your API keys and credentials"
echo ""
echo "3. Run the deployment script:"
echo "   export GCP_PROJECT_ID=$PROJECT_ID"
echo "   export GCP_REGION=$REGION"
echo "   ./deploy/deploy.sh gcp production"
echo ""
echo "🔗 Useful links:"
echo "   GCP Console: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
echo "   Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "   Secret Manager: https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo "   Cloud Build: https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID"