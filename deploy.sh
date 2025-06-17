#!/bin/bash

# Deployment script for Financial Planner on Google Cloud Run
# Make sure you have gcloud CLI installed and authenticated

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
REGION="us-central1"
BACKEND_SERVICE="finplanner-backend"
FRONTEND_SERVICE="finplanner-frontend"

echo "🚀 Starting deployment to Google Cloud Run..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    echo "❌ Error: Not authenticated with gcloud. Run 'gcloud auth login' first."
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and deploy backend
echo "🐍 Building and deploying backend..."
gcloud builds submit --config cloudbuild-backend.yaml .

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region=$REGION --format="value(status.url)")
echo "Backend deployed at: $BACKEND_URL"

# Update frontend Cloud Build config with actual backend URL
sed -i.bak "s|REACT_APP_API_URL=.*|REACT_APP_API_URL=$BACKEND_URL|" cloudbuild-frontend.yaml

# Build and deploy frontend
echo "⚛️  Building and deploying frontend..."
gcloud builds submit --config cloudbuild-frontend.yaml .

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format="value(status.url)")

# Restore original Cloud Build config
mv cloudbuild-frontend.yaml.bak cloudbuild-frontend.yaml

echo "✅ Deployment completed successfully!"
echo ""
echo "📍 Service URLs:"
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""
echo "🔗 Access your application at: $FRONTEND_URL"