#!/bin/bash
set -e

ENVIRONMENT=${1:-production}

echo "🚂 Deploying to Railway..."

# Install Railway CLI if not present
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway (if not already logged in)
railway login

# Deploy
echo "🚀 Deploying application..."
railway up

# Set environment variables if they exist
if [ -f ".env.$ENVIRONMENT" ]; then
    echo "Setting environment variables..."
    while IFS= read -r line; do
        if [[ $line =~ ^[^#]*= ]]; then
            key=$(echo $line | cut -d '=' -f1)
            value=$(echo $line | cut -d '=' -f2-)
            railway variables set $key="$value"
        fi
    done < .env.$ENVIRONMENT
fi

echo "✅ Railway deployment completed!"
echo "🌐 Check your Railway dashboard for the deployment URL"