# SupplierComply - File Guide

Complete reference for every file in the project.

---

## Documentation Files

| File | Purpose | Read This If... |
|------|---------|-----------------|
| `README.md` | Project overview, quick start | You're new to the project |
| `SETUP_GUIDE.md` | Complete setup & deployment | You want to deploy or develop |
| `PROJECT_SUMMARY.md` | What's been built | You want a high-level overview |
| `FILE_GUIDE.md` | This file - explains all files | You want to understand the codebase |

### Deployment Documentation

| File | Purpose |
|------|---------|
| `deployment/DEPLOYMENT.md` | Step-by-step Render deployment |
| `deployment/PLATFORM_COMPARISON.md` | Compare Render vs Railway vs VPS |
| `deployment/DEPLOYMENT_FLOWCHART.md` | Visual deployment flowcharts |
| `deployment/render.yaml` | One-click Render deploy config |

### Business Documentation

| File | Purpose |
|------|---------|
| `business/BUSINESS.md` | Sales scripts, email templates, pricing strategy |

---

## Backend Files (`backend/`)

### Core Application

| File | Purpose | Key Functions |
|------|---------|---------------|
| `app.py` | Main Flask app, database models, config | `create_app()`, User model, Product model, Payment model |

**Contains:**
- Flask app factory
- SQLAlchemy database models
- Cloudinary configuration
- Security headers
- Error handlers

### Route Modules

| File | Purpose | Routes |
|------|---------|--------|
| `routes_auth.py` | Authentication | `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/forgot-password`, `/auth/reset-password` |
| `routes_barcode.py` | Barcode generation | `/barcode/generate`, `/barcode/history`, `/barcode/stats` |
| `routes_kemsa.py` | KEMSA export | `/kemsa/upload`, `/kemsa/preview`, `/kemsa/download`, `/kemsa/template` |
| `routes_dashboard.py` | User dashboard | `/dashboard/api/stats`, `/dashboard/api/products`, `/dashboard/api/audit-report` |
| `routes_payment.py` | Payment system | `/payment/api/status`, `/payment/api/i-have-paid`, `/payment/api/admin/confirm` |
| `routes_admin.py` | Admin panel | `/admin/api/dashboard`, `/admin/api/users`, `/admin/api/activities` |

### Configuration

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies with exact versions |
| `.env.example` | Template for environment variables |

---

## Frontend Files (`frontend/`)

### Templates (`templates/`)

| File | Purpose | Who Sees It |
|------|---------|-------------|
| `base.html` | Base template with nav, footer | All pages extend this |
| `index.html` | Landing page | Visitors |
| `auth.html` | Login, register, password reset | Unauthenticated users |
| `dashboard.html` | User dashboard | Logged-in users |
| `barcode.html` | Barcode generator | Logged-in users |
| `kemsa.html` | KEMSA export wizard | Logged-in users |
| `upgrade.html` | Payment/upgrade page | Logged-in users |
| `admin.html` | Admin dashboard | Admin users only |
| `404.html` | Not found error | Everyone |
| `500.html` | Server error | Everyone |

### Static Files (`static/`)

| File | Purpose |
|------|---------|
| `css/style.css` | Custom styles beyond Tailwind |
| `js/main.js` | Main JavaScript utilities, flash messages, API helpers |

---

## Database Files (`database/`)

| File | Purpose |
|------|---------|
| `schema.sql` | PostgreSQL schema - creates all tables, indexes, triggers |

**Creates:**
- `users` table
- `products` table
- `payments` table
- `activities` table
- Indexes for performance
- Default admin user

---

## File Relationships

```
User Request
     │
     ▼
┌─────────────────┐
│   Nginx/Proxy   │ (Render/Railway handles this)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Flask app.py  │
│   (routes the   │
│    request)     │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┬────────┐
    ▼         ▼        ▼        ▼        ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│routes_│ │routes_│ │routes_│ │routes_│ │routes_│
│ auth  │ │barcode│ │ kemsa │ │payment│ │ admin │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    │         │         │         │         │
    │    ┌────┘         │         │         │
    │    ▼              │         │         │
    │ ┌────────┐        │         │         │
    │ │Cloudin-│        │         │         │
    │ │  ary   │        │         │         │
    │ └────────┘        │         │         │
    │                   │         │         │
    └───────────────────┴─────────┴─────────┘
                        │
                        ▼
                ┌───────────────┐
                │  PostgreSQL   │
                │   Database    │
                └───────────────┘
```

---

## Request Flow Example

### Barcode Generation Flow

```
1. User clicks "Generate Barcode" in barcode.html
          │
          ▼
2. JavaScript sends POST to /barcode/generate
          │
          ▼
3. routes_barcode.py receives request
   - Validates input
   - Checks user limits
   - Generates GTIN-14
   - Creates barcode image
          │
          ▼
4. Uploads to Cloudinary
          │
          ▼
5. Saves to PostgreSQL (products table)
          │
          ▼
6. Returns JSON with barcode URL
          │
          ▼
7. JavaScript displays image in barcode.html
```

### Payment Flow

```
1. User pays via M-Pesa to Paybill 247247
   (enters payment code as account number)
          │
          ▼
2. User clicks "I Have Paid" in upgrade.html
          │
          ▼
3. routes_payment.py creates pending payment
          │
          ▼
4. Admin sees pending in admin.html
          │
          ▼
5. Admin checks Equity Bank statement
          │
          ▼
6. Admin clicks "Confirm Payment"
          │
          ▼
7. routes_payment.py updates user to paid
   - Sets paid_until = today + 30 days
   - Sends confirmation email
          │
          ▼
8. User sees paid features immediately
```

---

## Environment Variables File

### `.env.example` Explained

```env
# Database - Connection string for PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/suppliercomply

# Flask - Secret key for sessions (generate random)
SECRET_KEY=your-random-secret-key-here
FLASK_ENV=production  # or 'development' for local

# Cloudinary - Image storage credentials
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email - SMTP settings for notifications
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Payment - Reference only (manual reconciliation)
EQUITY_PAYBILL=247247
```

---

## Key Functions Reference

### Barcode Generation (`routes_barcode.py`)

| Function | Purpose |
|----------|---------|
| `calculate_gs1_check_digit()` | Validates GTIN-14 check digit |
| `generate_gtin_14()` | Creates valid GTIN-14 number |
| `create_gs1_128_barcode()` | Generates barcode image with text |

### Payment System (`routes_payment.py`)

| Function | Purpose |
|----------|---------|
| `generate_payment_code()` | Creates unique codes (SC001, SC002...) |
| `log_activity()` | Records user actions |
| `send_payment_confirmation_email()` | Sends welcome email to paid users |

### KEMSA Export (`routes_kemsa.py`)

| Function | Purpose |
|----------|---------|
| `parse_csv_file()` | Reads and parses uploaded CSV |
| `validate_kemsa_data()` | Checks data meets KEMSA requirements |
| `create_kemsa_excel()` | Generates formatted Excel file |

---

## Customization Points

### To Change Branding

| File | What to Change |
|------|----------------|
| `templates/base.html` | Logo, colors in Tailwind config |
| `templates/index.html` | Hero section, features, pricing |
| `static/css/style.css` | Custom styles |

### To Change Pricing

| File | What to Change |
|------|----------------|
| `templates/index.html` | Pricing section |
| `templates/upgrade.html` | Payment amount display |
| `routes_payment.py` | `amount=15000` in payment creation |
| `business/BUSINESS.md` | Pricing strategy docs |

### To Add Features

| File | What to Add |
|------|-------------|
| `app.py` | New database models |
| `routes_*.py` | New API endpoints |
| `templates/*.html` | New pages |
| `static/js/main.js` | New JavaScript utilities |

---

## Testing Files

While there are no dedicated test files (MVP approach), you can test using:

| What to Test | How |
|--------------|-----|
| Registration | Create account at `/auth/register` |
| Barcode generation | Go to `/barcode`, fill form |
| KEMSA export | Go to `/kemsa`, upload CSV |
| Payment flow | Click "I Have Paid", check admin |

---

## File Sizes (Approximate)

| Category | Files | Lines of Code |
|----------|-------|---------------|
| Backend Python | 7 | ~2,500 |
| Frontend HTML | 10 | ~3,500 |
| CSS/JS | 2 | ~800 |
| Documentation | 7 | ~3,000 |
| **Total** | **26** | **~9,800** |

---

## Quick Navigation

**I want to...** → **Go to...**

- Deploy the app → `SETUP_GUIDE.md`
- Understand the code → This file
- Change pricing → `templates/upgrade.html`
- Add a feature → `backend/routes_*.py`
- Customize styling → `static/css/style.css`
- Write sales copy → `business/BUSINESS.md`
- Fix a bug → Check logs, then relevant `routes_*.py`
- Add a page → Create `templates/newpage.html`, add route in `app.py`

---

**Last Updated**: 2024
**Total Files**: 26
**Status**: Production Ready
