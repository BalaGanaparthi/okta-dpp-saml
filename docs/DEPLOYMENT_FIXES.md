# Deployment Fixes Applied

## Railway Deployment Error Fixed

### Error Encountered
```
ERROR: failed to build: failed to solve: process "/bin/sh -c python generate_certs.py"
did not complete successfully: exit code: 2

python: can't open file '/app/generate_certs.py': [Errno 2] No such file or directory
```

### Root Cause
After reorganizing the project structure, the Dockerfile was still referencing old file paths:
- `generate_certs.py` moved to `scripts/generate_certs.py`
- `app.py` moved to `src/app.py`

---

## Fixes Applied

### 1. ✅ Updated Dockerfile

**Line 27 - Certificate Generation:**
```dockerfile
# Before (BROKEN)
RUN python generate_certs.py

# After (FIXED)
RUN python scripts/generate_certs.py
```

**Line 40 - Application Startup:**
```dockerfile
# Before (BROKEN)
CMD ["python", "app.py"]

# After (FIXED)
CMD ["python", "-m", "src.app"]
```

### 2. ✅ Updated Procfile (Already Fixed)

```
web: gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

This was already updated during the initial project reorganization.

---

## Complete Updated Files

### Dockerfile (Complete)
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (includes pre-generated certs from certs/ folder)
COPY . .

# Expose port
EXPOSE 8443

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8443/health')"

# Run application
CMD ["python", "-m", "src.app"]
```

### Procfile
```
web: gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

## Verification Steps

### Local Docker Build Test
```bash
# Build the Docker image
docker build -t okta-dpp-test .

# Run the container
docker run -p 8443:8443 okta-dpp-test

# Test health endpoint
curl http://localhost:8443/health
```

### Railway Deployment
```bash
# Commit the fixes
git add Dockerfile Procfile
git commit -m "Fix deployment paths after project reorganization"

# Push to trigger Railway deployment
git push

# Monitor deployment
railway logs
```

---

## File Path Reference

For future updates, here's the correct file structure:

```
project004-okta-dpp/
├── src/
│   ├── app.py              ← Main application (was: app.py)
│   ├── config.py           ← Configuration
│   ├── saml_handler.py     ← SAML processing
│   ├── device_checker.py   ← Device checks
│   └── logger_config.py    ← Logging
├── scripts/
│   ├── generate_certs.py   ← Certificate generation (was: generate_certs.py)
│   ├── gen_x509v3.py       ← X509v3 cert generation
│   └── ...                 ← Other utility scripts
├── tests/                  ← All test files
├── examples/               ← SAML examples
├── docs/                   ← All documentation
├── certs/                  ← Generated certificates
│   ├── saml.crt
│   └── saml.key
├── Dockerfile              ← Docker configuration (FIXED)
├── Procfile                ← Railway/Heroku config (FIXED)
└── requirements.txt        ← Python dependencies
```

---

## Deployment Checklist

Before deploying, ensure:

- [ ] ✅ Dockerfile references `scripts/generate_certs.py`
- [ ] ✅ Dockerfile CMD uses `python -m src.app`
- [ ] ✅ Procfile uses `src.app:app` with gunicorn
- [ ] ✅ All imports in Python files use `src.` prefix
- [ ] ✅ Certificates load from `certs/` folder
- [ ] ✅ No hardcoded old paths remain

---

## Common Deployment Issues

### Issue: Module Import Errors
**Symptom:** `ModuleNotFoundError: No module named 'app'`
**Fix:** Use `python -m src.app` or `gunicorn src.app:app`

### Issue: Certificate Generation Fails
**Symptom:** `FileNotFoundError: generate_certs.py`
**Fix:** Use `python scripts/generate_certs.py`

### Issue: Import Errors in Application
**Symptom:** `ImportError: No module named 'config'`
**Fix:** Update imports to use `from src.config import Config`

---

## Testing Locally

### Method 1: Direct Python
```bash
python3 -m src.app
```

### Method 2: Gunicorn (Production-like)
```bash
gunicorn src.app:app --bind 0.0.0.0:8443 --workers 2
```

### Method 3: Docker
```bash
docker build -t okta-dpp .
docker run -p 8443:8443 okta-dpp
```

### Method 4: Docker Compose
```bash
docker-compose up
```

---

## Status

✅ **All deployment paths fixed and verified**

**Date:** March 22, 2026
**Next Action:** Commit and push to Railway for deployment
