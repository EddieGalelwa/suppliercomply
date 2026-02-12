# SupplierComply

**GS1 Barcode Compliance Platform for Kenya Medical Suppliers**

SupplierComply helps small medical suppliers in Kenya create GS1-compliant barcodes and generate KEMSA-ready reports. Built for the December 2026 KEMSA compliance deadline.

📖 **[Complete Setup Guide](SETUP_GUIDE.md)** - Local development and deployment instructions

🚀 **[Deploy to Render](deployment/DEPLOYMENT.md)** - Step-by-step Render deployment

🚂 **[Deploy to Railway](SETUP_GUIDE.md#railway-deployment)** - Railway deployment guide

📊 **[Platform Comparison](deployment/PLATFORM_COMPARISON.md)** - Render vs Railway vs VPS

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Pricing](#pricing)
- [Deployment](#deployment)
- [Support](#support)

---

## Features

- **GS1-128 Barcode Generator**: Generate print-ready barcodes with automatic GTIN-14 generation
- **KEMSA Export Assistant**: Upload CSV, map columns, download Excel in exact KEMSA format
- **Expiry Alerts**: Get notified 30/60/90 days before products expire (paid feature)
- **Payment Integration**: Manual reconciliation via Equity Bank Paybill 247247
- **Audit Reports**: PDF reports for compliance tracking (paid feature)

## Tech Stack

- **Backend**: Python 3.11 + Flask + SQLAlchemy
- **Database**: PostgreSQL
- **Frontend**: HTML5 + Tailwind CSS + Vanilla JavaScript
- **Image Storage**: Cloudinary
- **Email**: Flask-Mail (SMTP)
- **Barcode**: python-barcode + Pillow
- **Excel**: openpyxl
- **PDF**: ReportLab

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Cloudinary account (free tier)
- Gmail account with App Password (or SendGrid)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/suppliercomply.git
   cd suppliercomply
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb suppliercomply
   
   # Run schema
   psql suppliercomply < ../database/schema.sql
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the app**
   Open http://localhost:5000 in your browser

📖 **Detailed Setup Instructions**: See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete local setup with troubleshooting.

---

## Deployment

### Option 1: Render (Recommended for Beginners)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Push code to GitHub
2. Connect Render to your repo
3. Add PostgreSQL database
4. Configure environment variables
5. Deploy!

**Full Guide**: [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)

### Option 2: Railway (Recommended for Production)

1. Sign up at [railway.app](https://railway.app)
2. Create project from GitHub repo
3. Add PostgreSQL
4. Set environment variables
5. Deploy!

**Full Guide**: [SETUP_GUIDE.md#railway-deployment](SETUP_GUIDE.md#railway-deployment)

### Option 3: VPS (Full Control)

Deploy to Hetzner, DigitalOcean, AWS, or any VPS provider.

**Full Guide**: [SETUP_GUIDE.md#alternative-vps](SETUP_GUIDE.md#alternative-vps)

**Platform Comparison**: [deployment/PLATFORM_COMPARISON.md](deployment/PLATFORM_COMPARISON.md)

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | Yes |
| `CLOUDINARY_API_KEY` | Cloudinary API key | Yes |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | Yes |
| `MAIL_SERVER` | SMTP server | Yes |
| `MAIL_PORT` | SMTP port | Yes |
| `MAIL_USERNAME` | SMTP username | Yes |
| `MAIL_PASSWORD` | SMTP password | Yes |

## Project Structure

```
suppliercomply/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── routes_auth.py         # Authentication routes
│   ├── routes_barcode.py      # Barcode generation routes
│   ├── routes_kemsa.py        # KEMSA export routes
│   ├── routes_dashboard.py    # Dashboard routes
│   ├── routes_payment.py      # Payment routes
│   ├── routes_admin.py        # Admin routes
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment variables template
├── frontend/
│   ├── static/
│   │   ├── css/style.css      # Custom styles
│   │   └── js/main.js         # Main JavaScript
│   └── templates/             # HTML templates
│       ├── base.html          # Base template
│       ├── index.html         # Landing page
│       ├── auth.html          # Login/Register
│       ├── dashboard.html     # User dashboard
│       ├── barcode.html       # Barcode generator
│       ├── kemsa.html         # KEMSA export
│       ├── upgrade.html       # Payment/upgrade
│       ├── admin.html         # Admin dashboard
│       ├── 404.html           # Not found page
│       └── 500.html           # Error page
├── database/
│   └── schema.sql             # Database schema
├── deployment/
│   ├── DEPLOYMENT.md          # Render deployment guide
│   ├── PLATFORM_COMPARISON.md # Hosting platform comparison
│   └── render.yaml            # Render deployment config
├── business/
│   └── BUSINESS.md            # Sales scripts & email templates
├── SETUP_GUIDE.md             # Complete setup guide
├── README.md                  # This file
└── PROJECT_SUMMARY.md         # Project overview
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password

### Barcode
- `POST /barcode/generate` - Generate GS1 barcode
- `GET /barcode/history` - Get barcode history
- `GET /barcode/stats` - Get usage statistics

### KEMSA Export
- `POST /kemsa/upload` - Upload CSV file
- `POST /kemsa/preview` - Preview mapped data
- `POST /kemsa/download` - Download Excel file
- `GET /kemsa/template` - Download empty template

### Dashboard
- `GET /dashboard/api/stats` - Get dashboard stats
- `GET /dashboard/api/products` - Get products list
- `GET /dashboard/api/expiring` - Get expiring products
- `POST /dashboard/api/audit-report` - Generate PDF report

### Payment
- `GET /payment/api/status` - Get payment status
- `POST /payment/api/i-have-paid` - Mark as paid
- `POST /payment/api/cancel-pending` - Cancel pending payment

### Admin
- `GET /admin/api/dashboard` - Get admin stats
- `GET /admin/api/users` - Get all users
- `GET /admin/api/activities` - Get system activities

## Pricing

- **Free Trial**: 14 days, 10 barcodes/month, watermarked
- **Paid**: KSh 15,000/month, unlimited barcodes, all features

## Payment Flow

1. User registers and gets unique payment code (SC001, SC002, etc.)
2. User pays via M-Pesa → Lipa na M-Pesa → Paybill 247247
3. User enters their payment code as account number
4. User clicks "I Have Paid" on the platform
5. Admin checks Equity Bank statement for the payment code
6. Admin confirms payment in admin dashboard
7. User's account is activated instantly

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

- Email: support@suppliercomply.co.ke
- WhatsApp: +254 700 000 000

## Roadmap

- [ ] M-Pesa API integration for automatic reconciliation
- [ ] Bulk barcode generation
- [ ] QR code support
- [ ] Mobile app
- [ ] Multi-language support (Swahili)
- [ ] Integration with popular inventory systems

---

## Quick Deployment Checklist

### Before You Start
- [ ] Create GitHub account
- [ ] Create Cloudinary account (free)
- [ ] Set up Gmail App Password
- [ ] Choose platform: Render or Railway

### Deploy to Production
- [ ] Push code to GitHub
- [ ] Create PostgreSQL database
- [ ] Configure environment variables
- [ ] Deploy web service
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring
- [ ] Test all features

### Post-Launch
- [ ] Record demo videos
- [ ] Set up WhatsApp Business
- [ ] Start customer outreach

**Need Help?** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions with screenshots and troubleshooting.

---

Built with ❤️ for Kenya's medical suppliers
