# 🚀 Edify AI Assistant - Production Deployment Guide

## Server Details
- **Domain**: edify-ai-assistant.i95-dev.com
- **IP**: 45.79.124.136
- **Username**: i95devteam
- **Password**: Plm@321Qazi95dev

## Technologies Used
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Assistant UI
- **Backend**: Python Flask, Vector Database (FAISS/Pinecone), Azure Blob Storage
- **Deployment**: Nginx, PM2, Node.js, Python

---

## 🔧 Pre-Deployment Setup (Local)

### 1. Update Environment Files
Before deploying, update these files with your actual credentials:

**Backend** (`backend/.env.production`):
```bash
# Update these with your actual values:
AZURE_STORAGE_CONNECTION_STRING=your_actual_connection_string
AZURE_STORAGE_ACCOUNT_NAME=your_actual_account_name
AZURE_STORAGE_ACCOUNT_KEY=your_actual_account_key
EDIFY_API_KEY=your_actual_api_key
FLASK_SECRET_KEY=change-this-to-a-secure-random-string
```

### 2. Build Frontend for Production (Local)
```bash
cd frontend/chatbot
npm install
npm run build
```

---

## 📦 Server Deployment Steps

### Step 1: Connect to Server
```bash
ssh i95devteam@45.79.124.136
# Password: Plm@321Qazi95dev
```

### Step 2: Install Required Software
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and development tools
sudo apt install python3 python3-pip python3-venv python3-dev build-essential -y

# Install Nginx
sudo apt install nginx -y

# Install PM2 globally
sudo npm install -g pm2

# Install Git (if needed)
sudo apt install git -y
```

### Step 3: Create Project Directory
```bash
sudo mkdir -p /home/i95devteam
sudo chown i95devteam:i95devteam /home/i95devteam
cd /home/i95devteam
```

### Step 4: Transfer Files
**Using SCP from your local machine:**
```bash
scp -r your-local-project-path/* i95devteam@45.79.124.136:/home/i95devteam/
```

**Or using WinSCP:**
1. Connect to `45.79.124.136:22` with `i95devteam:Plm@321Qazi95dev`
2. Upload entire project folder to `/home/i95devteam/`
3. Ensure all files are transferred correctly

### Step 5: Run Deployment Script
```bash
cd /home/i95devteam
chmod +x deploy-server.sh
./deploy-server.sh
```

This script will:
- Set up backend Python virtual environment
- Install all dependencies
- Configure environment files
- Build the frontend
- Configure Nginx
- Start services with PM2
- Configure firewall

### Step 6: Configure Environment Variables
```bash
# Edit backend environment variables
nano /home/i95devteam/backend/.env

# Update these important settings:
# - AZURE_STORAGE_CONNECTION_STRING
# - AZURE_STORAGE_ACCOUNT_NAME
# - AZURE_STORAGE_ACCOUNT_KEY
# - EDIFY_API_KEY
# - FLASK_SECRET_KEY
```

### Step 7: Configure DNS (IMPORTANT)
Configure your DNS provider to point the domain to your server:

**DNS Settings:**
- Type: A Record
- Name: edify-ai-assistant.i95-dev.com
- Value: 45.79.124.136
- TTL: 300 (or default)

Wait 5-15 minutes for DNS propagation.

### Step 8: Verify Deployment
```bash
# Check PM2 services
pm2 status

# Check Nginx
sudo systemctl status nginx

# Check if ports are listening
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :3000
sudo netstat -tlnp | grep :5000

# Test the application
curl http://localhost/api/health
```

### Step 9: Setup SSL (Optional but Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d edify-ai-assistant.i95-dev.com

# Test automatic renewal
sudo certbot renew --dry-run
```

---

## 🔍 Service Management Commands

### Check Service Status
```bash
# Check PM2 services
pm2 status
pm2 logs

# Check Nginx
sudo systemctl status nginx

# Check ports
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :5000
```

### Restart Services
```bash
# Restart all PM2 services
pm2 restart all

# Restart specific service
pm2 restart edify-backend
pm2 restart edify-frontend

# Restart Nginx
sudo systemctl restart nginx
```

### View Logs
```bash
# PM2 logs
pm2 logs edify-backend
pm2 logs edify-frontend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 🌐 Access Your Application

- **Main Application**: http://edify-ai-assistant.i95-dev.com
- **Backend API**: http://edify-ai-assistant.i95-dev.com/api
- **Health Check**: http://edify-ai-assistant.i95-dev.com/api/health

---

## 🔧 Troubleshooting

### Common Issues:

1. **Backend not starting**: Check environment variables in `.env`
2. **Frontend not loading**: Check Nginx configuration and file permissions
3. **API calls failing**: Check CORS settings and backend URL in frontend
4. **File downloads not working**: Check Azure credentials and container settings

### Debug Commands:
```bash
# Check if processes are running
ps aux | grep python
ps aux | grep node

# Check disk space
df -h

# Check memory usage
free -h

# Check system logs
sudo journalctl -f
```

---

## 📝 Post-Deployment Checklist

- [ ] Backend health check responds
- [ ] Frontend loads correctly
- [ ] Chat functionality works
- [ ] File downloads work
- [ ] All services start on boot
- [ ] Logs are being written
- [ ] Firewall is configured
- [ ] Environment variables are set

---

## 🔒 Security Recommendations

1. Change default passwords
2. Setup SSL certificate (Let's Encrypt)
3. Configure proper firewall rules
4. Regular system updates
5. Monitor logs for suspicious activity
6. Backup database and configuration files

---

## 📞 Support

If you encounter issues:
1. Check the logs first: `pm2 logs`
2. Verify service status: `pm2 status`
3. Check network connectivity: `curl http://localhost:5000/api/health`
4. Review environment variables: Make sure all credentials are correct
