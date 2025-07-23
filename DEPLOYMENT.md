# 🚀 Deployment Guide

This guide covers deployment options for your Reroute application with domain setup, cloud hosting, linting, and CI/CD.

## 📋 Prerequisites

- Domain name registered
- Cloud provider account (DigitalOcean, AWS, GCP, Railway, etc.)
- Docker installed locally
- Git repository on GitHub

## 🛠️ Setup

### 1. Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env.production
```

Edit `.env.production` with your actual values:
- Database credentials
- API keys (OpenAI, Strava, GraphHopper)
- Domain configuration
- Deployment settings

### 2. Linting & Formatting

The project is pre-configured with:

**Backend (Python):**
- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)
- pre-commit hooks

**Frontend (TypeScript/React):**
- ESLint (linting)
- Prettier (code formatting)
- TypeScript compiler

Install dev dependencies and setup pre-commit:

```bash
# Backend
cd backend && poetry install

# Frontend
cd frontend && npm install

# Setup pre-commit hooks (from root directory)
pre-commit install
```

### 3. CI/CD Pipeline

GitHub Actions is configured to:
- Run tests and linting on every PR
- Deploy to production on main branch pushes
- Test both backend and frontend

Required GitHub Secrets:
```
DEPLOY_HOST=your-server-ip
DEPLOY_USER=deploy
DEPLOY_KEY=your-ssh-private-key
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret
OPENAI_API_KEY=sk-...
STRAVA_CLIENT_ID=...
STRAVA_CLIENT_SECRET=...
```

## 🌐 Domain Setup

Run the domain setup script:

```bash
chmod +x scripts/setup-domain.sh
./scripts/setup-domain.sh yourdomain.com admin@yourdomain.com
```

This will:
- Update nginx configuration
- Generate SSL certificate with Let's Encrypt
- Create certificate renewal script

## ☁️ Cloud Deployment Options

### Option 1: DigitalOcean Droplet

1. Create a droplet (Ubuntu 20.04+, 2GB+ RAM)
2. Install Docker and Docker Compose on the server
3. Set up deploy user and SSH keys
4. Run deployment:

```bash
chmod +x deploy/deploy.sh deploy/digitalocean.sh
./deploy/deploy.sh digitalocean production
```

### Option 2: Railway (Easiest)

1. Connect your GitHub repository to Railway
2. Deploy with one command:

```bash
chmod +x deploy/railway.sh
./deploy/railway.sh production
```

### Option 3: Vercel (Frontend Only)

For frontend-only deployment:

```bash
chmod +x deploy/vercel.sh
./deploy/vercel.sh production
```

### Option 4: Docker Compose (Self-hosted)

On your server:

```bash
git clone your-repo
cd reroute
cp .env.example .env
# Edit .env with your values
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Manual Server Setup (DigitalOcean)

### 1. Create Droplet

- Choose Ubuntu 20.04 LTS
- Minimum 2GB RAM, 2 vCPUs
- Add your SSH key

### 2. Initial Server Setup

```bash
# Connect to your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create deploy user
adduser deploy
usermod -aG docker deploy
usermod -aG sudo deploy

# Setup project directory
mkdir -p /opt/reroute
chown deploy:deploy /opt/reroute

# Setup nginx
apt install nginx certbot python3-certbot-nginx -y
systemctl enable nginx
```

### 3. DNS Configuration

Point your domain to your server:

```
A record: yourdomain.com -> your-server-ip
A record: www.yourdomain.com -> your-server-ip
```

### 4. Deploy

From your local machine:

```bash
./deploy/deploy.sh digitalocean production
```

## 📊 Monitoring & Maintenance

### Health Checks

The deployment includes health checks for:
- Application (HTTP endpoint)
- Database (PostgreSQL)
- Cache (Redis)

### SSL Certificate Renewal

Certificates auto-renew via the created script. Add to crontab:

```bash
sudo crontab -e
# Add: 0 2 * * 1 /opt/reroute/scripts/renew-ssl.sh
```

### Backup Strategy

Database backups:

```bash
# Create backup
docker-compose exec db pg_dump -U reroute reroute > backup.sql

# Restore backup
docker-compose exec -T db psql -U reroute reroute < backup.sql
```

## 🐛 Troubleshooting

### Common Issues

1. **SSL Certificate Issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

2. **Database Connection**
   ```bash
   docker-compose logs db
   docker-compose exec db psql -U reroute
   ```

3. **Application Logs**
   ```bash
   docker-compose logs app
   ```

4. **Nginx Configuration**
   ```bash
   nginx -t
   systemctl reload nginx
   ```

### Performance Optimization

- Enable Gzip compression (included in nginx.conf)
- Use CDN for static assets
- Configure Redis for caching
- Monitor with tools like New Relic or DataDog

## 🔐 Security Checklist

- [ ] Strong passwords for all services
- [ ] Firewall configured (UFW)
- [ ] SSL certificates installed
- [ ] Regular security updates
- [ ] Database access restricted
- [ ] API rate limiting enabled
- [ ] Environment variables secured

## 📈 Scaling

For high traffic:

1. **Database**: Upgrade to managed PostgreSQL (DigitalOcean Managed Database)
2. **Application**: Use multiple app instances behind load balancer
3. **Cache**: Redis cluster or managed Redis
4. **CDN**: CloudFlare or AWS CloudFront
5. **Monitoring**: Add APM tools

## 💡 Tips

- Use staging environment for testing
- Monitor application logs
- Set up alerts for downtime
- Regular database backups
- Keep dependencies updated
- Use secrets management for production