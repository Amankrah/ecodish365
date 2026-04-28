# EcoDish365 Production Deployment Guide for ecodish365.com

## Prerequisites

- AWS EC2 instance (Ubuntu 20.04+) at **13.49.5.171**
- Domain **ecodish365.com** pointed to your Elastic IP
- RSA key pair `ecodish365.pem` (located in `backend/` directory)
- **Minimum 2 GB RAM** on the instance (t3.small or larger). The Rust
  toolchain compiles the `rust_core` extension during deploy, and PyO3
  builds can OOM on 1 GB instances. If you must deploy on t3.micro, add a
  swap file (`sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`)
  before running `./deploy.sh`.

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
- Install system dependencies (Python, Node.js, Nginx, SQLite, build tools)
- Install the **Rust toolchain** (rustup, into `$HOME/.cargo`) — required to
  compile the `rust_core` PyO3 extension that backs the HSR / HEFI / FCS /
  HENI scoring engines
- Setup Python virtual environment and install packages
- **Build `rust_core` via `maturin develop --release`** and verify the
  resulting `rust_core.{hsr,hefi,fcs,heni}` modules import cleanly. Adds
  ~1–3 minutes to a fresh deploy depending on instance size.
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
                         ↓               ↓
                   SQLite Database   rust_core (PyO3 native extension,
                                     loaded in-process by Django for
                                     HSR / HEFI / FCS / HENI scoring)
```

The Rust scoring layer ships as a compiled Python extension in the venv's
`site-packages` (`rust_core.{hsr,hefi,fcs,heni}`). Django imports it like
any other module; there's no separate Rust process to manage.

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

**rust_core build / import issues:**

If Django logs show `ImportError: rust_core.hefi is not available` or similar,
the native extension didn't build or wasn't installed into the active venv.
```bash
# Confirm Rust toolchain is on PATH
source "$HOME/.cargo/env"
rustc --version

# Rebuild the extension
cd /var/www/ecodish365/backend
source venv/bin/activate
cd rust_core
maturin develop --release

# Verify the module loads
cd ..
python -c "from rust_core import hsr, hefi, fcs, heni; print('OK')"

# Restart Django so the new .so is picked up
sudo supervisorctl restart ecodish365-django
```

If `maturin develop` is killed with `signal: 9` or hangs at "Compiling pyo3",
the instance ran out of memory during the compile. Add swap (see Prerequisites)
and retry.

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
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Rebuild rust_core ONLY if backend/rust_core/ changed in this pull.
# Cheap to skip when unchanged; required to pick up Rust changes.
if git diff --name-only HEAD@{1} HEAD | grep -q '^backend/rust_core/'; then
    source "$HOME/.cargo/env"
    cd rust_core
    maturin develop --release
    cd ..
fi

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


sudo certbot --nginx -d ecodish365.com -d www.ecodish365.com --non-interactive

sudo ss -tlnp | grep nginx

sudo cat /etc/nginx/sites-available/ecodish365.com


git fetch origin && git restore --worktree --staged backend/deploy.sh && git pull origin main --ff-only"