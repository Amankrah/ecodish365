#!/bin/bash

# EcoDish365 Production Deployment Script for ecodish365.com
# Run this script on your AWS EC2 instance

set -e  # Exit on any error

echo "🚀 Starting EcoDish365 Production Deployment for ecodish365.com"

# Configuration
PROJECT_DIR="/var/www/ecodish365"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"
DJANGO_PROJECT_DIR="$BACKEND_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to ensure virtual environment is activated
activate_venv() {
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        exit 1
    fi
    
    source $VENV_DIR/bin/activate
    
    if [ "$VIRTUAL_ENV" != "$VENV_DIR" ]; then
        print_error "Failed to activate virtual environment"
        exit 1
    fi
    
    print_status "Virtual environment active: $VIRTUAL_ENV"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# 1. System Dependencies
print_status "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev nginx supervisor certbot python3-certbot-nginx sqlite3 curl

# Install Node.js 18.x for frontend
print_status "Installing Node.js for frontend..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version

# 2. Verify project structure
print_status "Verifying project structure..."

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/backend/requirements.txt" ]; then
    print_error "Project structure not found. Make sure you're in /var/www/ecodish365 and the repository is cloned."
    print_error "Expected file: $PROJECT_DIR/backend/requirements.txt"
    exit 1
fi

print_status "Project structure verified ✓"

# 3. Create project directory permissions
print_status "Setting up project directory permissions..."
sudo chown -R $USER:$USER $PROJECT_DIR

# 4. Setup Python virtual environment
print_status "Creating Python virtual environment..."
cd $BACKEND_DIR

# Remove existing venv if it exists
if [ -d "$VENV_DIR" ]; then
    print_warning "Removing existing virtual environment..."
    rm -rf $VENV_DIR
fi

# Create new virtual environment
python3 -m venv $VENV_DIR

# Verify venv was created
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    print_error "Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
activate_venv

# 5. Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify key packages are installed
python -c "import django; print(f'Django {django.get_version()} installed')"

# 6. Environment configuration
print_status "Setting up environment configuration..."
if [ ! -f "$BACKEND_DIR/.env" ]; then
    print_warning "No .env file found. Creating basic production configuration..."
    cat > $BACKEND_DIR/.env << EOF
DJANGO_ENV=production
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ecodish365.com,www.ecodish365.com,13.49.5.171
EOF
    print_status "Basic .env file created"
fi

# 7. Setup SQLite database directory with proper permissions
print_status "Setting up SQLite database..."
mkdir -p $DJANGO_PROJECT_DIR/data
sudo chown $USER:www-data $DJANGO_PROJECT_DIR/data
sudo chmod 775 $DJANGO_PROJECT_DIR/data

# 8. Django setup
print_status "Running Django migrations and setup..."
cd $DJANGO_PROJECT_DIR

# Ensure virtual environment is still activated
activate_venv

# Clear Django cache and old static files
print_status "Clearing Django cache and static files..."
rm -rf staticfiles
rm -rf __pycache__
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Clear additional Django caches
print_status "Clearing additional Django caches..."
rm -rf media/.cache 2>/dev/null || true
rm -rf .django_cache 2>/dev/null || true
rm -rf tmp 2>/dev/null || true

# Clear any potential database cache files
print_status "Clearing database cache files..."
find . -name "*.db-journal" -delete 2>/dev/null || true
find . -name "*.db-wal" -delete 2>/dev/null || true
find . -name "*.db-shm" -delete 2>/dev/null || true

# Set Django settings module and verify Django can be imported
export DJANGO_SETTINGS_MODULE="dish_project.settings"
python -c "import django; django.setup()" || {
    print_error "Django setup failed - check settings"
    exit 1
}

# Run Django commands
python manage.py collectstatic --noinput --clear
python manage.py migrate

# Set proper permissions for SQLite database
if [ -f "$DJANGO_PROJECT_DIR/db.sqlite3" ]; then
    sudo chown $USER:www-data $DJANGO_PROJECT_DIR/db.sqlite3
    sudo chmod 664 $DJANGO_PROJECT_DIR/db.sqlite3
fi

# 9. Create Django superuser (optional for this public project)
print_status "Creating Django superuser (optional)..."
activate_venv
export DJANGO_SETTINGS_MODULE="dish_project.settings"

python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ecodish365.com', 'change-this-password')
    print("Superuser 'admin' created")
else:
    print("Superuser already exists")
EOF

# 10. Frontend Build and Deployment
print_status "Building and deploying frontend..."
cd $FRONTEND_DIR

# Clear existing cache and builds
print_status "Clearing frontend cache and old builds..."
rm -rf .next
rm -rf node_modules/.cache
rm -rf node_modules/.vite 2>/dev/null || true
rm -rf .cache 2>/dev/null || true
rm -rf dist 2>/dev/null || true
rm -rf build 2>/dev/null || true
rm -rf out 2>/dev/null || true
npm cache clean --force 2>/dev/null || true
# Clear yarn cache if it exists
yarn cache clean 2>/dev/null || true
# Clear any potential browser cache files
rm -rf .turbo 2>/dev/null || true
rm -rf .vercel 2>/dev/null || true

# Create production environment file
if [ ! -f "$FRONTEND_DIR/.env.production" ]; then
    print_status "Creating frontend production environment file..."
    cat > $FRONTEND_DIR/.env.production << EOF
NEXT_PUBLIC_API_URL=https://ecodish365.com
NODE_ENV=production
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_DOMAIN=ecodish365.com
NEXT_PUBLIC_PROTOCOL=https
EOF
fi

# Install frontend dependencies (fresh install)
print_status "Installing frontend dependencies..."
rm -rf node_modules
npm ci

# Build the frontend
print_status "Building frontend for production..."
npm run build

# Clear and recreate directory for built frontend
print_status "Preparing frontend deployment directory..."
sudo rm -rf /var/www/html/ecodish365
sudo mkdir -p /var/www/html/ecodish365
sudo chown $USER:www-data /var/www/html/ecodish365

# Copy built files to web directory
print_status "Deploying frontend files..."
sudo cp -r $FRONTEND_DIR/.next/standalone/* /var/www/html/ecodish365/
sudo cp -r $FRONTEND_DIR/.next/standalone/.next /var/www/html/ecodish365/
sudo cp -r $FRONTEND_DIR/.next/static /var/www/html/ecodish365/.next/
sudo cp -r $FRONTEND_DIR/public /var/www/html/ecodish365/

# Set proper permissions
sudo chown -R $USER:www-data /var/www/html/ecodish365
sudo chmod -R 755 /var/www/html/ecodish365

print_status "Frontend build and deployment completed ✓"

# 11. Nginx configuration
print_status "Configuring Nginx..."

# Create initial HTTP-only configuration for Let's Encrypt
sudo tee /etc/nginx/sites-available/ecodish365.com > /dev/null << EOF
# Upstream definitions
upstream django_backend {
    server 127.0.0.1:8000;
}

upstream frontend_backend {
    server 127.0.0.1:3000;
}

# HTTP server - initial configuration for Let's Encrypt
server {
    listen 80;
    server_name ecodish365.com www.ecodish365.com 13.49.5.171;

    # Allow Let's Encrypt challenges
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Common proxy settings
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_redirect off;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    
    # Next.js static files
    location /_next/static/ {
        alias /var/www/html/ecodish365/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Django static files
    location /static/ {
        alias $DJANGO_PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Django media files
    location /media/ {
        alias $DJANGO_PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Django Admin
    location /admin/ {
        proxy_pass http://django_backend;
    }
    
    # Django API routes
    location /api/ {
        proxy_pass http://django_backend;
    }
    
    # Health check
    location /health/ {
        proxy_pass http://django_backend;
    }
    
    # Frontend - all other routes go to Next.js
    location / {
        proxy_pass http://frontend_backend;
        
        # WebSocket support for Next.js
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Error pages
    error_page 502 503 504 /50x.html;
    location = /50x.html {
        root /var/www/html;
        internal;
    }
}
EOF

# Enable the site and test configuration
sudo ln -sf /etc/nginx/sites-available/ecodish365.com /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
if ! sudo nginx -t; then
    print_error "Nginx configuration test failed"
    exit 1
fi

print_status "Basic Nginx configuration completed ✓"

# Start nginx to serve HTTP for Let's Encrypt
sudo systemctl reload nginx

# 12. SSL Certificate with Let's Encrypt
print_status "Setting up SSL certificate with Let's Encrypt..."

# Get SSL certificate
sudo certbot --nginx -d ecodish365.com -d www.ecodish365.com --non-interactive --agree-tos --email dishdevinfo@gmail.com

# Verify SSL certificate was installed
if [ -f "/etc/letsencrypt/live/ecodish365.com/fullchain.pem" ]; then
    print_status "SSL certificate installed successfully ✓"
    
    # Now update to full HTTPS configuration
    print_status "Updating to full HTTPS configuration..."
    
    sudo tee /etc/nginx/sites-available/ecodish365.com > /dev/null << EOF
# Upstream definitions
upstream django_backend {
    server 127.0.0.1:8000;
}

upstream frontend_backend {
    server 127.0.0.1:3000;
}

# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name ecodish365.com www.ecodish365.com 13.49.5.171;

    # Allow Let's Encrypt challenges
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name ecodish365.com www.ecodish365.com;

    # SSL configuration - managed by certbot
    ssl_certificate /etc/letsencrypt/live/ecodish365.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ecodish365.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Common proxy settings
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_redirect off;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    
    # Next.js static files
    location /_next/static/ {
        alias /var/www/html/ecodish365/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Django static files
    location /static/ {
        alias $DJANGO_PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Django media files
    location /media/ {
        alias $DJANGO_PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Django Admin
    location /admin/ {
        proxy_pass http://django_backend;
    }
    
    # Django API routes
    location /api/ {
        proxy_pass http://django_backend;
    }
    
    # Health check
    location /health/ {
        proxy_pass http://django_backend;
    }
    
    # Frontend - all other routes go to Next.js
    location / {
        proxy_pass http://frontend_backend;
        
        # WebSocket support for Next.js
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Error pages
    error_page 502 503 504 /50x.html;
    location = /50x.html {
        root /var/www/html;
        internal;
    }
}
EOF

    # Test the updated configuration
    sudo nginx -t && sudo systemctl reload nginx
    print_status "HTTPS configuration activated ✓"
    
else
    print_error "SSL certificate installation failed"
    print_warning "Continuing with HTTP-only configuration"
fi

# Create a simple error page
print_status "Creating error page..."
sudo mkdir -p /var/www/html
sudo tee /var/www/html/50x.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>EcoDish365 - Service Temporarily Unavailable</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
        h1 { color: #333; }
        p { color: #666; }
    </style>
</head>
<body>
    <h1>Service Temporarily Unavailable</h1>
    <p>EcoDish365 services are starting up. Please try again in a moment.</p>
    <p>If this problem persists, please contact support.</p>
</body>
</html>
EOF

# 13. Supervisor configuration for services
print_status "Configuring Supervisor for service management..."

# Django/Gunicorn configuration
sudo tee /etc/supervisor/conf.d/ecodish365-django.conf > /dev/null << EOF
[program:ecodish365-django]
command=$VENV_DIR/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 --timeout 300 dish_project.wsgi:application
directory=$DJANGO_PROJECT_DIR
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ecodish365-django.log
environment=DJANGO_ENV="production",DJANGO_SETTINGS_MODULE="dish_project.settings"
EOF

# Next.js frontend configuration
sudo tee /etc/supervisor/conf.d/ecodish365-frontend.conf > /dev/null << EOF
[program:ecodish365-frontend]
command=/usr/bin/node server.js
directory=/var/www/html/ecodish365
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ecodish365-frontend.log
environment=NODE_ENV="production",PORT="3000"
EOF

# 14. Start services
print_status "Starting services..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo systemctl enable nginx supervisor
sudo systemctl start nginx supervisor

# Restart services to ensure configuration changes take effect
print_status "Restarting services to apply configuration changes..."
sudo supervisorctl restart all
sudo systemctl restart nginx

# Clear nginx cache and system caches
print_status "Clearing nginx cache and system caches..."
# Clear nginx cache
sudo systemctl reload nginx
# Clear system caches if they exist
sudo rm -rf /var/cache/nginx/* 2>/dev/null || true
sudo rm -rf /tmp/nginx* 2>/dev/null || true
# Clear any potential system-level caches
sudo sync
echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null 2>&1 || true

# 15. Firewall configuration
print_status "Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# 16. Setup automatic SSL renewal
print_status "Setting up automatic SSL certificate renewal..."
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# 17. Create backup script for SQLite database
print_status "Setting up database backup..."
sudo tee /usr/local/bin/ecodish365-backup.sh > /dev/null << EOF
#!/bin/bash
BACKUP_DIR="/var/backups/ecodish365"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR
sqlite3 $DJANGO_PROJECT_DIR/db.sqlite3 ".backup \$BACKUP_DIR/ecodish365_backup_\$DATE.sqlite3"
# Keep only last 7 days of backups
find \$BACKUP_DIR -name "ecodish365_backup_*.sqlite3" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/ecodish365-backup.sh

# Setup daily backup
echo "0 2 * * * /usr/local/bin/ecodish365-backup.sh" | sudo crontab -

print_status "✅ EcoDish365 Production Deployment Complete!"
print_status "Your EcoDish365 application is now running at https://ecodish365.com"
print_status ""
print_status "Services deployed:"
print_status "- Frontend (Next.js): https://ecodish365.com → port 3000"
print_status "- Backend (Django): https://ecodish365.com/api/, /admin/ → port 8000"
print_status "- API endpoints: https://ecodish365.com/api/cnf/, /api/hsr/, etc."
print_status ""
print_status "🔧 Fixed Issues:"
print_status "- API URL routing (removed double /api/ in paths)"
print_status "- Comprehensive cache clearing (Django, Next.js, Nginx, System)"
print_status ""
print_status "Next steps:"
print_status "1. Update backend/.env with actual production values if needed"
print_status "2. Update frontend/.env.production if needed"
print_status "3. Change default superuser password: python manage.py changepassword admin"
print_status "4. Test the deployment: curl -k https://ecodish365.com"
print_status "5. Monitor logs: sudo tail -f /var/log/ecodish365-*.log"
print_status ""
print_status "Service management commands:"
print_status "- sudo supervisorctl status"
print_status "- sudo supervisorctl restart ecodish365-frontend"
print_status "- sudo supervisorctl restart ecodish365-django"
print_status "- sudo systemctl reload nginx"
print_status ""
print_status "Database backup:"
print_status "- Manual backup: /usr/local/bin/ecodish365-backup.sh"
print_status "- Backups location: /var/backups/ecodish365/" 