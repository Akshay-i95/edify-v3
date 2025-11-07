# Edify AI - Systemd Services Guide

This guide explains how to manage the Edify AI application services that run automatically on the server.

## Overview

The Edify AI application consists of two services:
- **Backend Service** (`edify-backend.service`) - Python Flask API on port 5000
- **Frontend Service** (`edify-frontend.service`) - Next.js application on port 3000

Both services are configured to start automatically on server boot and restart if they crash.

## Service Files Location

- Backend: `/etc/systemd/system/edify-backend.service`
- Frontend: `/etc/systemd/system/edify-frontend.service`

## Common Commands

### Check Status
```bash
# Check both services
sudo systemctl status edify-backend.service edify-frontend.service

# Check individual service
sudo systemctl status edify-backend.service
sudo systemctl status edify-frontend.service
```

### Start/Stop/Restart Services
```bash
# Start both services
sudo systemctl start edify-backend.service edify-frontend.service

# Stop both services
sudo systemctl stop edify-backend.service edify-frontend.service

# Restart both services
sudo systemctl restart edify-backend.service edify-frontend.service

# Restart individual service
sudo systemctl restart edify-backend.service
```

### View Logs
```bash
# View logs for both services
sudo journalctl -u edify-backend.service -u edify-frontend.service -f

# View logs for individual service
sudo journalctl -u edify-backend.service -f
sudo journalctl -u edify-frontend.service -f

# View last 100 lines
sudo journalctl -u edify-backend.service -n 100
```

### Enable/Disable Auto-Start
```bash
# Enable auto-start on boot (already enabled)
sudo systemctl enable edify-backend.service edify-frontend.service

# Disable auto-start on boot
sudo systemctl disable edify-backend.service edify-frontend.service
```

## Service Configuration Details

### Backend Service (`edify-backend.service`)
```ini
[Unit]
Description=Edify AI Backend Service
After=network.target

[Service]
Type=simple
User=i95devteam
Group=i95devteam
WorkingDirectory=/home/i95devteam/edify-v3/backend
Environment=PATH=/home/i95devteam/edify-v3/backend/venv/bin
ExecStart=/home/i95devteam/edify-v3/backend/venv/bin/python3 app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Frontend Service (`edify-frontend.service`)
```ini
[Unit]
Description=Edify AI Frontend Service
After=network.target

[Service]
Type=simple
User=i95devteam
Group=i95devteam
WorkingDirectory=/home/i95devteam/edify-v3/frontend/chatbot
Environment=NODE_ENV=development
Environment=PATH=/usr/bin:/bin:/usr/local/bin
ExecStart=/usr/bin/npm run dev
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Service Not Starting
1. Check service status:
   ```bash
   sudo systemctl status edify-backend.service
   ```

2. Check logs for errors:
   ```bash
   sudo journalctl -u edify-backend.service -n 50
   ```

3. Check file permissions:
   ```bash
   ls -la /home/i95devteam/edify-v3/backend/
   ls -la /home/i95devteam/edify-v3/backend/venv/bin/python3
   ```

### Common Issues & Solutions

#### Backend Service Issues
- **Virtual environment not found**: Ensure venv exists at `/home/i95devteam/edify-v3/backend/venv/`
- **Python dependencies missing**: Activate venv and run `pip install -r requirements.txt`
- **Port 5000 already in use**: Check what's using the port with `sudo lsof -i :5000`

#### Frontend Service Issues
- **Node modules missing**: Run `npm install` in `/home/i95devteam/edify-v3/frontend/chatbot/`
- **Port 3000 already in use**: Check what's using the port with `sudo lsof -i :3000`
- **Build errors**: Check logs and ensure all dependencies are installed

### Modifying Services

1. Edit the service file:
   ```bash
   sudo nano /etc/systemd/system/edify-backend.service
   ```

2. Reload systemd configuration:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Restart the service:
   ```bash
   sudo systemctl restart edify-backend.service
   ```

## Testing Services

### Test Backend
```bash
# Test API endpoint
curl http://localhost:5000/api/health

# Test chat endpoint
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}'
```

### Test Frontend
```bash
# Test homepage
curl http://localhost:3000

# Test API route
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'
```

### Test Domain
```bash
# Test HTTPS domain
curl -I https://edify-ai-assistant.i95-dev.com/
```

## Manual Start/Stop (Alternative)

If you need to run services manually (not recommended for production):

### Backend Manual Start
```bash
cd /home/i95devteam/edify-v3/backend
source venv/bin/activate
python3 app.py
```

### Frontend Manual Start
```bash
cd /home/i95devteam/edify-v3/frontend/chatbot
npm run dev
```

## Service Dependencies

- **Backend requires**: Python 3.x, virtual environment, Flask dependencies
- **Frontend requires**: Node.js, npm, Next.js dependencies
- **Both require**: Network connectivity, proper file permissions

## Auto-Recovery

Both services are configured with:
- `Restart=always` - Automatically restart if they crash
- `RestartSec=3` - Wait 3 seconds before restarting
- Enabled for auto-start on system boot

## Monitoring

Monitor service health with:
```bash
# Quick status check
sudo systemctl is-active edify-backend.service edify-frontend.service

# Detailed status
sudo systemctl status edify-backend.service edify-frontend.service --no-pager

# Resource usage
sudo systemctl show edify-backend.service --property=MainPID
ps aux | grep [PID]
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Check status | `sudo systemctl status edify-backend.service edify-frontend.service` |
| View logs | `sudo journalctl -u edify-backend.service -f` |
| Restart both | `sudo systemctl restart edify-backend.service edify-frontend.service` |
| Stop both | `sudo systemctl stop edify-backend.service edify-frontend.service` |
| Start both | `sudo systemctl start edify-backend.service edify-frontend.service` |
| Reload config | `sudo systemctl daemon-reload` |

---

*Last updated: November 4, 2025*