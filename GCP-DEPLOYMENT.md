# 🌐 Google Cloud Platform Deployment Guide

Complete deployment guide for Reroute application and GraphHopper server on GCP using Cloud Run.

## 🚀 Quick Start

1. **Initial Setup**
   ```bash
   ./scripts/setup-gcp.sh your-project-id us-central1
   ```

2. **Deploy Application**
   ```bash
   export GCP_PROJECT_ID=your-project-id
   export GCP_REGION=us-central1
   ./deploy/deploy.sh gcp production
   ```

3. **Setup Custom Domain** (optional)
   ```bash
   ./scripts/gcp-domain-setup.sh yourdomain.com
   ```

## 📋 Prerequisites

- GCP account with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed locally
- Domain name (optional)

### Install Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# Ubuntu/Debian
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login
gcloud auth application-default login
```

## 🏗️ Architecture

The GCP deployment includes:

- **Cloud Run**: Serverless containers for main app and GraphHopper
- **Cloud SQL**: Managed PostgreSQL database
- **Cloud Redis**: Managed Redis cache
- **Secret Manager**: Secure storage for API keys
- **Cloud Build**: CI/CD pipeline
- **Cloud Load Balancing**: (with custom domains)

## 🛠️ Manual Setup Steps

### 1. Project Setup

```bash
# Create new project (optional)
gcloud projects create your-project-id --name="Reroute App"

# Set current project
gcloud config set project your-project-id
```

### 2. Enable APIs

```bash
./scripts/setup-gcp.sh your-project-id us-central1
```

This will enable all required APIs and create service accounts.

### 3. Set Environment Variables

Edit `.env.gcp` with your actual values:

```bash
# Required
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
OPENAI_API_KEY=sk-your-openai-key
STRAVA_CLIENT_ID=your-strava-client-id
STRAVA_CLIENT_SECRET=your-strava-secret

# Optional
DOMAIN=yourdomain.com
GRAPHHOPPER_API_KEY=your-graphhopper-key
```

### 4. Store Secrets

```bash
# Store secrets in Secret Manager
echo "your-secret-key" | gcloud secrets versions add SECRET_KEY --data-file=-
echo "sk-your-openai-key" | gcloud secrets versions add OPENAI_API_KEY --data-file=-
echo "your-strava-client-id" | gcloud secrets versions add STRAVA_CLIENT_ID --data-file=-
echo "your-strava-secret" | gcloud secrets versions add STRAVA_CLIENT_SECRET --data-file=-
```

## 🚀 Deployment

### Option 1: Automated Script

```bash
chmod +x deploy/gcp.sh
./deploy/gcp.sh production
```

### Option 2: Manual Deployment

```bash
# Build and push GraphHopper
cd reroute-graphhopper-server
gcloud builds submit --tag gcr.io/$PROJECT_ID/reroute-graphhopper:latest .

# Deploy GraphHopper to Cloud Run
gcloud run deploy reroute-graphhopper \
  --image gcr.io/$PROJECT_ID/reroute-graphhopper:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory=2Gi

# Build main application
cd ..
gcloud builds submit --tag gcr.io/$PROJECT_ID/reroute-app:latest .

# Deploy main application
gcloud run deploy reroute-app \
  --image gcr.io/$PROJECT_ID/reroute-app:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory=1Gi \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest"
```

## 🌐 Custom Domain Setup

### 1. Verify Domain Ownership

```bash
gcloud domains verify yourdomain.com
```

### 2. Create Domain Mappings

```bash
./scripts/gcp-domain-setup.sh yourdomain.com
```

### 3. Update DNS Records

Add CNAME records to your domain:

```
Type: CNAME
Name: yourdomain.com (or @)
Value: ghs.googlehosted.com

Type: CNAME  
Name: graphhopper
Value: ghs.googlehosted.com
```

## 🔄 CI/CD with GitHub Actions

### Required GitHub Secrets

```
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GCP_SA_KEY=<base64-encoded-service-account-key>
OPENAI_API_KEY=sk-your-key
STRAVA_CLIENT_ID=your-id
STRAVA_CLIENT_SECRET=your-secret
GRAPHHOPPER_API_KEY=your-key
```

### Get Service Account Key

```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=reroute-deploy@your-project-id.iam.gserviceaccount.com

# Base64 encode for GitHub
base64 key.json
```

### Setup Cloud Build Trigger

1. Connect GitHub repository to Cloud Build
2. Create trigger using `gcp/cloudbuild.yaml`
3. Set substitution variables

## 📊 Monitoring & Logging

### View Logs

```bash
# Application logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=reroute-app" --limit=50

# GraphHopper logs  
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=reroute-graphhopper" --limit=50
```

### Monitor Performance

```bash
# View metrics in Cloud Console
gcloud logging metrics list
```

### Set up Alerts

```bash
# Create uptime checks
gcloud monitoring uptime create \
  --resource-type=URL \
  --resource-name=https://yourdomain.com
```

## 🔧 Configuration

### Environment Variables

Cloud Run services can use environment variables or Secret Manager:

```bash
# Update environment variable
gcloud run services update reroute-app \
  --set-env-vars="NEW_VAR=value" \
  --region=us-central1

# Update secret
gcloud run services update reroute-app \
  --set-secrets="API_KEY=API_KEY:latest" \
  --region=us-central1
```

### Scaling Configuration

```bash
# Configure autoscaling
gcloud run services update reroute-app \
  --min-instances=1 \
  --max-instances=100 \
  --concurrency=1000 \
  --memory=1Gi \
  --cpu=1
```

## 💾 Database Management

### Access Cloud SQL

```bash
# Connect via proxy
gcloud sql connect reroute-postgres --user=reroute-user

# Create backup
gcloud sql backups create --instance=reroute-postgres
```

### Redis Management

```bash
# Get Redis info
gcloud redis instances describe reroute-redis --region=us-central1

# Update Redis memory
gcloud redis instances update reroute-redis \
  --region=us-central1 \
  --memory=2GB
```

## 🔐 Security

### Service Account Permissions

The deployment creates a service account with minimal required permissions:

- `roles/run.admin` - Deploy to Cloud Run
- `roles/sql.admin` - Manage Cloud SQL
- `roles/secretmanager.admin` - Access secrets

### Network Security

Cloud Run services are:
- HTTPS-only by default
- Protected by Google's global load balancer
- Support custom VPC (if needed)

## 💰 Cost Optimization

### Estimated Monthly Costs (Light Usage)

- **Cloud Run**: $0-20 (pay per use)
- **Cloud SQL**: $25-50 (f1-micro instance)
- **Redis**: $30-40 (1GB memory)
- **Total**: ~$55-110/month

### Cost Reduction Tips

1. Use `min-instances=0` for development
2. Set appropriate CPU/memory limits
3. Use Cloud SQL proxy for local development
4. Enable request compression
5. Implement proper caching

## 🐛 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   gcloud builds log [BUILD_ID]
   ```

2. **Service Won't Start**
   ```bash
   gcloud run services get-iam-policy reroute-app --region=us-central1
   gcloud logs read "resource.labels.service_name=reroute-app"
   ```

3. **Database Connection Issues**
   ```bash
   gcloud sql instances describe reroute-postgres
   gcloud run services describe reroute-app --region=us-central1
   ```

4. **Domain Mapping Issues**
   ```bash
   gcloud run domain-mappings describe --domain=yourdomain.com --region=us-central1
   ```

### Health Checks

```bash
# Check service health
curl https://your-service-url/health

# Check GraphHopper
curl https://graphhopper.yourdomain.com/info
```

## 📈 Scaling for Production

### High Availability Setup

```bash
# Deploy to multiple regions
gcloud run deploy reroute-app \
  --image gcr.io/$PROJECT_ID/reroute-app:latest \
  --region us-west1

# Use Global Load Balancer for multi-region
gcloud compute backend-services create reroute-backend \
  --global \
  --load-balancing-scheme=EXTERNAL
```

### Performance Optimization

1. **Enable CDN**
   ```bash
   # Configure Cloud CDN for static assets
   gcloud compute backend-services update reroute-backend \
     --enable-cdn --global
   ```

2. **Database Read Replicas**
   ```bash
   gcloud sql instances create reroute-postgres-replica \
     --master-instance-name=reroute-postgres
   ```

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Build](https://cloud.google.com/build/docs)
- [Domain Mapping](https://cloud.google.com/run/docs/mapping-custom-domains)