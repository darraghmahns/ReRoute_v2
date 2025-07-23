#!/bin/bash
set -e

# Deployment script for cloud providers
# Usage: ./deploy.sh [provider] [environment]
# Examples:
#   ./deploy.sh digitalocean production
#   ./deploy.sh aws staging
#   ./deploy.sh gcp production

PROVIDER=${1:-digitalocean}
ENVIRONMENT=${2:-production}

echo "🚀 Deploying to $PROVIDER ($ENVIRONMENT environment)"

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
    export $(grep -v '^#' .env.$ENVIRONMENT | xargs)
fi

case $PROVIDER in
    "digitalocean")
        echo "📦 Deploying to DigitalOcean Droplet..."
        ./deploy/digitalocean.sh $ENVIRONMENT
        ;;
    "aws")
        echo "📦 Deploying to AWS ECS..."
        ./deploy/aws.sh $ENVIRONMENT
        ;;
    "gcp")
        echo "📦 Deploying to Google Cloud Run..."
        ./deploy/gcp.sh $ENVIRONMENT
        ;;
    "vercel")
        echo "📦 Deploying frontend to Vercel..."
        ./deploy/vercel.sh $ENVIRONMENT
        ;;
    "railway")
        echo "📦 Deploying to Railway..."
        ./deploy/railway.sh $ENVIRONMENT
        ;;
    *)
        echo "❌ Unknown provider: $PROVIDER"
        echo "Supported providers: digitalocean, aws, gcp, vercel, railway"
        exit 1
        ;;
esac

echo "✅ Deployment completed successfully!"