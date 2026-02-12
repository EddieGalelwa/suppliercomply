# SupplierComply Deployment Guide

Complete step-by-step guide to deploy SupplierComply to production.

## Table of Contents

1. [Render Deployment (Recommended)](#render-deployment)
2. [Cloudinary Setup](#cloudinary-setup)
3. [Email (SMTP) Setup](#email-setup)
4. [Custom Domain Setup](#custom-domain-setup)
5. [Payment System Setup](#payment-system-setup)
6. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Render Deployment

Render offers a generous free tier perfect for startups:
- **Web Service**: Free (sleeps after 15 min inactivity)
- **PostgreSQL**: Free (500MB storage)

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Name your repository `suppliercomply`
3. Make it private (recommended)
4. Push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/suppliercomply.git
   git push -u origin main
   ```

### Step 2: Create PostgreSQL Database on Render

1. Go to https://dashboard.render.com
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: `suppliercomply-db`
   - **Database**: `suppliercomply`
   - **User**: (leave default)
   - **Region**: Choose closest to your users (Frankfurt for Africa)
   - **Plan**: Free
4. Click "Create Database"
5. Copy the "Internal Database URL" - you'll need this

### Step 3: Create Web Service on Render

1. In Render dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `suppliercomply`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     cd backend && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     cd backend && gunicorn app:app
     ```
   - **Plan**: Free

4. Click "Advanced" and add environment variables:

   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | (Generate: `openssl rand -hex 32`) |
   | `DATABASE_URL` | (Paste from PostgreSQL step) |
   | `CLOUDINARY_CLOUD_NAME` | (From Cloudinary setup) |
   | `CLOUDINARY_API_KEY` | (From Cloudinary setup) |
   | `CLOUDINARY_API_SECRET` | (From Cloudinary setup) |
   | `MAIL_SERVER` | `smtp.gmail.com` |
   | `MAIL_PORT` | `587` |
   | `MAIL_USE_TLS` | `True` |
   | `MAIL_USERNAME` | (Your Gmail) |
   | `MAIL_PASSWORD` | (Gmail App Password) |
   | `FLASK_ENV` | `production` |

5. Click "Create Web Service"

6. Render will automatically deploy your app. Wait for the build to complete.

7. Your app will be live at: `https://suppliercomply.onrender.com`

---

## Cloudinary Setup

Cloudinary stores barcode images (free tier: 25GB).

1. Go to https://cloudinary.com/users/register/free
2. Sign up with your email
3. Verify your email address
4. In the dashboard, find:
   - **Cloud Name**: (e.g., `yourname`)
   - **API Key**: (long string of numbers)
   - **API Secret**: (click to reveal)
5. Add these to your Render environment variables

---

## Email Setup

### Option A: Gmail (Recommended for beginners)

1. Enable 2-Factor Authentication on your Google account:
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. Generate App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)" → "SupplierComply"
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. Add to environment variables:
   - `MAIL_USERNAME`: your-email@gmail.com
   - `MAIL_PASSWORD`: your-app-password (without spaces)

### Option B: SendGrid (For higher volume)

1. Sign up at https://signup.sendgrid.com
2. Verify your account
3. Create an API key:
   - Settings → API Keys → Create API Key
   - Name: "SupplierComply"
   - Permissions: "Full Access" or "Restricted Access" (Mail Send)
4. Add to environment variables:
   - `MAIL_SERVER`: `smtp.sendgrid.net`
   - `MAIL_PORT`: `587`
   - `MAIL_USE_TLS`: `True`
   - `MAIL_USERNAME`: `apikey`
   - `MAIL_PASSWORD`: your-sendgrid-api-key

---

## Custom Domain Setup

### Register Domain (Truehost.co.ke)

1. Go to https://truehost.co.ke
2. Search for `suppliercomply.co.ke`
3. Add to cart and checkout (~KSh 1,000/year)
4. Complete registration with your details

### Configure DNS

1. In Truehost dashboard, go to DNS Management
2. Add CNAME record:
   - **Name**: `www`
   - **Type**: `CNAME`
   - **Value**: `suppliercomply.onrender.com`
   - **TTL**: 3600
3. Add redirect (optional):
   - Redirect `suppliercomply.co.ke` → `www.suppliercomply.co.ke`

### Add Custom Domain to Render

1. In Render dashboard, go to your Web Service
2. Click "Settings" → "Custom Domains"
3. Click "Add Custom Domain"
4. Enter: `www.suppliercomply.co.ke`
5. Render will provide a verification record - add this to your DNS if needed
6. Wait for SSL certificate to be issued (automatic, may take a few minutes)

---

## Payment System Setup

### Test Equity Paybill 247247

1. Send yourself KSh 10 via M-Pesa:
   - M-Pesa → Lipa na M-Pesa → Paybill
   - Business Number: `247247`
   - Account Number: `TEST001`
   - Amount: `10`

2. Check your Equity Bank account:
   - Equity Mobile App, or
   - Dial `*247#`, or
   - Online banking

3. Verify the deposit appears with account number `TEST001`

### Configure Payment Codes

1. First 100 users will get codes SC001-SC100
2. These are auto-generated on registration
3. Pre-reserve codes for key customers if needed

### Admin Payment Workflow

1. User clicks "I Have Paid" → appears in admin pending queue
2. Check Equity statement for payment code
3. In admin dashboard, search payment code
4. Click "Confirm Payment" → user activated instantly

---

## Post-Deployment Checklist

### Immediate Tests

- [ ] Register a new user → receives payment code
- [ ] Login → sees dashboard
- [ ] Generate barcode → PNG downloads
- [ ] Upload CSV → column mapping works
- [ ] Payment flow → appears in admin queue

### Security Checks

- [ ] HTTPS is working (no mixed content warnings)
- [ ] Password reset email arrives
- [ ] Session expires after inactivity
- [ ] Admin routes are protected

### Performance Checks

- [ ] Page loads in < 3 seconds
- [ ] Barcode generation < 5 seconds
- [ ] CSV upload works for 1000+ rows

### Monitoring Setup

1. **Uptime Monitoring** (free options):
   - UptimeRobot: https://uptimerobot.com
   - Set up ping to `https://your-domain.com/health`

2. **Error Tracking** (optional):
   - Sentry: https://sentry.io (free tier)
   - Add to Flask app for error reporting

---

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection locally
psql $DATABASE_URL -c "SELECT 1;"
```

### Cloudinary Upload Fails

- Check Cloudinary dashboard for usage limits
- Verify API credentials in environment variables
- Check Cloudinary logs

### Email Not Sending

- For Gmail: Ensure "Less secure app access" is OFF (use App Passwords)
- Check spam folders
- Verify SMTP settings in environment variables

### App Won't Start

Check Render logs:
1. Go to Web Service → Logs
2. Look for Python errors
3. Common issues:
   - Missing environment variables
   - Database connection failed
   - Missing dependencies

---

## Scaling Up

When you outgrow the free tier:

### Render Paid Plans

- **Starter**: $7/month (never sleeps, 512MB RAM)
- **Standard**: $25/month (2GB RAM, better performance)

### Database Scaling

- Render PostgreSQL Pro: $15/month (up to 4GB)
- Or migrate to AWS RDS / Google Cloud SQL

### Cloudinary Scaling

- Free: 25GB storage, 25GB bandwidth
- Plus: $25/month (225GB storage)

---

## Backup Strategy

### Database Backups

Render automatically backs up PostgreSQL daily. To download:

```bash
# Connect to Render PostgreSQL
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Code Backups

- GitHub repository is your primary backup
- Keep local copies of `.env` files (never commit them!)

---

## Support

If you encounter issues:

1. Check Render logs first
2. Review this deployment guide
3. Check Flask documentation: https://flask.palletsprojects.com
4. Contact support: support@suppliercomply.co.ke

---

**Congratulations! Your SupplierComply instance is now live! 🎉**
