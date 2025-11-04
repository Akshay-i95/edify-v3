#!/bin/bash
# ===========================================
# EDIFY AI V2 - PRODUCTION DEPLOYMENT SETUP
# ===========================================
# This script sets up environment for production deployment

echo "🚀 Setting up Edify AI V2 Production Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_info "Project root directory detected: $(pwd)"

# Get deployment configuration
echo -e "\n${BLUE}🔧 Production Configuration${NC}"

read -p "Enter your domain name (e.g., your-domain.com): " DOMAIN_NAME
if [ -z "$DOMAIN_NAME" ]; then
    print_error "Domain name is required"
    exit 1
fi

read -p "Enter backend port (default: 5000): " BACKEND_PORT
BACKEND_PORT=${BACKEND_PORT:-5000}

read -p "Enter frontend port (default: 3000): " FRONTEND_PORT
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# Setup Backend Production Environment
echo -e "\n${BLUE}📦 Setting up Backend Production Environment...${NC}"

cd backend

# Create production .env file
cat > .env.production << EOF
# ===========================================
# EDIFY AI V2 - PRODUCTION CONFIGURATION
# ===========================================

# ===========================================
# FLASK CONFIGURATION
# ===========================================
FLASK_SECRET_KEY=$(openssl rand -base64 32)
FLASK_PORT=${BACKEND_PORT}
FLASK_DEBUG=false
FLASK_ENV=production

# ===========================================
# VECTOR DATABASE CONFIGURATION
# ===========================================
VECTOR_DB_TYPE=pinecone
VECTOR_DB_PATH=./vector_store_pinecone
COLLECTION_NAME=pdf_chunks
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Vector search configuration
MAX_CONTEXT_CHUNKS=8
MIN_SIMILARITY_THRESHOLD=0.35
ENABLE_CITATIONS=true
ENABLE_CONTEXT_EXPANSION=true
MAX_CONTEXT_LENGTH=6000

# ===========================================
# PINECONE CONFIGURATION
# ===========================================
# TODO: Set your actual Pinecone API key
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=chatbot-chunks

# ===========================================
# AZURE STORAGE CONFIGURATION
# ===========================================
# TODO: Set your actual Azure credentials
AZURE_STORAGE_CONNECTION_STRING=your-azure-connection-string-here
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account-name
AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key
AZURE_STORAGE_CONTAINER_NAME=your-container-name
AZURE_BLOB_FOLDER_PATH=documents/

# ===========================================
# LLM SERVICE CONFIGURATION
# ===========================================
# TODO: Set your actual API keys
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama3-8b-8192

# ===========================================
# CORS CONFIGURATION
# ===========================================
ALLOWED_ORIGINS=https://${DOMAIN_NAME},https://www.${DOMAIN_NAME}

# ===========================================
# LOGGING CONFIGURATION
# ===========================================
LOG_LEVEL=INFO
LOG_FILE=backend.log
ENABLE_FILE_LOGGING=true
ENABLE_CONSOLE_LOGGING=true

# ===========================================
# PERFORMANCE CONFIGURATION
# ===========================================
MAX_CONVERSATION_HISTORY=20
MAX_CONTEXT_COMPRESSION_LENGTH=30
ENABLE_REASONING=true
ENABLE_VIDEO_SOURCES=true
ENABLE_SOURCE_CITATIONS=true

# ===========================================
# SECURITY CONFIGURATION
# ===========================================
RATE_LIMIT_PER_MINUTE=60

# ===========================================
# PRODUCTION CONFIGURATION
# ===========================================
DEBUG_MODE=false
DEBUG_VECTOR_DB=false
DEBUG_LLM_RESPONSES=false
EOF

print_status "Created backend production environment file"

# Create systemd service file for backend
cat > edify-backend.service << EOF
[Unit]
Description=Edify AI V2 Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
EnvironmentFile=$(pwd)/.env.production
ExecStart=$(pwd)/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_status "Created systemd service file for backend"

cd ..

# Setup Frontend Production Environment
echo -e "\n${BLUE}🌐 Setting up Frontend Production Environment...${NC}"

cd frontend/chatbot

# Create production .env file
cat > .env.production << EOF
# ===========================================
# EDIFY AI V2 - FRONTEND PRODUCTION CONFIG
# ===========================================

# ===========================================
# BACKEND API CONFIGURATION
# ===========================================
NEXT_PUBLIC_BACKEND_URL=https://${DOMAIN_NAME}:${BACKEND_PORT}
BACKEND_URL=https://${DOMAIN_NAME}:${BACKEND_PORT}

# ===========================================
# APPLICATION CONFIGURATION
# ===========================================
NEXT_PUBLIC_APP_ENV=production
NODE_ENV=production
NEXT_PUBLIC_APP_NAME=Edify AI Assistant
NEXT_PUBLIC_APP_VERSION=2.0.0

# ===========================================
# FRONTEND FEATURES CONFIGURATION
# ===========================================
NEXT_PUBLIC_ENABLE_REASONING=true
NEXT_PUBLIC_ENABLE_SOURCES=true
NEXT_PUBLIC_ENABLE_VIDEOS=true
NEXT_PUBLIC_ENABLE_MOBILE_API=true
NEXT_PUBLIC_DEFAULT_ROLE=user

# ===========================================
# UI/UX CONFIGURATION
# ===========================================
NEXT_PUBLIC_DEFAULT_NAMESPACES=kb-psp,kb-msp
NEXT_PUBLIC_SHOW_NAMESPACE_SELECTOR=true
NEXT_PUBLIC_SHOW_ROLE_SELECTOR=false
NEXT_PUBLIC_ENABLE_STREAMING=true
NEXT_PUBLIC_STREAM_DELAY_MS=20

# ===========================================
# PRODUCTION CONFIGURATION
# ===========================================
NEXT_PUBLIC_DEV_MODE=false
NEXT_PUBLIC_DEBUG_LOGGING=false
NEXT_PUBLIC_SHOW_DETAILED_ERRORS=false
NEXT_PUBLIC_API_TIMEOUT=30000
EOF

print_status "Created frontend production environment file"

# Create systemd service file for frontend
cat > edify-frontend.service << EOF
[Unit]
Description=Edify AI V2 Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$(pwd)
EnvironmentFile=$(pwd)/.env.production
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_status "Created systemd service file for frontend"

cd ../..

# Create nginx configuration
echo -e "\n${BLUE}🌐 Creating Nginx Configuration...${NC}"

cat > nginx-edify-ai.conf << EOF
# Nginx configuration for Edify AI V2
server {
    listen 80;
    server_name ${DOMAIN_NAME} www.${DOMAIN_NAME};
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN_NAME} www.${DOMAIN_NAME};
    
    # SSL Configuration (you'll need to set up SSL certificates)
    # ssl_certificate /path/to/your/certificate.pem;
    # ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:${BACKEND_PORT}/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # CORS headers for API
        add_header Access-Control-Allow-Origin "https://${DOMAIN_NAME}" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "https://${DOMAIN_NAME}";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain charset=UTF-8';
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

print_status "Created Nginx configuration file"

# Create deployment script
cat > deploy.sh << 'EOF'
#!/bin/bash
# Production deployment script

echo "🚀 Deploying Edify AI V2 to Production..."

# Build frontend
echo "🏗️ Building frontend..."
cd frontend/chatbot
npm run build:prod
echo "✅ Frontend built successfully"

# Install systemd services
echo "📦 Installing systemd services..."
sudo cp ../../backend/edify-backend.service /etc/systemd/system/
sudo cp edify-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable edify-backend
sudo systemctl enable edify-frontend
sudo systemctl start edify-backend
sudo systemctl start edify-frontend

echo "✅ Services installed and started"

# Install nginx configuration
echo "🌐 Installing Nginx configuration..."
sudo cp ../../nginx-edify-ai.conf /etc/nginx/sites-available/edify-ai
sudo ln -sf /etc/nginx/sites-available/edify-ai /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Nginx configured and reloaded"

echo "🎉 Deployment complete!"
echo "Your application should be available at: https://$(grep server_name ../../nginx-edify-ai.conf | awk '{print $2}' | head -1 | sed 's/;//g')"
EOF

chmod +x deploy.sh
print_status "Created deployment script"

# Final instructions
echo -e "\n${GREEN}🎉 Production environment setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Edit backend/.env.production with your actual API keys"
echo "2. Edit frontend/chatbot/.env.production if needed"
echo "3. Set up SSL certificates for your domain"
echo "4. Run './deploy.sh' to deploy to production"
echo ""
echo -e "${BLUE}Files created:${NC}"
echo "- backend/.env.production"
echo "- frontend/chatbot/.env.production"
echo "- backend/edify-backend.service"
echo "- frontend/chatbot/edify-frontend.service"
echo "- nginx-edify-ai.conf"
echo "- deploy.sh"
echo ""
print_warning "Don't forget to:"
print_warning "- Configure your actual API keys in .env.production files"
print_warning "- Set up SSL certificates for HTTPS"
print_warning "- Configure your firewall to allow ports 80 and 443"