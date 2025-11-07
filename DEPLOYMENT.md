# Deployment Guide

This guide covers deploying the LinkedIn Profile Scraper to various cloud platforms.

## ⚠️ Important Considerations

Before deploying:
- **LinkedIn Terms of Service**: Web scraping may violate LinkedIn's ToS. Use at your own risk.
- **Resource Requirements**: This scraper needs Chrome/Chromium, which requires significant memory (1-2GB RAM minimum).
- **Environment Variables**: Never commit `.env` file. Use platform-specific environment variable settings.
- **Rate Limiting**: Be mindful of LinkedIn's rate limits to avoid account restrictions.

---

## Deployment Options

### 1. Railway (Recommended for Easy Deployment)

[Railway](https://railway.app) is a modern platform that makes deployment easy.

#### Steps:

1. **Sign up** at [railway.app](https://railway.app)

2. **Create a new project** and connect your GitHub repository

3. **Add environment variables**:
   - Go to your project → Variables
   - Add:
     - `LINKEDIN_EMAIL=your_email@example.com`
     - `LINKEDIN_PASSWORD=your_password`

4. **Deploy**:
   - Railway will automatically detect the `Dockerfile` and deploy
   - Or use the `railway.json` configuration file

5. **Run the scraper**:
   - The scraper runs as a one-time job
   - You can trigger it manually or set up a cron job

**Pricing**: Free tier available, then pay-as-you-go (~$5-10/month for occasional use)

---

### 2. Render

[Render](https://render.com) offers free tier with some limitations.

#### Steps:

1. **Sign up** at [render.com](https://render.com)

2. **Create a new Web Service**:
   - Connect your GitHub repository
   - Select "Docker" as the environment
   - Use the provided `render.yaml` or configure manually

3. **Set environment variables**:
   - Go to Environment → Add Environment Variable
   - Add `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD`

4. **Deploy**:
   - Render will build from the Dockerfile
   - The service will start automatically

**Pricing**: Free tier available (with limitations), then $7/month for starter plan

---

### 3. Google Cloud Run

Google Cloud Run is serverless and charges only for execution time.

#### Steps:

1. **Install Google Cloud SDK**:
   ```bash
   # Download from https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Build and deploy**:
   ```bash
   # Build the container
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/linkedin-scraper
   
   # Deploy to Cloud Run
   gcloud run deploy linkedin-scraper \
     --image gcr.io/YOUR_PROJECT_ID/linkedin-scraper \
     --platform managed \
     --region us-central1 \
     --set-env-vars LINKEDIN_EMAIL=your_email@example.com,LINKEDIN_PASSWORD=your_password \
     --memory 2Gi \
     --timeout 3600
   ```

4. **Trigger manually** or set up Cloud Scheduler for periodic runs

**Pricing**: Pay per use, very cost-effective for occasional scraping (~$0.10-1 per run)

---

### 4. AWS EC2 / Lambda

#### EC2 (Virtual Server)

1. **Launch an EC2 instance**:
   - Ubuntu 22.04 LTS
   - t3.medium or larger (2GB+ RAM)
   - Configure security groups

2. **SSH into the instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip git
   git clone your-repo-url
   cd linkedin-scraper
   pip3 install -r requirements.txt
   ```

4. **Set environment variables**:
   ```bash
   export LINKEDIN_EMAIL=your_email@example.com
   export LINKEDIN_PASSWORD=your_password
   ```

5. **Run the scraper**:
   ```bash
   python3 scraper.py
   ```

**Pricing**: ~$10-20/month for t3.medium instance

#### Lambda (Serverless)

Note: Lambda has limitations with Chrome. Consider using AWS Fargate instead.

---

### 5. DigitalOcean App Platform

1. **Sign up** at [digitalocean.com](https://digitalocean.com)

2. **Create App**:
   - Connect GitHub repository
   - Select Dockerfile
   - Set environment variables

3. **Deploy**

**Pricing**: $5/month for basic plan

---

### 6. Docker on Any VPS

You can run the Docker container on any VPS provider (Linode, Vultr, Hetzner, etc.)

#### Steps:

1. **Install Docker** on your VPS:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

2. **Clone your repository**:
   ```bash
   git clone your-repo-url
   cd linkedin-scraper
   ```

3. **Build and run**:
   ```bash
   docker build -t linkedin-scraper .
   docker run --env-file .env linkedin-scraper
   ```

4. **Or use docker-compose** (create `docker-compose.yml`):
   ```yaml
   version: '3.8'
   services:
     scraper:
       build: .
       env_file:
         - .env
       volumes:
         - ./profiles.csv:/app/profiles.csv
         - ./linkedin_urls.txt:/app/linkedin_urls.txt
   ```

---

## Environment Variables Setup

For all platforms, set these environment variables (never commit them):

- `LINKEDIN_EMAIL`: Your LinkedIn test account email
- `LINKEDIN_PASSWORD`: Your LinkedIn test account password

### Platform-Specific Instructions:

- **Railway**: Project → Variables → Add Variable
- **Render**: Environment → Add Environment Variable
- **Google Cloud Run**: Use `--set-env-vars` flag or Cloud Console
- **AWS EC2**: Export in shell or use AWS Systems Manager Parameter Store
- **Docker**: Use `--env-file .env` or `-e` flags

---

## Scheduled Execution

To run the scraper on a schedule:

### Option 1: Cron Job (Linux/VPS)
```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/scraper && python3 scraper.py
```

### Option 2: GitHub Actions
Create `.github/workflows/scrape.yml`:
```yaml
name: Run Scraper
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scraper.py
        env:
          LINKEDIN_EMAIL: ${{ secrets.LINKEDIN_EMAIL }}
          LINKEDIN_PASSWORD: ${{ secrets.LINKEDIN_PASSWORD }}
```

### Option 3: Cloud Scheduler (Google Cloud)
```bash
gcloud scheduler jobs create http linkedin-scraper-job \
  --schedule="0 2 * * *" \
  --uri="https://YOUR-CLOUD-RUN-URL" \
  --http-method=GET
```

---

## Monitoring & Logs

- **Railway**: View logs in the dashboard
- **Render**: Logs tab in dashboard
- **Google Cloud Run**: Cloud Logging
- **AWS EC2**: Use `journalctl` or CloudWatch
- **Docker**: `docker logs container-name`

---

## Troubleshooting Deployment

### Chrome/Chromium Issues
- Ensure sufficient memory (1-2GB minimum)
- Check that Chrome dependencies are installed
- Verify headless mode is enabled

### Environment Variables
- Double-check variable names (case-sensitive)
- Ensure no quotes around values
- Verify variables are set in the platform dashboard

### Timeout Issues
- Increase timeout settings for long-running scrapes
- Consider breaking into smaller batches

---

## Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| Railway | Limited | $5-10/mo | Easy deployment |
| Render | Limited | $7/mo | Simple setup |
| Google Cloud Run | Generous | Pay-per-use | Cost-effective |
| AWS EC2 | 1 year free | $10-20/mo | Full control |
| DigitalOcean | No | $5/mo | Simple VPS |
| VPS (Hetzner) | No | €4-10/mo | Budget option |

---

## Security Best Practices

1. **Never commit** `.env` file or credentials
2. **Use secrets management** (platform-specific)
3. **Rotate credentials** regularly
4. **Use test accounts** only
5. **Monitor usage** to detect issues early
6. **Set up alerts** for failures

---

## Next Steps

1. Choose a deployment platform
2. Set up environment variables
3. Deploy using the provided Dockerfile
4. Test the deployment
5. Set up monitoring and scheduling

For questions or issues, refer to the platform's documentation or open an issue in the repository.

