# Deployment Guide for Ubuntu Server

This guide will help you deploy S³ (Škoda Smart Stream) to your Ubuntu server at `89.168.52.201/skoda` using Apache.

## Prerequisites

- Ubuntu server with Apache installed
- Node.js 18+ and npm
- Python 3.11+ with pip
- Git

## Step 1: Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18+ (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.11+ and pip (if not already installed)
sudo apt install -y python3 python3-pip python3-venv

# Install Git (if not already installed)
sudo apt install -y git

# Install PM2 for process management
sudo npm install -g pm2

# Install Apache modules for reverse proxy
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod rewrite
sudo a2enmod headers
sudo systemctl restart apache2
```

## Step 2: Clone the Repository

```bash
# Navigate to your web root (adjust path as needed)
cd /var/www

# Clone the repository
sudo git clone https://github.com/ExceptedPrism3/Skoda.git skoda
sudo chown -R $USER:$USER skoda
cd skoda
```

## Step 3: Set Up Python Environment and Process Data

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install pandas transformers scikit-learn numpy scipy openpyxl sentencepiece

# Note: torch is optional but recommended for better translation performance
# Uncomment if you want to install PyTorch (large download ~2GB)
# pip install torch

# Run data ingestion (make sure data files are in the data/ folder)
# Add src to PYTHONPATH so Python can find the s3 module
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python -m s3.ingest

# This will generate:
# - web/src/data/users.json
# - web/src/data/courses.json
# - web/src/data/job_descriptions.json
# - web/src/data/course_content.json
```

## Step 4: Build and Set Up Next.js Application

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install

# Build the application for production
NEXT_PUBLIC_BASE_PATH=/skoda npm run build

# The build output will be in the .next/ directory
```

## Step 5: Configure Apache

Create an Apache configuration file for the Skoda application:

```bash
sudo nano /etc/apache2/sites-available/skoda.conf
```

Add the following configuration:

```apache
<VirtualHost *:80>
    ServerName 89.168.52.201
    
    # Proxy to Next.js application
    ProxyPreserveHost On
    ProxyRequests Off
    
    # Main application
    <Location /skoda>
        ProxyPass http://localhost:3002/skoda
        ProxyPassReverse http://localhost:3002/skoda
        ProxyPassReverse /
        
        # Headers for proper routing
        RequestHeader set X-Forwarded-Proto "http"
        RequestHeader set X-Forwarded-Prefix "/skoda"
    </Location>
    
    # Static assets
    <Location /skoda/_next>
        ProxyPass http://localhost:3002/skoda/_next
        ProxyPassReverse http://localhost:3002/skoda/_next
    </Location>
    
    # Error and access logs (optional)
    ErrorLog ${APACHE_LOG_DIR}/skoda_error.log
    CustomLog ${APACHE_LOG_DIR}/skoda_access.log combined
</VirtualHost>
```

**Note:** If you already have a VirtualHost for `89.168.52.201`, you can add the Location blocks to your existing configuration instead.

Enable the site and restart Apache:

```bash
sudo a2ensite skoda.conf
sudo systemctl reload apache2
```

## Step 6: Start the Next.js Application with PM2

```bash
# Navigate to the web directory
cd /var/www/skoda/web

# Create a PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'skoda-web',
    script: 'npm',
    args: 'start',
    cwd: '/var/www/skoda/web',
    env: {
      NODE_ENV: 'production',
      PORT: 3002,
      NEXT_PUBLIC_BASE_PATH: '/skoda'
    },
    error_file: '/var/www/skoda/logs/pm2-error.log',
    out_file: '/var/www/skoda/logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    autorestart: true,
    max_memory_restart: '1G'
  }]
};
EOF

# Create logs directory
mkdir -p /var/www/skoda/logs

# Start the application
pm2 start ecosystem.config.js

# Save PM2 configuration to start on boot
pm2 save
pm2 startup
```

## Step 7: Verify Deployment

1. Check if the Next.js app is running:
   ```bash
   pm2 status
   pm2 logs skoda-web
   ```

2. Check Apache configuration:
   ```bash
   sudo apache2ctl configtest
   ```

3. Test the application:
   - Open `http://89.168.52.201/skoda` in your browser
   - You should see the login page

## Troubleshooting

### If the app doesn't load:

1. **Check PM2 logs:**
   ```bash
   pm2 logs skoda-web
   ```

2. **Check Apache logs:**
   ```bash
   sudo tail -f /var/log/apache2/skoda_error.log
   sudo tail -f /var/log/apache2/skoda_access.log
   ```

3. **Verify Next.js is running:**
   ```bash
   curl http://localhost:3002/skoda
   ```

4. **Check if port 3002 is accessible:**
   ```bash
   netstat -tlnp | grep 3002
   ```

### If you need to rebuild:

```bash
cd /var/www/skoda/web
NEXT_PUBLIC_BASE_PATH=/skoda npm run build
pm2 restart skoda-web
```

### If you need to update the code:

```bash
cd /var/www/skoda
git pull
cd web
npm install
NEXT_PUBLIC_BASE_PATH=/skoda npm run build
pm2 restart skoda-web
```

## Security Considerations

1. **Firewall:** Make sure port 80 (HTTP) is open, but consider closing port 3000 from external access since Apache will proxy to it.

2. **HTTPS:** Consider setting up SSL/TLS with Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-apache
   sudo certbot --apache -d your-domain.com
   ```

3. **Data Files:** Ensure the `data/` folder is not accessible via web (it should already be in .gitignore).

## Maintenance

- **View logs:** `pm2 logs skoda-web`
- **Restart app:** `pm2 restart skoda-web`
- **Stop app:** `pm2 stop skoda-web`
- **Start app:** `pm2 start skoda-web`
- **Monitor:** `pm2 monit`

