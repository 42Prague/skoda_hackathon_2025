#!/bin/bash

# S³ (Škoda Smart Stream) - Server Setup Script
# Run this script on your Ubuntu server to set up the application

set -e

echo "🚀 Setting up S³ (Škoda Smart Stream) on Ubuntu Server"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root for certain commands
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Please don't run this script as root. It will ask for sudo when needed."
   exit 1
fi

# Step 1: Install system dependencies
echo -e "\n${YELLOW}Step 1: Installing system dependencies...${NC}"
sudo apt update

# Check Node.js version
NODE_VERSION=0
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    echo "Node.js $(node -v) is already installed"
fi

# Install Node.js 20+ if not already installed or if version is too old
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "Installing Node.js 20 (required for Next.js 16)..."
    # Remove conflicting npm package if it exists
    sudo apt remove -y npm 2>/dev/null || true
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    # Verify npm is available (comes bundled with nodejs from NodeSource)
    if ! command -v npm &> /dev/null; then
        echo "⚠️  npm not found, installing separately..."
        sudo apt install -y npm
    fi
else
    echo "Node.js version is sufficient (18+)"
    # Ensure npm is available
    if ! command -v npm &> /dev/null; then
        echo "Installing npm..."
        sudo apt install -y npm
    fi
fi

# Install other dependencies
sudo apt install -y python3 python3-pip python3-venv git

# Install PM2 globally
if ! command -v pm2 &> /dev/null; then
    echo "Installing PM2..."
    sudo npm install -g pm2
fi

# Install Apache modules
echo "Enabling Apache modules..."
sudo a2enmod proxy proxy_http rewrite headers
sudo systemctl restart apache2

# Step 2: Clone repository (if not already cloned)
if [ ! -d "web" ]; then
    echo -e "\n${YELLOW}Step 2: Cloning repository...${NC}"
    if [ -d ".git" ]; then
        echo "Repository already exists, pulling latest changes..."
        git pull
    else
        echo "Please clone the repository first:"
        echo "  git clone https://github.com/ExceptedPrism3/Skoda.git"
        echo "  cd Skoda"
        exit 1
    fi
else
    echo -e "\n${YELLOW}Step 2: Repository already cloned${NC}"
fi

# Step 3: Set up Python environment
echo -e "\n${YELLOW}Step 3: Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip

# Install all required Python dependencies
echo "Installing Python dependencies..."
pip install pandas transformers scikit-learn numpy scipy openpyxl sentencepiece pydantic

# Note: torch is optional but recommended for better translation performance
# Uncomment the line below if you want to install PyTorch (large download ~2GB)
# pip install torch

# Step 4: Process data (if data folder exists)
if [ -d "data" ] && [ "$(ls -A data 2>/dev/null)" ]; then
    echo -e "\n${YELLOW}Step 4: Processing data...${NC}"
    # Add src to PYTHONPATH so Python can find the s3 module
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
    python -m s3.ingest
    echo -e "${GREEN}✓ Data processed successfully${NC}"
else
    echo -e "\n${YELLOW}Step 4: Skipping data processing (data folder not found or empty)${NC}"
    echo "⚠️  Make sure to place your data files in the data/ folder and run:"
    echo "   source venv/bin/activate"
    echo "   export PYTHONPATH=\${PYTHONPATH}:\$(pwd)/src"
    echo "   python -m s3.ingest"
fi

# Step 5: Set up Next.js application
echo -e "\n${YELLOW}Step 5: Setting up Next.js application...${NC}"
cd web
npm install
cd ..

# Step 6: Build Next.js application
echo -e "\n${YELLOW}Step 6: Building Next.js application...${NC}"
cd web
NEXT_PUBLIC_BASE_PATH=/skoda npm run build
cd ..

# Step 7: Create PM2 ecosystem file
echo -e "\n${YELLOW}Step 7: Creating PM2 configuration...${NC}"
mkdir -p logs
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'skoda-web',
    script: 'npm',
    args: 'start',
    cwd: process.cwd() + '/web',
    env: {
      NODE_ENV: 'production',
      PORT: 3002,
      NEXT_PUBLIC_BASE_PATH: '/skoda'
    },
    error_file: process.cwd() + '/logs/pm2-error.log',
    out_file: process.cwd() + '/logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    autorestart: true,
    max_memory_restart: '1G'
  }]
};
EOF

# Step 8: Configure Apache
echo -e "\n${YELLOW}Step 8: Configuring Apache...${NC}"

# Check if SSL VirtualHost exists
SSL_CONF=$(sudo grep -l "VirtualHost.*443" /etc/apache2/sites-enabled/*.conf 2>/dev/null | head -1)

if [ ! -z "$SSL_CONF" ]; then
    echo "Found existing SSL VirtualHost: $SSL_CONF"
    echo "Adding /skoda location blocks to existing SSL configuration..."
    
    # Check if already configured
    if ! sudo grep -q "Location /skoda" "$SSL_CONF"; then
        # Create backup
        BACKUP_FILE="${SSL_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
        sudo cp "$SSL_CONF" "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        
        # Add location blocks before closing VirtualHost tag
        sudo sed -i '/<\/VirtualHost>/i\
    # Proxy to Skoda Next.js application\
    ProxyPreserveHost On\
    ProxyRequests Off\
\
    <Location /skoda>\
        ProxyPass http://localhost:3002/skoda\
        ProxyPassReverse http://localhost:3002/skoda\
        RequestHeader set X-Forwarded-Proto "https"\
        RequestHeader set X-Forwarded-Prefix "/skoda"\
    </Location>\
\
    <Location /skoda/_next>\
        ProxyPass http://localhost:3002/skoda/_next\
        ProxyPassReverse http://localhost:3002/skoda/_next\
    </Location>\
' "$SSL_CONF"
        echo "✓ Added /skoda configuration to SSL VirtualHost"
    else
        echo "✓ /skoda location already configured in SSL VirtualHost"
    fi
else
    echo "No SSL VirtualHost found, creating HTTP-only configuration..."
    sudo tee /etc/apache2/sites-available/skoda.conf > /dev/null << EOF
<VirtualHost *:80>
    ServerName 89.168.52.201
    
    ProxyPreserveHost On
    ProxyRequests Off
    
    <Location /skoda>
        ProxyPass http://localhost:3002/skoda
        ProxyPassReverse http://localhost:3002/skoda
        RequestHeader set X-Forwarded-Proto "http"
        RequestHeader set X-Forwarded-Prefix "/skoda"
    </Location>
    
    <Location /skoda/_next>
        ProxyPass http://localhost:3002/skoda/_next
        ProxyPassReverse http://localhost:3002/skoda/_next
    </Location>
    
    ErrorLog \${APACHE_LOG_DIR}/skoda_error.log
    CustomLog \${APACHE_LOG_DIR}/skoda_access.log combined
</VirtualHost>
EOF
    sudo a2ensite skoda.conf
fi

# Test Apache configuration
sudo apache2ctl configtest
sudo systemctl reload apache2
echo "✓ Apache configured and reloaded"

# Step 9: Start the application with PM2
echo -e "\n${YELLOW}Step 9: Starting application with PM2...${NC}"
pm2 start ecosystem.config.js
pm2 save

# Setup PM2 to start on boot
echo -e "\n${YELLOW}Setting up PM2 to start on boot...${NC}"
echo "Run the following command that PM2 will output:"
pm2 startup

echo -e "\n${GREEN}=================================================="
echo "✅ Setup complete!"
echo "==================================================${NC}"
echo ""
echo "Your application should now be accessible at:"
echo "  http://89.168.52.201/skoda"
echo ""
echo "Useful commands:"
echo "  pm2 status              - Check application status"
echo "  pm2 logs skoda-web      - View application logs"
echo "  pm2 restart skoda-web   - Restart the application"
echo "  pm2 stop skoda-web      - Stop the application"
echo ""
echo "Apache logs:"
echo "  sudo tail -f /var/log/apache2/skoda_error.log"
echo "  sudo tail -f /var/log/apache2/skoda_access.log"
echo ""

