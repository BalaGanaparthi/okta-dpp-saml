# Railway Quick Start

Deploy your Okta Device Posture Provider to Railway in under 5 minutes!

## Method 1: Web Interface (Easiest)

### 1. Login to Railway
Go to https://railway.app and login with GitHub

### 2. Deploy
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose **`BalaGanaparthi/okta-dpp-saml`**
4. Wait ~2 minutes for deployment

### 3. Generate Domain
1. Click **"Settings"** → **"Domains"**
2. Click **"Generate Domain"**
3. Copy your URL: `https://okta-dpp-saml-production.up.railway.app`

### 4. Set Environment Variables
1. Click **"Variables"** tab
2. Add these variables:

```
SAML_ENTITY_ID=https://your-app.up.railway.app
SAML_SSO_URL=https://your-app.up.railway.app/saml/sso
OKTA_ENTITY_ID=http://www.okta.com/exk<your-id>
OKTA_ACS_URL=https://<your-org>.okta.com/sso/saml2/<app-id>
REQUIRE_MANAGED=true
```

### 5. Test
Visit: `https://your-app.up.railway.app/health`

**Done!** 🎉

---

## Method 2: CLI (For Developers)

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Deploy
```bash
# Login
railway login

# Deploy
./railway-deploy.sh
```

### 3. Configure
```bash
# Set variables
railway variables set SAML_ENTITY_ID=https://your-app.up.railway.app
railway variables set SAML_SSO_URL=https://your-app.up.railway.app/saml/sso

# View logs
railway logs

# Open in browser
railway open
```

**Done!** 🎉

---

## Configure Okta

Once deployed, update your Okta SAML app:

### 1. In Okta Admin Console
Applications → Your SAML App → General Settings

### 2. Update URLs
- **Single sign on URL**: `https://your-app.up.railway.app/saml/sso`
- **Audience URI**: `https://your-app.up.railway.app`

### 3. Download Metadata
Visit: `https://your-app.up.railway.app/saml/metadata`

### 4. Test
Initiate SAML authentication from Okta!

---

## Useful Commands

```bash
# View deployment status
railway status

# View logs
railway logs --follow

# SSH into container
railway shell

# View environment variables
railway variables

# Open dashboard
railway open

# Delete deployment
railway down
```

---

## Troubleshooting

### Build Failed
```bash
# Check build logs
railway logs --deployment

# Common fix: Update dependencies
git add .
git commit -m "Update dependencies"
git push
```

### App Not Responding
```bash
# Check if PORT is set
railway variables

# Should show: PORT=8443 (or Railway's assigned port)

# Check logs for errors
railway logs
```

### SAML Errors
```bash
# Verify metadata
curl https://your-app.up.railway.app/saml/metadata

# Check certificates
railway run ls -la certs/

# Should show: saml.crt and saml.key
```

---

## Cost
- **Free Tier**: $5 credit/month (~500 hours)
- **Typical Usage**: $0-5/month for low traffic
- **Pro Tier**: $20/month for production

---

## Next Steps
- ✅ Deploy to Railway
- ✅ Configure Okta
- ✅ Test authentication
- 📊 Monitor with Railway dashboard
- 🔒 Add custom domain (optional)
- 📈 Scale as needed

Full documentation: **RAILWAY_DEPLOYMENT.md**

---

**Your app is now live! 🚀**

Share your deployment URL and start verifying devices!
