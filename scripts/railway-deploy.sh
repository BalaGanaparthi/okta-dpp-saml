#!/bin/bash

# Railway Deployment Script
# Quick setup for deploying to Railway

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        Railway Deployment - Okta Device Posture Provider     ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found"
    echo ""
    echo "Install it with:"
    echo "  npm install -g @railway/cli"
    echo ""
    echo "Or use the Railway web interface:"
    echo "  https://railway.app"
    exit 1
fi

echo "✅ Railway CLI found"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
fi

echo "✅ Logged in to Railway"
echo ""

# Check if project is linked
if ! railway status &> /dev/null; then
    echo "🔗 No Railway project linked"
    echo ""
    echo "Options:"
    echo "  1. Link to existing project: railway link"
    echo "  2. Create new project: railway init"
    echo ""
    read -p "Create new project? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        railway init
    else
        echo "Please run 'railway link' to link an existing project"
        exit 1
    fi
fi

echo "✅ Railway project linked"
echo ""

# Deploy
echo "🚀 Deploying to Railway..."
echo ""
railway up

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  Deployment Complete!                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Get deployment URL
echo "🌐 Getting deployment URL..."
RAILWAY_URL=$(railway domain 2>&1 | grep -oP 'https://[^\s]+' || echo "")

if [ -n "$RAILWAY_URL" ]; then
    echo "✅ Your app is deployed at:"
    echo "   $RAILWAY_URL"
    echo ""
else
    echo "⚠️  Deployment URL not found yet"
    echo "   Run 'railway domain' to generate one"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Generate Domain (if not done):"
echo "   railway domain"
echo ""
echo "2. Set Environment Variables:"
echo "   railway variables set SAML_ENTITY_ID=https://your-app.up.railway.app"
echo "   railway variables set SAML_SSO_URL=https://your-app.up.railway.app/saml/sso"
echo "   railway variables set OKTA_ENTITY_ID=http://www.okta.com/exk<id>"
echo "   railway variables set OKTA_ACS_URL=https://<org>.okta.com/sso/saml2/<id>"
echo ""
echo "3. View Logs:"
echo "   railway logs"
echo ""
echo "4. Open in Browser:"
echo "   railway open"
echo ""
echo "5. Check Health:"
echo "   curl $RAILWAY_URL/health"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Full documentation: RAILWAY_DEPLOYMENT.md"
echo ""
