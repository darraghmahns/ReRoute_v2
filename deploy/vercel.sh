#!/bin/bash
set -e

ENVIRONMENT=${1:-production}

echo "▲ Deploying frontend to Vercel..."

cd frontend

# Install Vercel CLI if not present
if ! command -v vercel &> /dev/null; then
    echo "Installing Vercel CLI..."
    npm install -g vercel
fi

# Build the project
npm run build

# Deploy to Vercel
if [ "$ENVIRONMENT" = "production" ]; then
    vercel --prod
else
    vercel
fi

cd ..

echo "✅ Vercel deployment completed!"
echo "🌐 Check your Vercel dashboard for the deployment URL"