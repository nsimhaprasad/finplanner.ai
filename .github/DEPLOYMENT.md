# GitHub Actions Deployment Guide

This project uses GitHub Actions to automatically deploy to Google Cloud Run on every push to the main branch.

## Setup Requirements

### 1. Google Cloud Setup

1. Create a Google Cloud Project
2. Enable the following APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

3. Create a service account:
   ```bash
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions"
   ```

4. Grant necessary permissions:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"
   ```

5. Create and download service account key:
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

### 2. GitHub Secrets Setup

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

- `GCP_PROJECT_ID`: Your Google Cloud Project ID
- `GCP_SA_KEY`: Contents of the service account key JSON file

## Deployment Workflow

The deployment happens automatically on every push to main:

1. **Backend Deployment**: Builds and deploys FastAPI backend
2. **Frontend Deployment**: Builds frontend with backend URL and deploys

### Manual Deployment

You can also trigger deployment manually:
1. Go to Actions tab in GitHub
2. Select "Deploy to Cloud Run" workflow
3. Click "Run workflow"

## Monitoring Deployments

- View deployment logs in GitHub Actions
- Check Cloud Run services in Google Cloud Console
- Service URLs are displayed in the deployment logs

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check GCP_SA_KEY secret is correctly set
2. **Permission Denied**: Verify service account has required roles
3. **Build Failed**: Check Dockerfile syntax and dependencies
4. **Service Not Found**: Ensure service names match in workflow

### Checking Logs

```bash
# View Cloud Run service logs
gcloud logs read --service=finplanner-backend --limit=50

gcloud logs read --service=finplanner-frontend --limit=50
```