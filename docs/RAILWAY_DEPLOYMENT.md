# Railway Deployment Guide

Complete guide to deploy the Okta Device Posture Provider to Railway.

## Prerequisites

1. **Railway Account**: Sign up at https://railway.app
2. **GitHub Account**: Repository must be on GitHub
3. **Railway CLI** (optional): Install with `npm install -g @railway/cli`

## Quick Deployment (Web Interface)

### Step 1: Prepare Repository

Your repository is already configured with:
- ✅ `Procfile` - Defines web process
- ✅ `railway.json` - Railway configuration
- ✅ `runtime.txt` - Python version
- ✅ `nixpacks.toml` - Build configuration
- ✅ `requirements.txt` - Dependencies

### Step 2: Deploy to Railway

#### Option A: Deploy from GitHub (Recommended)

1. **Log in to Railway**
   - Go to https://railway.app
   - Click "Login" and authenticate with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `BalaGanaparthi/okta-dpp-saml`

3. **Configure Deployment**
   - Railway will auto-detect the Python app
   - It will use the configurations from railway.json

4. **Wait for Build**
   - Railway will:
     - Install Python 3.11
     - Install dependencies from requirements.txt
     - Generate SAML certificates
     - Start the application
   - Build takes ~2-3 minutes

5. **Get Your URL**
   - Once deployed, Railway provides a URL like:
   - `https://okta-dpp-saml-production.up.railway.app`

#### Option B: Deploy with Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to existing project or create new
railway link

# Deploy
railway up

# Open in browser
railway open
```

### Step 3: Configure Environment Variables

1. **In Railway Dashboard**
   - Go to your project
   - Click "Variables" tab
   - Add the following variables:

```bash
# Server Configuration
PORT=8443
FLASK_ENV=production

# SAML Configuration (Update these!)
SAML_ENTITY_ID=https://your-app.up.railway.app
SAML_SSO_URL=https://your-app.up.railway.app/saml/sso
SAML_ACS_URL=https://your-app.up.railway.app/saml/acs

# Okta Configuration (Update these!)
OKTA_ENTITY_ID=http://www.okta.com/exk<your-app-id>
OKTA_ACS_URL=https://<your-org>.okta.com/sso/saml2/<app-id>

# Device Check Configuration
REQUIRE_MANAGED=true
REQUIRE_COMPLIANT=false
REQUIRE_ENCRYPTED=false
```

2. **Redeploy**
   - Railway will automatically redeploy with new variables

### Step 4: Update config.py for Environment Variables

The app needs to read from environment variables. Update is already included in the code.

### Step 5: Configure Custom Domain (Optional)

1. **In Railway Dashboard**
   - Go to "Settings" → "Domains"
   - Click "Generate Domain" for a railway.app subdomain
   - Or add custom domain:
     - Click "Custom Domain"
     - Enter your domain (e.g., `dpp.yourdomain.com`)
     - Add CNAME record to your DNS:
       - Name: `dpp`
       - Value: `your-app.up.railway.app`

2. **Update Environment Variables**
   - Update `SAML_ENTITY_ID` and `SAML_SSO_URL` with new domain

### Step 6: Configure Okta

1. **In Okta Admin Console**
   - Applications → Your SAML App → General Settings

2. **Update URLs**
   - **Single sign on URL**:
     ```
     https://your-app.up.railway.app/saml/sso
     ```
   - **Audience URI (SP Entity ID)**:
     ```
     https://your-app.up.railway.app
     ```

3. **Download Metadata**
   - Visit: `https://your-app.up.railway.app/saml/metadata`
   - Upload to Okta or manually configure

4. **Configure Device Posture**
   - In Okta, enable Device Assurance
   - Add your DPP as a device posture provider
   - Reference: `urn:okta:saml:2.0:DevicePosture`

### Step 7: Test Deployment

1. **Health Check**
   ```bash
   curl https://your-app.up.railway.app/health
   ```

2. **View Metadata**
   ```bash
   curl https://your-app.up.railway.app/saml/metadata
   ```

3. **Test SAML Flow**
   - Initiate authentication from Okta
   - Should redirect to your Railway-hosted DPP
   - See the stunning UI
   - Complete authentication

---

## Advanced Configuration

### Using PostgreSQL Database

Railway offers free PostgreSQL database:

1. **Add PostgreSQL Service**
   - In Railway project
   - Click "New" → "Database" → "Add PostgreSQL"

2. **Get Connection String**
   - Railway provides `DATABASE_URL` variable automatically

3. **Update Application**
   - Modify `device_checker.py` to use PostgreSQL
   - Add SQLAlchemy to requirements.txt
   - Implement database models

### Environment-Specific Configuration

Update `config.py` to read from environment variables:

```python
import os

class Config:
    def _default_config(self):
        return {
            'server': {
                'host': '0.0.0.0',
                'port': int(os.getenv('PORT', 8443)),
                'debug': os.getenv('FLASK_ENV') != 'production'
            },
            'saml': {
                'entity_id': os.getenv('SAML_ENTITY_ID', 'https://dpp.example.com'),
                'sso_url': os.getenv('SAML_SSO_URL', 'https://dpp.example.com/saml/sso'),
                # ... rest of config
            }
        }
```

### Monitoring and Logs

1. **View Logs**
   ```bash
   # Using CLI
   railway logs

   # Or in Dashboard
   # Go to "Deployments" → Click deployment → "View Logs"
   ```

2. **Set Up Monitoring**
   - Railway provides basic metrics
   - For advanced monitoring, integrate:
     - Sentry for error tracking
     - Datadog for APM
     - Prometheus + Grafana

---

## Troubleshooting

### Build Failures

**Issue**: Build fails with dependency errors

**Solution**:
```bash
# Update requirements.txt versions
# Ensure compatible versions of lxml, signxml
```

**Issue**: Certificate generation fails

**Solution**:
```toml
# In nixpacks.toml, ensure libxml2 and libxslt are included
nixPkgs = ["python311", "libxml2", "libxslt"]
```

### Runtime Errors

**Issue**: App crashes on startup

**Solution**:
```bash
# Check logs
railway logs

# Common causes:
# 1. Port binding - use 0.0.0.0:$PORT
# 2. Missing certificates - check build phase
# 3. Import errors - verify all dependencies installed
```

**Issue**: SAML errors

**Solution**:
```bash
# Verify certificates exist
railway run ls -la certs/

# Check environment variables
railway variables

# Test metadata endpoint
curl https://your-app.up.railway.app/saml/metadata
```

### Performance Issues

**Issue**: Slow response times

**Solution**:
1. **Upgrade Railway Plan**
   - Free tier: Shared resources
   - Pro tier: Dedicated resources

2. **Enable Caching**
   - Add Redis for session caching
   - Implement response caching

3. **Optimize Code**
   - Profile slow endpoints
   - Add database indexes
   - Use connection pooling

---

## Railway CLI Commands

```bash
# Login
railway login

# Link project
railway link

# Deploy
railway up

# View logs
railway logs

# Open in browser
railway open

# Run commands remotely
railway run python generate_certs.py

# View environment variables
railway variables

# Set environment variable
railway variables set KEY=VALUE

# SSH into container
railway shell

# View status
railway status
```

---

## Cost Estimation

### Free Tier
- **Included**: $5 credit/month
- **Resources**: Shared CPU, 512MB RAM
- **Bandwidth**: 100GB/month
- **Good for**: Development, testing, low traffic

### Pro Tier ($20/month)
- **Credit**: $20/month included
- **Resources**: Dedicated CPU, up to 8GB RAM
- **Bandwidth**: 100GB/month
- **Good for**: Production, medium traffic

### Cost Breakdown
- **CPU**: ~$0.000463/minute
- **Memory**: ~$0.000231/GB/minute
- **Expected monthly cost**: $5-15 for typical usage

---

## Production Checklist

Before going live:

- [ ] Custom domain configured
- [ ] SSL certificate active (automatic with Railway)
- [ ] Environment variables set correctly
- [ ] Okta integration tested
- [ ] SAML metadata uploaded to Okta
- [ ] Health check endpoint responding
- [ ] Logs monitored for errors
- [ ] Backup strategy in place
- [ ] Rate limiting configured (if needed)
- [ ] Security headers enabled
- [ ] CORS configured properly
- [ ] Error tracking set up (Sentry)
- [ ] Performance monitoring enabled
- [ ] Database backups configured (if using DB)
- [ ] Documentation updated with production URLs

---

## Scaling Considerations

### Horizontal Scaling
Railway supports scaling replicas:

```bash
# In railway.json
{
  "deploy": {
    "numReplicas": 3
  }
}
```

### Vertical Scaling
Increase resources in Railway dashboard:
- Go to Settings → Resources
- Adjust CPU and Memory

### Load Balancing
Railway automatically load balances across replicas.

### Session Management
For multiple replicas:
1. Use Redis for session storage
2. Or use stateless JWT tokens
3. Ensure SAML state is shared

---

## Continuous Deployment

### Auto-Deploy on Git Push

Railway automatically deploys when you push to main:

```bash
# Make changes
git add .
git commit -m "Update configuration"
git push origin main

# Railway detects push and auto-deploys
```

### Branch Deployments

Deploy specific branches:

1. In Railway Dashboard
2. Settings → Deployments
3. Enable "Deploy on push"
4. Configure branch patterns

### GitHub Actions Integration

Create `.github/workflows/railway.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

---

## Backup and Recovery

### Database Backups

If using PostgreSQL on Railway:

```bash
# Manual backup
railway run pg_dump -U postgres > backup.sql

# Automated backups (Railway Pro)
# Enabled automatically with daily snapshots
```

### Configuration Backup

```bash
# Export environment variables
railway variables > variables.txt

# Export to .env format
railway variables --env > .env.railway
```

### Disaster Recovery

1. **Backup Strategy**
   - Daily automated backups (Railway Pro)
   - Manual backups before major changes
   - Store backups in external storage (S3, GCS)

2. **Recovery Process**
   - Create new Railway project
   - Deploy from GitHub
   - Restore database from backup
   - Update environment variables
   - Update DNS records

---

## Security Best Practices

### Environment Variables
- ✅ Never commit secrets to git
- ✅ Use Railway's environment variables
- ✅ Rotate credentials regularly
- ✅ Use different values for staging/production

### SSL/TLS
- ✅ Railway provides automatic SSL
- ✅ Enforce HTTPS (redirect HTTP)
- ✅ Use strong cipher suites
- ✅ Enable HSTS headers

### Network Security
- ✅ Configure firewall rules (Railway Pro)
- ✅ Limit CORS origins
- ✅ Implement rate limiting
- ✅ Use IP whitelisting for admin endpoints

### Application Security
- ✅ Keep dependencies updated
- ✅ Regular security audits
- ✅ Monitor for vulnerabilities
- ✅ Implement request validation
- ✅ Use secure session management

---

## Support Resources

- **Railway Documentation**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://status.railway.app
- **GitHub Issues**: https://github.com/railwayapp/railway/issues

---

## Next Steps

1. **Deploy to Railway** using the instructions above
2. **Test thoroughly** in staging environment
3. **Configure Okta** with production URLs
4. **Monitor performance** and errors
5. **Scale as needed** based on traffic
6. **Set up alerting** for critical issues
7. **Document** your specific configuration

---

Your Okta Device Posture Provider is now ready to deploy to Railway! 🚀

The deployment process is streamlined and Railway handles most of the infrastructure complexity automatically.
