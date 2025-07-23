#!/bin/bash
set -e

DOMAIN=${1}
PROJECT_ID=${2:-$(gcloud config get-value project 2>/dev/null)}
REGION=${3:-us-central1}

if [ -z "$DOMAIN" ] || [ -z "$PROJECT_ID" ]; then
    echo "❌ Usage: ./gcp-domain-setup.sh <domain> [project-id] [region]"
    echo "Example: ./gcp-domain-setup.sh reroute.app my-project us-central1"
    exit 1
fi

echo "🌐 Setting up custom domain for GCP Cloud Run"
echo "   Domain: $DOMAIN"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"

# Verify domain ownership
echo "🔐 Verifying domain ownership..."
if ! gcloud domains verify $DOMAIN 2>/dev/null; then
    echo "⚠️  Domain verification required"
    echo "1. Go to: https://console.cloud.google.com/apis/credentials/domainverification"
    echo "2. Add domain: $DOMAIN"
    echo "3. Follow verification steps (DNS TXT record or HTML file)"
    echo "4. Run this script again after verification"
    exit 1
fi

echo "✅ Domain ownership verified"

# Check if services are deployed
echo "🔍 Checking if services are deployed..."
if ! gcloud run services describe reroute-app --region=$REGION &>/dev/null; then
    echo "❌ Main application service not found"
    echo "Please deploy your application first:"
    echo "   ./deploy/deploy.sh gcp production"
    exit 1
fi

if ! gcloud run services describe reroute-graphhopper --region=$REGION &>/dev/null; then
    echo "❌ GraphHopper service not found"
    echo "Please deploy your application first:"
    echo "   ./deploy/deploy.sh gcp production"
    exit 1
fi

# Create domain mappings
echo "🔗 Creating domain mappings..."

# Map main application
echo "   Mapping $DOMAIN to reroute-app..."
if ! gcloud run domain-mappings describe --domain=$DOMAIN --region=$REGION &>/dev/null; then
    gcloud run domain-mappings create \
        --service=reroute-app \
        --domain=$DOMAIN \
        --region=$REGION
else
    echo "   Domain mapping already exists for $DOMAIN"
fi

# Map GraphHopper subdomain
GRAPHHOPPER_SUBDOMAIN="graphhopper.$DOMAIN"
echo "   Mapping $GRAPHHOPPER_SUBDOMAIN to reroute-graphhopper..."
if ! gcloud run domain-mappings describe --domain=$GRAPHHOPPER_SUBDOMAIN --region=$REGION &>/dev/null; then
    gcloud run domain-mappings create \
        --service=reroute-graphhopper \
        --domain=$GRAPHHOPPER_SUBDOMAIN \
        --region=$REGION
else
    echo "   Domain mapping already exists for $GRAPHHOPPER_SUBDOMAIN"
fi

# Get the CNAME target
CNAME_TARGET="ghs.googlehosted.com"

echo ""
echo "✅ Domain mapping setup completed!"
echo ""
echo "📋 DNS Configuration Required:"
echo "Add the following DNS records to your domain registrar:"
echo ""
echo "Main Application:"
echo "   Type: CNAME"
echo "   Name: $DOMAIN (or @ for root domain)"
echo "   Value: $CNAME_TARGET"
echo ""
echo "GraphHopper Service:"
echo "   Type: CNAME"
echo "   Name: graphhopper"
echo "   Value: $CNAME_TARGET"
echo ""
echo "🔐 SSL Certificate:"
echo "   Google will automatically provision SSL certificates"
echo "   This may take up to 15 minutes after DNS propagation"
echo ""
echo "🌐 Your applications will be available at:"
echo "   Main App: https://$DOMAIN"
echo "   GraphHopper: https://$GRAPHHOPPER_SUBDOMAIN"
echo ""
echo "📊 Check domain mapping status:"
echo "   gcloud run domain-mappings describe --domain=$DOMAIN --region=$REGION"
echo "   gcloud run domain-mappings describe --domain=$GRAPHHOPPER_SUBDOMAIN --region=$REGION"