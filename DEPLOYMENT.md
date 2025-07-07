# EcoDish365 Production Deployment Guide for ecodish365.com

## Prerequisites

- AWS EC2 instance (Ubuntu 20.04+) at **13.49.5.171**
- Domain **ecodish365.com** pointed to your Elastic IP
- RSA key pair `ecodish365.pem` (located in `backend/` directory)

## Step 1: SSH into AWS Server

```bash
# Navigate to backend directory where the key is located
cd backend

# Set proper permissions for the SSH key
chmod 400 ecodish365.pem

# SSH into your AWS instance
ssh -i ecodish365.pem ubuntu@13.49.5.171
```

## Step 2: Clone Repository and Setup

```bash
# On your AWS server
sudo mkdir -p /var/www/ecodish365
sudo chown $USER:$USER /var/www/ecodish365
cd /var/www/ecodish365

# Clone the repository
git clone https://github.com/Amankrah/ecodish365 .

# The deployment script will create a basic production environment
# No manual environment configuration needed for this public project
```

## Step 3: Run Automated Deployment

```bash
cd backend
chmod +x deploy.sh
./deploy.sh
```

The deployment script will automatically:
- Install system dependencies (Python, Node.js, Nginx, SQLite, etc.)
- Setup Python virtual environment and install packages
- Configure SQLite database with proper permissions
- Build and deploy Next.js frontend
- Setup Nginx with SSL certificates (Let's Encrypt)
- Configure Supervisor for process management
- Setup automated daily database backups
- Configure firewall (UFW)
- Start all services

## Step 4: Post-Deployment Security

**After deployment completes, optionally:**

1. **Change the default admin password (if you plan to use Django admin):**
   ```bash
   cd /var/www/ecodish365/backend
   source venv/bin/activate
   python manage.py changepassword admin
   ```

2. **Restart services to apply changes:**
   ```bash
   sudo supervisorctl restart all
   ```

## Step 5: Verify Deployment

```bash
# Test HTTPS connection
curl -I https://ecodish365.com

# Check service status
sudo supervisorctl status

# View logs if needed
sudo tail -f /var/log/ecodish365-django.log
sudo tail -f /var/log/ecodish365-frontend.log
```

**Your EcoDish365 application should now be live at:** `https://ecodish365.com`

---

## Production Architecture

```
Internet → Nginx (443/80) → Django (8000) + Next.js (3000)
                         ↓
                   SQLite Database
```

## Service Management Commands

```bash
# Check all services
sudo supervisorctl status

# Restart individual services
sudo supervisorctl restart ecodish365-django
sudo supervisorctl restart ecodish365-frontend

# Reload Nginx
sudo systemctl reload nginx

# View real-time logs
sudo tail -f /var/log/ecodish365-django.log
sudo tail -f /var/log/ecodish365-frontend.log
```

## Database Backup

- **Automatic:** Daily backups at 2:00 AM to `/var/backups/ecodish365/`
- **Manual backup:** `/usr/local/bin/ecodish365-backup.sh`
- **View backups:** `ls -la /var/backups/ecodish365/`

## SSL Certificate Management

Certificates auto-renew via cron job. Manual renewal:
```bash
sudo certbot renew --dry-run
sudo systemctl reload nginx
```

## Security Features Enabled

✅ HTTPS with Let's Encrypt SSL certificates  
✅ Security headers (HSTS, XSS protection, etc.)  
✅ Firewall configured (UFW)  
✅ Proper file permissions for SQLite  
✅ Production-only CORS origins  

## Troubleshooting

**SSL Issues:**
```bash
sudo certbot certificates
sudo certbot renew --force-renewal
```

**Permission Issues:**
```bash
sudo chown -R $USER:www-data /var/www/ecodish365/backend/
sudo chmod 664 /var/www/ecodish365/backend/db.sqlite3
```

**Service Issues:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all
```

**View detailed logs:**
```bash
sudo journalctl -u supervisor -f
sudo nginx -t  # Test nginx configuration
```

---

## API Endpoints

The EcoDish365 API provides public access to:

### CNF (Canadian Nutrient File) API
- **Search Foods:** `GET /api/cnf/search/?q={query}`
- **Food Details:** `GET /api/cnf/foods/{food_id}/`
- **Food Groups:** `GET /api/cnf/food-groups/`
- **Compare Foods:** `POST /api/cnf/compare/`

### HSR (Health Star Rating) API
- **Calculate HSR:** `POST /api/hsr/calculate/`
- **Compare Foods:** `POST /api/hsr/compare/`
- **Food Profile:** `GET /api/hsr/food/{food_id}/`
- **Meal Insights:** `POST /api/hsr/meal-insights/`

### Environmental Impact API
- **Calculate Impact:** `POST /api/environmental-impact/calculate/`

### Example API Test:
```bash
# Test CNF search
curl "https://ecodish365.com/api/cnf/search/?q=apple&limit=5"

# Test HSR calculation
curl -X POST "https://ecodish365.com/api/hsr/calculate/" \
  -H "Content-Type: application/json" \
  -d '{
    "food_ids": [1001, 1002],
    "serving_sizes": [100, 150]
  }'
```

## Future Updates

To deploy updates:
```bash
cd /var/www/ecodish365
git pull origin main

# Update backend
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput

# Update frontend
cd ../frontend
npm ci
npm run build

# Restart services
sudo supervisorctl restart all
sudo systemctl reload nginx
```

## SSL Certificate Setup

```bash
# Initial SSL setup (done by deploy script)
sudo certbot --nginx -d ecodish365.com -d www.ecodish365.com --non-interactive

# Check certificate status
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run
```

## Nginx Configuration

The deployment creates a comprehensive Nginx configuration at `/etc/nginx/sites-available/ecodish365.com` with:

- **SSL termination** for HTTPS
- **Static file serving** for Django and Next.js assets
- **API routing** to Django backend
- **Frontend routing** to Next.js
- **Security headers** for production
- **Gzip compression** for performance

## Monitor Application

```bash
# Check system resources
htop

# Check disk usage
df -h

# Check database size
ls -lh /var/www/ecodish365/backend/db.sqlite3

# Check backup status
ls -la /var/backups/ecodish365/

# Check SSL certificate expiry
sudo certbot certificates
```