#!/bin/bash
set -e

ENVIRONMENT=${1:-production}
SERVER_USER=${DEPLOY_USER:-root}
SERVER_HOST=${DEPLOY_HOST}
APP_NAME="reroute"

if [ -z "$SERVER_HOST" ]; then
    echo "❌ DEPLOY_HOST environment variable is required"
    exit 1
fi

echo "🔄 Deploying to DigitalOcean Droplet: $SERVER_HOST"

# Build and push Docker image
echo "🏗️ Building Docker image..."
docker build -t $APP_NAME:latest .

# Save image to tar file
docker save $APP_NAME:latest | gzip > $APP_NAME-latest.tar.gz

# Copy files to server
echo "📤 Copying files to server..."
scp $APP_NAME-latest.tar.gz $SERVER_USER@$SERVER_HOST:/tmp/
scp docker-compose.prod.yml $SERVER_USER@$SERVER_HOST:/opt/$APP_NAME/docker-compose.yml
scp nginx.conf $SERVER_USER@$SERVER_HOST:/opt/$APP_NAME/
scp .env.$ENVIRONMENT $SERVER_USER@$SERVER_HOST:/opt/$APP_NAME/.env

# Deploy on server
echo "🚀 Deploying on server..."
ssh $SERVER_USER@$SERVER_HOST << EOF
    cd /opt/$APP_NAME
    
    # Load the Docker image
    docker load < /tmp/$APP_NAME-latest.tar.gz
    rm /tmp/$APP_NAME-latest.tar.gz
    
    # Stop existing containers
    docker-compose down || true
    
    # Start new containers
    docker-compose up -d
    
    # Run database migrations
    docker-compose exec -T app alembic upgrade head
    
    # Clean up old images
    docker image prune -f
EOF

# Cleanup local files
rm $APP_NAME-latest.tar.gz

echo "✅ DigitalOcean deployment completed!"
echo "🌐 Your app should be available at: https://$SERVER_HOST"