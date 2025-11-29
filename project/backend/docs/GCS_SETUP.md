# Google Cloud Storage Setup Guide

This guide explains how to set up Google Cloud Storage (GCS) for the Resume Tips feature.

## Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed (optional but recommended)

## Step 1: Create a GCS Bucket

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Cloud Storage** > **Buckets**
3. Click **Create Bucket**
4. Configure the bucket:
   - **Name**: Choose a globally unique name (e.g., `jobtrust-resumes-prod`)
   - **Location type**: Choose based on your needs (Multi-region recommended for production)
   - **Storage class**: Standard
   - **Access control**: Fine-grained (recommended)
5. Click **Create**

## Step 2: Create a Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Configure:
   - **Name**: `jobtrust-gcs-service`
   - **Description**: Service account for JobTrust GCS operations
4. Click **Create and Continue**
5. Grant the following roles:
   - `Storage Object Admin` (for upload/delete operations)
   - `Storage Object Viewer` (for generating signed URLs)
6. Click **Done**

## Step 3: Generate Service Account Key

1. Click on the newly created service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create**
6. Save the downloaded JSON file securely (e.g., `gcs-credentials.json`)

**Important**: Never commit this file to version control!

## Step 4: Configure Environment Variables

Add the following variables to your `.env` file:

```env
# Google Cloud Storage Configuration
GCS_BUCKET_NAME=your-bucket-name
GCS_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcs-credentials.json
```

### Environment Variable Descriptions

| Variable | Description | Example |
|----------|-------------|---------|
| `GCS_BUCKET_NAME` | Name of your GCS bucket | `jobtrust-resumes-prod` |
| `GCS_PROJECT_ID` | Your GCP project ID | `my-project-123456` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON key | `/app/secrets/gcs-credentials.json` |

## Step 5: Install Required Python Package

Add to `requirements.txt`:

```
google-cloud-storage==2.14.0
```

Install:

```bash
pip install google-cloud-storage
```

## Step 6: Configure CORS (Optional)

If you need direct browser uploads or downloads, configure CORS on your bucket:

```json
[
  {
    "origin": ["http://localhost:3000", "https://yourdomain.com"],
    "method": ["GET", "PUT", "POST", "DELETE"],
    "responseHeader": ["Content-Type", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
```

Apply using gcloud:

```bash
gsutil cors set cors.json gs://your-bucket-name
```

## Bucket Structure

Resumes are stored with the following path structure:

```
resumes/{user_id}/{resume_id}/{filename}
```

Example:
```
resumes/123e4567-e89b-12d3-a456-426614174000/abc12345-6789-0abc-def0-123456789abc/my_resume.pdf
```

## Security Best Practices

1. **Never expose service account keys** in client-side code
2. **Use signed URLs** for temporary file access (default: 15 minutes)
3. **Enable bucket versioning** for data recovery
4. **Set up lifecycle rules** to delete old files if needed
5. **Monitor access logs** for suspicious activity

## Troubleshooting

### Error: "Could not automatically determine credentials"

Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON key file.

### Error: "403 Forbidden"

Check that your service account has the required permissions on the bucket.

### Error: "Bucket not found"

Verify `GCS_BUCKET_NAME` matches your actual bucket name exactly.

## Testing the Setup

Run the following Python script to test your configuration:

```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket("your-bucket-name")

# Test upload
blob = bucket.blob("test/test.txt")
blob.upload_from_string("Hello, GCS!")
print("Upload successful!")

# Test download
content = blob.download_as_string()
print(f"Downloaded: {content}")

# Cleanup
blob.delete()
print("Cleanup successful!")
```

