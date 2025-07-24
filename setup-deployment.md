# Deployment Pipeline Setup

You now have 3 prebuilt deployment options:

## Option 1: Simple GitHub Actions (Recommended for quick start)

**File**: `.github/workflows/deploy-production.yml`

**Setup:**
1. Create a GCP service account with Cloud Run Admin, Cloud Build Editor, and Storage Admin roles
2. Download the service account key as JSON
3. Add it as a GitHub secret named `GCP_SA_KEY`
4. Push to main branch to trigger deployment

**Pros:** Simple, fast setup
**Cons:** Manual infrastructure management

## Option 2: Terraform + GitHub Actions (Recommended for production)

**Files**: 
- `.github/workflows/deploy-with-terraform.yml`
- `terraform/main.tf`
- `terraform/terraform.tfvars.example`

**Setup:**
1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Fill in your values in `terraform.tfvars`
3. Create GitHub secrets:
   - `GCP_SA_KEY`: Service account JSON with Owner role
   - `DB_PASSWORD`: Secure database password
4. Run locally first: `cd terraform && terraform init && terraform apply`
5. Push to main branch for automated deployments

**Pros:** Infrastructure as code, repeatable, secure
**Cons:** More complex setup

## Option 3: Use Official FastAPI Template (Clean slate)

**Command:**
```bash
pip install copier
copier copy https://github.com/fastapi/full-stack-fastapi-template.git my-new-project
```

**Pros:** Modern best practices, batteries included
**Cons:** Requires migrating your existing code

## Current Status

Your app is already deployed and working at:
- https://reroute-app-828281382646.us-central1.run.app

The deployment pipeline will:
1. Build your React frontend with correct API URLs
2. Copy frontend files to FastAPI backend
3. Build and push Docker image to Google Container Registry
4. Deploy to Cloud Run with proper configuration
5. Handle secrets via Google Secret Manager
6. Set up database and Redis infrastructure (Terraform option)

## Quick Start

For immediate use, I recommend **Option 1**:

1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts?project=reroute-training)
2. Create a service account with these roles:
   - Cloud Run Admin
   - Cloud Build Editor
   - Storage Admin
   - Service Account User
3. Download the JSON key
4. Add it to GitHub Settings > Secrets as `GCP_SA_KEY`
5. Push any change to trigger deployment

Your next push to the main branch will automatically deploy the latest version!