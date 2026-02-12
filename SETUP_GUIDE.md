# SupplierComply - Complete Setup Guide

A comprehensive guide for setting up SupplierComply locally and deploying to production using Render or Railway.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Render Deployment](#render-deployment)
4. [Railway Deployment](#railway-deployment)
5. [Alternative: VPS/Dedicated Server](#alternative-vps)
6. [Environment Variables Reference](#environment-variables)
7. [Post-Deployment Configuration](#post-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Video Setup Guides](#video-guides)

---

## Prerequisites

### Required Accounts (Free Tier Available)

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [GitHub](https://github.com) | Code repository | Unlimited public repos |
| [Cloudinary](https://cloudinary.com) | Barcode image storage | 25GB storage + bandwidth |
| [Gmail](https://gmail.com) or [SendGrid](https://sendgrid.com) | Email notifications | 100 emails/day |
| [Render](https://render.com) OR [Railway](https://railway.app) | Hosting & database | Web service + PostgreSQL |

### Software to Install Locally

- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **PostgreSQL 13+**: [Download](https://www.postgresql.org/download/)
- **Git**: [Download](https://git-scm.com/downloads)
- **VS Code** (recommended): [Download](https://code.visualstudio.com/)

---

## Local Development Setup

### Step 1: Clone the Repository

```bash
# Using HTTPS
git clone https://github.com/YOUR_USERNAME/suppliercomply.git

# Or using SSH
git clone git@github.com:YOUR_USERNAME/suppliercomply.git

cd suppliercomply
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

You'll know it's activated when you see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs Flask, SQLAlchemy, barcode libraries, and all other dependencies.

### Step 4: Set Up PostgreSQL Database

**Option A: Using pgAdmin (GUI)**
1. Open pgAdmin
2. Right-click "Databases" → "Create" → "Database"
3. Name: `suppliercomply`
4. Click "Save"

**Option B: Using Command Line**
```bash
# Windows (psql must be in PATH)
psql -U postgres -c "CREATE DATABASE suppliercomply;"

# macOS/Linux
sudo -u postgres createdb suppliercomply
```

**Option C: Using psql Interactive Shell**
```bash
psql -U postgres
CREATE DATABASE suppliercomply;
\q
```

### Step 5: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit with your text editor
# Windows: notepad .env
# macOS/Linux: nano .env or vim .env
```

**Minimum required for local development:**

```env
# Database (local PostgreSQL)
DATABASE_URL=postgresql://postgres:your_password@localhost/suppliercomply

# Flask
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Cloudinary (get from cloudinary.com)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Step 6: Set Up Cloudinary (Required for Barcode Storage)

1. Go to https://cloudinary.com/users/register/free
2. Sign up with email
3. Verify your email
4. In the dashboard, find:
   - **Cloud Name** (e.g., `johndoe`)
   - **API Key** (e.g., `123456789012345`)
   - **API Secret** (click to reveal)
5. Add these to your `.env` file

### Step 7: Set Up Gmail App Password (For Email)

1. Enable 2-Factor Authentication:
   - Go to https://myaccount.google.com/security
   - Click "2-Step Verification" → "Get started"
   - Follow the setup process

2. Generate App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)"
   - Enter: "SupplierComply Local"
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)
   - **Remove spaces** when adding to `.env`: `abcdefghijklmnop`

### Step 8: Initialize Database

```bash
# Run the schema
psql -U postgres -d suppliercomply -f ../database/schema.sql

# Or if you have the Flask app running, it will auto-create tables
```

### Step 9: Run the Application

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

Open your browser: **http://localhost:5000**

### Step 10: Create Admin User (Optional)

The first user registered automatically becomes admin (ID 1). Alternatively, the schema includes a default admin:
- Email: `admin@suppliercomply.co.ke`
- Password: `Admin123!`

**Change this immediately after first login!**

---

## Render Deployment

Render offers a generous free tier with automatic deployments from GitHub.

### Pros
- ✅ Free tier available
- ✅ Automatic deployments from GitHub
- ✅ Built-in PostgreSQL
- ✅ Custom domains with free SSL
- ✅ Easy scaling

### Cons
- ⚠️ Free web services sleep after 15 minutes of inactivity (slow first load)

### Step 1: Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/suppliercomply.git
git push -u origin main
```

### Step 2: Create PostgreSQL Database

1. Go to https://dashboard.render.com
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: `suppliercomply-db`
   - **Database**: `suppliercomply`
   - **User**: (leave default)
   - **Region**: `Frankfurt (EU Central)` (closest to Kenya)
   - **Plan**: `Free`
4. Click "Create Database"
5. Copy the "Internal Database URL" - you'll need this

### Step 3: Create Web Service

1. In Render dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:

| Setting | Value |
|---------|-------|
| Name | `suppliercomply` |
| Region | `Frankfurt (EU Central)` |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `cd backend && pip install -r requirements.txt` |
| Start Command | `cd backend && gunicorn app:app` |
| Plan | `Free` |

4. Click "Advanced" and add environment variables:

| Key | Value | How to Get |
|-----|-------|------------|
| `SECRET_KEY` | Generate with `openssl rand -hex 32` | Run in terminal |
| `DATABASE_URL` | Paste from PostgreSQL step | Render dashboard |
| `CLOUDINARY_CLOUD_NAME` | Your cloud name | Cloudinary dashboard |
| `CLOUDINARY_API_KEY` | Your API key | Cloudinary dashboard |
| `CLOUDINARY_API_SECRET` | Your API secret | Cloudinary dashboard |
| `MAIL_SERVER` | `smtp.gmail.com` | - |
| `MAIL_PORT` | `587` | - |
| `MAIL_USE_TLS` | `True` | - |
| `MAIL_USERNAME` | Your Gmail | Your email |
| `MAIL_PASSWORD` | Gmail App Password | Google account settings |
| `FLASK_ENV` | `production` | - |

5. Click "Create Web Service"

6. Wait for deployment (2-5 minutes)

7. Your app is live at: `https://suppliercomply.onrender.com`

### Step 4: Custom Domain (Optional)

1. Register domain at https://truehost.co.ke (~KSh 1,000/year)
2. In Truehost DNS settings, add CNAME:
   - Name: `www`
   - Value: `suppliercomply.onrender.com`
3. In Render dashboard → Settings → Custom Domains
4. Add: `www.suppliercomply.co.ke`
5. SSL certificate is automatic

---

## Railway Deployment

Railway is a modern platform with better free tier limits than Render.

### Pros
- ✅ More generous free tier ($5 credit/month)
- ✅ No sleep on free tier (always on)
- ✅ Easier database setup
- ✅ Better performance
- ✅ Native GitHub integration

### Cons
- ⚠️ Requires credit card for verification (won't be charged on free tier)
- ⚠️ Slightly steeper learning curve

### Step 1: Sign Up for Railway

1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign up with GitHub
4. Verify with credit card (won't be charged on free tier)

### Step 2: Create New Project

**Option A: Deploy from GitHub**
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Select your `suppliercomply` repository
4. Railway will auto-detect Python and create a service

**Option B: Manual Setup**
1. Click "New Project"
2. Select "Empty Project"
3. Click "New" → "Database" → "Add PostgreSQL"
4. Click "New" → "Service" → "Empty Service"

### Step 3: Add PostgreSQL Database

1. In your project, click "New"
2. Select "Database" → "Add PostgreSQL"
3. Railway creates the database automatically
4. Click on the database service
5. Go to "Connect" tab
6. Copy the `DATABASE_URL` (it starts with `postgresql://`)

### Step 4: Configure Environment Variables

1. Click on your web service
2. Go to "Variables" tab
3. Click "New Variable" and add each:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (use reference) |
| `SECRET_KEY` | (Generate: `openssl rand -hex 32`) |
| `CLOUDINARY_CLOUD_NAME` | Your cloud name |
| `CLOUDINARY_API_KEY` | Your API key |
| `CLOUDINARY_API_SECRET` | Your API secret |
| `MAIL_SERVER` | `smtp.gmail.com` |
| `MAIL_PORT` | `587` |
| `MAIL_USE_TLS` | `True` |
| `MAIL_USERNAME` | Your Gmail |
| `MAIL_PASSWORD` | Your app password |
| `FLASK_ENV` | `production` |

**Note:** For `DATABASE_URL`, click "Add Reference" and select your PostgreSQL service.

### Step 5: Configure Build Settings

1. In your service, go to "Settings" tab
2. Set:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### Step 6: Deploy

1. Railway automatically deploys when you push to GitHub
2. Or click "Deploy" in the dashboard
3. Wait for build to complete (2-3 minutes)
4. Your app is live!

### Step 7: Custom Domain

1. In service settings, click "Custom Domain"
2. Enter: `www.suppliercomply.co.ke`
3. Railway provides DNS records
4. Add them to your domain registrar
5. SSL is automatic

---

## Alternative: VPS/Dedicated Server

For maximum control, deploy to a VPS like DigitalOcean, AWS EC2, or Hetzner.

### Recommended VPS Providers

| Provider | Price | Location |
|----------|-------|----------|
| [Hetzner](https://hetzner.com) | €4.51/month | Germany |
| [DigitalOcean](https://digitalocean.com) | $6/month | Multiple |
| [AWS Lightsail](https://aws.amazon.com/lightsail) | $5/month | Multiple |
| [Vultr](https://vultr.com) | $5/month | Multiple |

### Quick Setup (Ubuntu 22.04)

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx git

# Clone repository
cd /var/www
git clone https://github.com/YOUR_USERNAME/suppliercomply.git
cd suppliercomply/backend

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE suppliercomply;"
sudo -u postgres psql -c "CREATE USER suppliercomply WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE suppliercomply TO suppliercomply;"

# Create .env file
nano .env
# Add your environment variables

# Initialize database
psql -U suppliercomply -d suppliercomply -f ../database/schema.sql

# Test the app
python app.py
# Press Ctrl+C to stop

# Set up Gunicorn service
cat > /etc/systemd/system/suppliercomply.service << 'EOF'
[Unit]
Description=SupplierComply Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/suppliercomply/backend
Environment="PATH=/var/www/suppliercomply/backend/venv/bin"
ExecStart=/var/www/suppliercomply/backend/venv/bin/gunicorn --workers 3 --bind unix:app.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl start suppliercomply
systemctl enable suppliercomply

# Configure Nginx
cat > /etc/nginx/sites-available/suppliercomply << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/suppliercomply/backend/app.sock;
    }

    location /static {
        alias /var/www/suppliercomply/frontend/static;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/suppliercomply /etc/nginx/sites-enabled
nginx -t
systemctl restart nginx

# Set up SSL with Certbot
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `a1b2c3d4e5f6...` (64 chars) |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud | `johndoe` |
| `CLOUDINARY_API_KEY` | Cloudinary API key | `123456789012345` |
| `CLOUDINARY_API_SECRET` | Cloudinary secret | `a1b2c3d4e5f6...` |

### Email Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Use TLS | `True` |
| `MAIL_USERNAME` | Email username | `you@gmail.com` |
| `MAIL_PASSWORD` | App password | `abcdefghijklmnop` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment | `production` |
| `FLASK_DEBUG` | Debug mode | `False` |
| `EQUITY_PAYBILL` | Paybill number | `247247` |
| `MONTHLY_PRICE_KES` | Price in KES | `15000` |

---

## Post-Deployment Configuration

### 1. Test Core Features

Create a test account and verify:
- [ ] Registration works
- [ ] Login works
- [ ] Barcode generation works
- [ ] Image uploads to Cloudinary
- [ ] Email notifications arrive
- [ ] KEMSA export preview works

### 2. Set Up Monitoring

**Uptime Monitoring (Free)**
1. Go to https://uptimerobot.com
2. Sign up for free
3. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-domain.com/health`
   - Interval: 5 minutes
4. Add your email for alerts

### 3. Configure Backups

**Render:** Automatic daily backups (free tier keeps 7 days)

**Railway:** Automatic daily backups

**Manual Backup:**
```bash
# Export database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Upload to cloud storage (AWS S3, Google Cloud, etc.)
```

### 4. Set Up Google Analytics (Optional)

1. Go to https://analytics.google.com
2. Create property
3. Add tracking code to `base.html`:
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

---

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError" on deployment

**Cause:** Dependencies not installed
**Fix:** 
- Check `requirements.txt` is in the correct directory
- Verify build command runs successfully
- Check deployment logs

#### "Database connection failed"

**Cause:** Wrong DATABASE_URL
**Fix:**
- Verify database URL format: `postgresql://user:password@host:port/database`
- Check database exists
- Verify user has permissions

**Render:** Use "Internal Database URL" not external

#### "Cloudinary upload failed"

**Cause:** Wrong credentials or exceeded quota
**Fix:**
- Verify Cloudinary credentials
- Check Cloudinary dashboard for usage
- Check Cloudinary logs

#### "Email not sending"

**Cause:** SMTP configuration issue
**Fix:**
- For Gmail: Use App Password, not regular password
- Enable "Less secure app access" is NOT needed with App Passwords
- Check spam folders
- Verify SMTP settings

#### "Free tier limit reached" on Render

**Cause:** Render free web services sleep after 15 minutes
**Fix:**
- Upgrade to paid tier ($7/month)
- Or use Railway (no sleep)
- Or use ping service to keep awake (not recommended)

### Getting Help

1. Check application logs:
   - **Render:** Dashboard → Logs
   - **Railway:** Dashboard → Deployments → Logs
   - **VPS:** `journalctl -u suppliercomply`

2. Enable debug mode temporarily:
   ```env
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

3. Contact support:
   - Email: support@suppliercomply.co.ke
   - WhatsApp: +254 700 000 000

---

## Video Guides

### Video 1: Local Setup (5 minutes)

**Script:**
```
[0:00] Hi! Let's set up SupplierComply on your local machine in 5 minutes.

[0:10] First, install Python 3.11 from python.org and PostgreSQL from postgresql.org.

[0:30] Clone the repository: git clone https://github.com/...

[0:45] Create a virtual environment and activate it.

[1:00] Install dependencies: pip install -r requirements.txt

[1:15] Create a PostgreSQL database called "suppliercomply".

[1:30] Copy .env.example to .env and fill in your credentials.

[1:45] Sign up for Cloudinary and add your credentials to .env.

[2:00] Set up Gmail App Password and add to .env.

[2:30] Run the database schema.

[2:45] Start the app: python app.py

[3:00] Open http://localhost:5000 in your browser.

[3:15] Register a test account and generate your first barcode!

[3:30] That's it! You're ready to develop or customize SupplierComply.

[3:45] For production deployment, check our Render or Railway guides.

[4:00] Questions? Email support@suppliercomply.co.ke
```

### Video 2: Render Deployment (8 minutes)

**Script:**
```
[0:00] Let's deploy SupplierComply to Render for free.

[0:15] First, push your code to GitHub.

[0:45] Go to render.com and sign up with GitHub.

[1:00] Create a new PostgreSQL database.

[1:30] Create a new Web Service and connect your GitHub repo.

[2:00] Configure build command: cd backend && pip install -r requirements.txt

[2:15] Configure start command: cd backend && gunicorn app:app

[2:30] Add environment variables: SECRET_KEY, DATABASE_URL, Cloudinary, Gmail.

[3:30] Deploy! Wait 2-3 minutes for the build.

[4:00] Your app is live! Test registration and barcode generation.

[4:30] Set up a custom domain at truehost.co.ke.

[5:00] Add CNAME record pointing to your Render URL.

[5:30] Add custom domain in Render settings.

[6:00] SSL certificate is automatic.

[6:30] Set up uptime monitoring at uptimerobot.com.

[7:00] You're live and monitoring! Share your URL with customers.

[7:30] Questions? Check our troubleshooting section or contact support.
```

### Video 3: Railway Deployment (7 minutes)

**Script:**
```
[0:00] Let's deploy SupplierComply to Railway - my preferred platform.

[0:15] Railway has a better free tier than Render - no sleep mode!

[0:30] Sign up at railway.app with GitHub.

[0:45] Create a new project and deploy from GitHub.

[1:15] Add a PostgreSQL database - Railway handles everything.

[1:45] Configure environment variables using Railway's UI.

[2:30] Set build command and start command.

[3:00] Deploy! Railway auto-deploys on every git push.

[3:30] Your app is live with a railway.app subdomain.

[4:00] Add a custom domain in settings.

[4:30] Railway provides DNS records - add them to your domain.

[5:00] SSL is automatic.

[5:30] Test all features - barcode generation, email, etc.

[6:00] Set up monitoring.

[6:30] You're done! Railway gives you $5/month free credit.

[6:45] Questions? Contact support@suppliercomply.co.ke
```

---

## Quick Reference Commands

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run app
python app.py

# Install new dependency
pip install package-name
pip freeze > requirements.txt

# Database
psql -U postgres -d suppliercomply
\dt  # List tables
\q   # Quit
```

### Git Commands

```bash
# Push changes
git add .
git commit -m "Description"
git push origin main

# Pull updates
git pull origin main
```

### Database Backup/Restore

```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

---

## Next Steps

1. ✅ Set up local development environment
2. ✅ Customize branding (logo, colors)
3. ✅ Deploy to Render or Railway
4. ✅ Set up custom domain
5. ✅ Configure monitoring
6. ✅ Test payment flow
7. ✅ Record demo videos
8. ✅ Launch to customers!

---

**Last Updated**: 2024
**Version**: 1.0

For support: support@suppliercomply.co.ke
