# Deploying to Render

Step-by-step guide to deploy the LinkedIn Scraper to Render.

## Prerequisites

1. A [Render](https://render.com) account (free tier available)
2. Your code pushed to GitHub/GitLab/Bitbucket
3. LinkedIn credentials ready

## Step-by-Step Deployment

### Step 1: Sign Up / Log In

1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended) or email
3. Verify your email if needed

### Step 2: Create New Service

1. Click **"New +"** button in the dashboard
2. Select **"Background Worker"** (not Web Service, since this is a one-time job)
3. Or select **"Cron Job"** if you want scheduled runs

### Step 3: Connect Repository

1. Connect your GitHub/GitLab account if not already connected
2. Select your repository: `LinkedIn Scraper`
3. Render will detect the `render.yaml` file automatically

### Step 4: Configure Service

**If using Background Worker:**

- **Name**: `linkedin-scraper` (or any name you prefer)
- **Environment**: `Docker`
- **Region**: Choose closest to you (e.g., `Oregon (US West)`)
- **Branch**: `main` or `master`
- **Root Directory**: Leave empty (or `.` if needed)
- **Dockerfile Path**: `./Dockerfile`
- **Docker Context**: `.`

**If using Cron Job:**

- **Name**: `linkedin-scraper`
- **Schedule**: `0 2 * * *` (runs daily at 2 AM UTC)
- **Command**: `python scraper.py`
- **Environment**: `Docker`

### Step 5: Set Environment Variables

1. Scroll down to **"Environment Variables"** section
2. Click **"Add Environment Variable"**
3. Add these two variables:

   ```
   LINKEDIN_EMAIL = your_email@example.com
   LINKEDIN_PASSWORD = your_password
   ```

   ⚠️ **Important**: 
   - No quotes around values
   - No spaces around `=`
   - Use your actual LinkedIn test account credentials

### Step 6: Choose Plan

- **Free Plan**: Limited hours per month (750 hours), good for testing
- **Starter Plan**: $7/month, unlimited hours, better for production

For occasional scraping, **Free Plan** should work fine.

### Step 7: Deploy

1. Click **"Create Background Worker"** or **"Create Cron Job"**
2. Render will start building your Docker image
3. Watch the build logs - it will:
   - Install system dependencies
   - Install Chrome
   - Install Python packages
   - Build the container

### Step 8: Monitor Deployment

1. Go to your service dashboard
2. Click on **"Logs"** tab to see real-time output
3. The scraper will run automatically:
   - **Background Worker**: Runs once when deployed, or manually via "Manual Deploy"
   - **Cron Job**: Runs on schedule

## Manual Execution (Background Worker)

If you deployed as a Background Worker:

1. Go to your service dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. The scraper will run and you can see logs in real-time

## Viewing Results

The `profiles.csv` file is generated inside the container. To access it:

### Option 1: Download via Render Shell

1. Go to your service → **"Shell"** tab
2. Run: `cat profiles.csv` to view contents
3. Or download via Render's file browser (if available)

### Option 2: Store in Cloud Storage

Modify the scraper to upload results to:
- AWS S3
- Google Cloud Storage
- Dropbox
- GitHub (commit and push)

### Option 3: Email Results

Add email functionality to send CSV as attachment.

## Troubleshooting

### Build Fails

**Issue**: Docker build fails
**Solution**: 
- Check build logs for specific errors
- Ensure Dockerfile is correct
- Verify all dependencies are in requirements.txt

### Chrome Not Found

**Issue**: `Chrome binary not found`
**Solution**: 
- The Dockerfile installs Chrome automatically
- If issues persist, check Dockerfile Chrome installation steps

### Environment Variables Not Working

**Issue**: Credentials not loading
**Solution**:
- Verify variable names are exactly: `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD`
- Check for extra spaces or quotes
- Re-deploy after adding variables

### Timeout Issues

**Issue**: Service times out
**Solution**:
- Increase timeout in service settings
- For long scrapes, consider breaking into smaller batches

### Memory Issues

**Issue**: Out of memory errors
**Solution**:
- Upgrade to Starter plan ($7/month) for more memory
- Or optimize the scraper to use less memory

## Cost

- **Free Plan**: 
  - 750 hours/month free
  - Good for ~25 runs/month (if each run takes ~30 minutes)
  - After free hours, $0.00025/second (~$0.90/hour)

- **Starter Plan**: 
  - $7/month
  - Unlimited hours
  - 512MB RAM (should be enough)

## Alternative: Render Cron Jobs

For scheduled runs, you can also use Render's Cron Job feature:

1. **New +** → **Cron Job**
2. Connect repository
3. Set schedule: `0 2 * * *` (daily at 2 AM UTC)
4. Command: `python scraper.py`
5. Set environment variables
6. Deploy

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test with 1-2 URLs first
3. ✅ Verify results
4. ✅ Set up scheduled runs (if needed)
5. ✅ Monitor for any issues

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Check service logs for debugging

---

**Note**: Remember to use a test LinkedIn account, not your personal account!

