# Deployment Guide

This guide covers various deployment options for the Okta Device Posture Provider.

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Kubernetes](#kubernetes)

---

## Local Development

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Generate certificates
python generate_certs.py

# Run the service
python app.py
```

Access at: `http://localhost:8443`

### Development with Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

---

## Docker Deployment

### Build and Run with Docker

```bash
# Build image
docker build -t okta-dpp:latest .

# Run container
docker run -d \
  --name okta-dpp \
  -p 8443:8443 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/certs:/app/certs \
  okta-dpp:latest
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Configuration

**Mount custom config:**
```bash
docker run -d \
  -p 8443:8443 \
  -v /path/to/config.yaml:/app/config.yaml \
  okta-dpp:latest
```

**Use existing certificates:**
```bash
docker run -d \
  -p 8443:8443 \
  -v /path/to/certs:/app/certs \
  okta-dpp:latest
```

**Environment variables:**
```bash
docker run -d \
  -p 8443:8443 \
  -e DPP_PORT=9443 \
  okta-dpp:latest
```

---

## Production Deployment

### Prerequisites

1. **Valid SSL/TLS Certificate**
   - Obtain from Let's Encrypt, commercial CA, or internal PKI
   - Replace self-signed certificates in `certs/` directory

2. **Production Server**
   - Linux server (Ubuntu 20.04+ or RHEL 8+)
   - Minimum 2GB RAM, 2 CPU cores
   - Python 3.8 or higher

3. **Reverse Proxy**
   - Nginx or Apache for SSL termination
   - Load balancing for high availability

### Setup Steps

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv -y

# Create application user
sudo useradd -r -s /bin/false dpp

# Create application directory
sudo mkdir -p /opt/okta-dpp
sudo chown dpp:dpp /opt/okta-dpp
```

#### 2. Application Deployment

```bash
# Copy application files
sudo cp -r . /opt/okta-dpp/
cd /opt/okta-dpp

# Create virtual environment
sudo -u dpp python3 -m venv venv

# Install dependencies
sudo -u dpp venv/bin/pip install -r requirements.txt

# Copy production certificates
sudo cp /path/to/prod/cert.crt certs/saml.crt
sudo cp /path/to/prod/cert.key certs/saml.key
sudo chown dpp:dpp certs/*
sudo chmod 600 certs/saml.key
```

#### 3. Configure Systemd Service

Create `/etc/systemd/system/okta-dpp.service`:

```ini
[Unit]
Description=Okta Device Posture Provider
After=network.target

[Service]
Type=simple
User=dpp
Group=dpp
WorkingDirectory=/opt/okta-dpp
Environment="PATH=/opt/okta-dpp/venv/bin"
ExecStart=/opt/okta-dpp/venv/bin/python app.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/okta-dpp

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable okta-dpp
sudo systemctl start okta-dpp
sudo systemctl status okta-dpp
```

#### 4. Nginx Reverse Proxy

Create `/etc/nginx/sites-available/okta-dpp`:

```nginx
upstream dpp_backend {
    server 127.0.0.1:8443;
    keepalive 64;
}

server {
    listen 80;
    server_name dpp.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dpp.example.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/dpp.example.com.crt;
    ssl_certificate_key /etc/ssl/private/dpp.example.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/dpp_access.log;
    error_log /var/log/nginx/dpp_error.log;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=dpp_limit:10m rate=10r/s;
    limit_req zone=dpp_limit burst=20 nodelay;

    location / {
        proxy_pass http://dpp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    # Health check endpoint (no auth)
    location /health {
        proxy_pass http://dpp_backend/health;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/okta-dpp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Monitoring and Logging

**Centralized Logging:**
```bash
# Configure rsyslog
sudo tee /etc/rsyslog.d/30-okta-dpp.conf <<EOF
if $programname == 'okta-dpp' then /var/log/okta-dpp/app.log
& stop
EOF

sudo systemctl restart rsyslog
```

**Log Rotation:**
```bash
sudo tee /etc/logrotate.d/okta-dpp <<EOF
/var/log/okta-dpp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 dpp dpp
    sharedscripts
    postrotate
        systemctl reload okta-dpp > /dev/null 2>&1 || true
    endscript
}
EOF
```

---

## Cloud Deployment

### AWS Deployment

#### Using EC2

```bash
# Launch EC2 instance (Amazon Linux 2)
aws ec2 run-instances \
  --image-id ami-xxxxxxxxx \
  --instance-type t3.medium \
  --key-name your-key \
  --security-groups dpp-sg

# Install application (follow Production Deployment steps)
```

#### Using ECS/Fargate

**Task Definition:**
```json
{
  "family": "okta-dpp",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "dpp",
      "image": "your-registry/okta-dpp:latest",
      "portMappings": [
        {
          "containerPort": 8443,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DPP_PORT",
          "value": "8443"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/okta-dpp",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "dpp"
        }
      }
    }
  ]
}
```

### Azure Deployment

#### Using Azure Container Instances

```bash
az container create \
  --resource-group okta-dpp-rg \
  --name okta-dpp \
  --image your-registry/okta-dpp:latest \
  --ports 8443 \
  --dns-name-label okta-dpp \
  --location eastus
```

### Google Cloud Platform

#### Using Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/okta-dpp

# Deploy to Cloud Run
gcloud run deploy okta-dpp \
  --image gcr.io/PROJECT_ID/okta-dpp \
  --platform managed \
  --port 8443 \
  --allow-unauthenticated
```

---

## Kubernetes

### Deployment Manifest

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: okta-dpp
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: okta-dpp
  template:
    metadata:
      labels:
        app: okta-dpp
    spec:
      containers:
      - name: dpp
        image: okta-dpp:latest
        ports:
        - containerPort: 8443
        env:
        - name: DPP_PORT
          value: "8443"
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
        - name: certs
          mountPath: /app/certs
        livenessProbe:
          httpGet:
            path: /health
            port: 8443
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8443
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: dpp-config
      - name: certs
        secret:
          secretName: dpp-certs
```

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: okta-dpp
  namespace: default
spec:
  type: LoadBalancer
  selector:
    app: okta-dpp
  ports:
  - protocol: TCP
    port: 443
    targetPort: 8443
```

**ingress.yaml:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: okta-dpp
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - dpp.example.com
    secretName: dpp-tls
  rules:
  - host: dpp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: okta-dpp
            port:
              number: 443
```

### Deploy to Kubernetes

```bash
# Create ConfigMap
kubectl create configmap dpp-config --from-file=config.yaml

# Create Secret for certificates
kubectl create secret generic dpp-certs \
  --from-file=saml.crt=certs/saml.crt \
  --from-file=saml.key=certs/saml.key

# Deploy application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check status
kubectl get pods
kubectl get services
kubectl get ingress
```

---

## High Availability Setup

### Load Balancing

**HAProxy Configuration:**
```
frontend dpp_frontend
    bind *:443 ssl crt /etc/ssl/certs/dpp.pem
    mode http
    default_backend dpp_backend

backend dpp_backend
    mode http
    balance roundrobin
    option httpchk GET /health
    server dpp1 10.0.1.10:8443 check
    server dpp2 10.0.1.11:8443 check
    server dpp3 10.0.1.12:8443 check
```

### Database Replication

For production with database:
- Use PostgreSQL with primary-replica setup
- Configure connection pooling (pgBouncer)
- Enable automatic failover

### Monitoring

**Prometheus Configuration:**
```yaml
scrape_configs:
  - job_name: 'okta-dpp'
    static_configs:
      - targets: ['dpp.example.com:8443']
    metrics_path: '/metrics'
    scheme: https
```

---

## Security Checklist

- [ ] Use valid SSL/TLS certificates
- [ ] Enable HTTPS only (disable HTTP)
- [ ] Implement rate limiting
- [ ] Add authentication for admin endpoints
- [ ] Enable request logging
- [ ] Set up monitoring and alerts
- [ ] Regular security updates
- [ ] Firewall configuration
- [ ] Secure certificate storage
- [ ] Network segmentation

---

## Troubleshooting

### Check Logs
```bash
# Systemd service
sudo journalctl -u okta-dpp -f

# Docker
docker logs -f okta-dpp

# Kubernetes
kubectl logs -f deployment/okta-dpp
```

### Test Connectivity
```bash
# Health check
curl http://localhost:8443/health

# Test from external
curl https://dpp.example.com/health
```

### Debug Mode
```bash
# Enable debug in config.yaml
server:
  debug: true

# Restart service
sudo systemctl restart okta-dpp
```

---

## Backup and Recovery

### Backup
```bash
# Configuration
tar -czf dpp-backup-$(date +%Y%m%d).tar.gz \
  config.yaml \
  certs/ \
  device_registry.db

# Database (if using PostgreSQL)
pg_dump -U dpp dpp > dpp-backup-$(date +%Y%m%d).sql
```

### Recovery
```bash
# Restore files
tar -xzf dpp-backup-YYYYMMDD.tar.gz -C /opt/okta-dpp/

# Restore database
psql -U dpp dpp < dpp-backup-YYYYMMDD.sql
```

---

For additional support, refer to the main README.md
