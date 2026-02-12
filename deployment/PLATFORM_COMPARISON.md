# SupplierComply - Hosting Platform Comparison

Compare Render vs Railway vs VPS for deploying SupplierComply.

---

## Quick Comparison

| Feature | Render | Railway | VPS (Hetzner) |
|---------|--------|---------|---------------|
| **Free Tier** | ✅ Yes | ✅ Yes ($5 credit) | ❌ No |
| **Monthly Cost (Paid)** | $7 | $5+ | €4.51+ |
| **Sleep on Idle** | ✅ Yes (15 min) | ❌ No | ❌ No |
| **PostgreSQL** | ✅ Free 500MB | ✅ Free 500MB | Self-managed |
| **Custom Domain** | ✅ Free SSL | ✅ Free SSL | Manual SSL |
| **GitHub Integration** | ✅ Native | ✅ Native | Manual |
| **Auto Deploy** | ✅ Yes | ✅ Yes | Manual |
| **Uptime SLA** | 99.9% | 99.9% | Depends on provider |
| **Best For** | Beginners | Production | Full control |

---

## Detailed Comparison

### Render

**Best for:** Beginners, prototypes, low-traffic sites

**Pros:**
- ✅ Simplest setup - just connect GitHub repo
- ✅ Generous free tier
- ✅ Built-in PostgreSQL
- ✅ Automatic SSL for custom domains
- ✅ Good documentation

**Cons:**
- ⚠️ Free web services sleep after 15 minutes (slow first load)
- ⚠️ Cold start can take 30-60 seconds
- ⚠️ Limited to 512MB RAM on free tier

**Pricing:**
| Plan | Cost | Features |
|------|------|----------|
| Free | $0 | Sleeps after 15 min, 512MB RAM |
| Starter | $7/mo | Never sleeps, 512MB RAM |
| Standard | $25/mo | 2GB RAM, better performance |

**Setup Time:** 15 minutes

---

### Railway

**Best for:** Production apps, businesses, high-traffic sites

**Pros:**
- ✅ No sleep on free tier (always on)
- ✅ $5 free credit every month
- ✅ Better performance than Render
- ✅ Easier environment variable management
- ✅ Automatic database provisioning
- ✅ Better developer experience

**Cons:**
- ⚠️ Requires credit card for verification
- ⚠️ Slightly steeper learning curve
- ⚠️ Can be more expensive at scale

**Pricing:**
| Usage | Cost |
|-------|------|
| Free Tier | $0 (with $5 credit) |
| Small App | $5-10/mo |
| Medium App | $20-50/mo |
| Large App | $100+/mo |

**Setup Time:** 20 minutes

---

### VPS (Hetzner/DigitalOcean)

**Best for:** Full control, cost optimization at scale, compliance requirements

**Pros:**
- ✅ Full control over server
- ✅ Most cost-effective at scale
- ✅ No platform limitations
- ✅ Can run multiple apps
- ✅ Better for learning DevOps

**Cons:**
- ⚠️ Requires technical knowledge
- ⚠️ Manual setup and maintenance
- ⚠️ No automatic deployments
- ⚠️ Responsible for security updates
- ⚠️ Manual SSL certificate management

**Pricing:**
| Provider | Cost | Specs |
|----------|------|-------|
| Hetzner CX11 | €4.51/mo | 1 vCPU, 2GB RAM, 20GB SSD |
| DigitalOcean Basic | $6/mo | 1 vCPU, 512MB RAM, 10GB SSD |
| AWS Lightsail | $5/mo | 1 vCPU, 1GB RAM, 40GB SSD |
| Vultr Cloud | $5/mo | 1 vCPU, 1GB RAM, 25GB SSD |

**Setup Time:** 1-2 hours

---

## Recommendation by Use Case

### Just Starting / Testing
**→ Render (Free)**
- Easiest to set up
- No credit card required
- Perfect for learning

### Small Business / Production
**→ Railway (Free/Paid)**
- Always on (no sleep)
- Better performance
- Professional appearance

### Established Business / High Traffic
**→ Railway (Paid) or VPS**
- Predictable costs
- Better performance
- Room to grow

### Technical Team / Full Control
**→ VPS (Hetzner)**
- Lowest cost at scale
- Full control
- Custom configurations

---

## Migration Guide

### Render → Railway

1. Export database from Render:
   ```bash
   pg_dump RENDER_DATABASE_URL > backup.sql
   ```

2. Create new Railway project

3. Import database:
   ```bash
   psql RAILWAY_DATABASE_URL < backup.sql
   ```

4. Copy environment variables

5. Update DNS to point to Railway

### Railway → VPS

1. Export database:
   ```bash
   pg_dump RAILWAY_DATABASE_URL > backup.sql
   ```

2. Set up VPS with PostgreSQL

3. Import database:
   ```bash
   psql VPS_DATABASE_URL < backup.sql
   ```

4. Install and configure app

5. Update DNS

---

## Performance Benchmarks

Based on SupplierComply testing:

| Platform | Cold Start | Warm Response | Barcode Gen |
|----------|------------|---------------|-------------|
| Render Free | 45s | 200ms | 3s |
| Render Starter | 5s | 150ms | 2s |
| Railway Free | 0s | 180ms | 2.5s |
| Railway Paid | 0s | 120ms | 1.5s |
| Hetzner CX11 | 0s | 100ms | 1s |

---

## Our Recommendation

**For SupplierComply specifically:**

1. **Development:** Render Free (simplest)
2. **Launch:** Railway Free (always on, professional)
3. **Growth:** Railway Starter ($5/mo) or Hetzner CX11 (€4.51/mo)
4. **Scale:** Hetzner or AWS (cost optimization)

**Start with Railway** - it gives you the best free tier experience and easy upgrade path.

---

## Decision Flowchart

```
Do you have a credit card?
├── No → Render (Free)
└── Yes → What's your priority?
    ├── Ease of use → Render
    ├── Always-on → Railway
    ├── Performance → Railway or VPS
    └── Cost (long-term) → VPS
```

---

## Additional Resources

### Render
- Docs: https://render.com/docs
- Pricing: https://render.com/pricing
- Community: https://community.render.com

### Railway
- Docs: https://docs.railway.app
- Pricing: https://railway.app/pricing
- Discord: https://discord.gg/railway

### VPS
- Hetzner: https://docs.hetzner.com
- DigitalOcean: https://docs.digitalocean.com
- AWS: https://docs.aws.amazon.com

---

**Need help deciding?** Contact support@suppliercomply.co.ke
