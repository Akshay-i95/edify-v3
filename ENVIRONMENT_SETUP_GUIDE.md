# Edify AI V2 - Environment Configuration Guide

This guide will help you set up and connect the frontend and backend components of Edify AI V2 using environment variables.

## 🚀 Quick Start

### For Development

**Windows Users:**
```cmd
setup-dev.bat
```

**Linux/Mac Users:**
```bash
chmod +x setup-dev.sh
./setup-dev.sh
```

**Manual Setup:**
```bash
# Backend setup
cd backend
cp .env.example .env
# Edit .env with your configuration
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup  
cd ../frontend/chatbot
cp .env.example .env.local
# Edit .env.local with your configuration
npm install
```

## 📁 Environment Files Structure

```
edify-ai-v2/
├── backend/
│   ├── .env                 # Your development config
│   ├── .env.example         # Template with all variables
│   └── .env.production      # Production config (created by setup script)
└── frontend/chatbot/
    ├── .env.local           # Your development config
    ├── .env.example         # Template with all variables
    └── .env.production      # Production config (created by setup script)
```

## 🔧 Backend Configuration (backend/.env)

### Required Variables

```bash
# Flask Configuration
FLASK_SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_PORT=5000
FLASK_DEBUG=true  # false for production
FLASK_ENV=development  # production for production

# Vector Database (Pinecone)
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=chatbot-chunks

# LLM Service (Groq)
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama3-8b-8192

# Azure Storage (for file downloads)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account-name
AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key
AZURE_STORAGE_CONTAINER_NAME=your-container-name
```

### Optional Variables

```bash
# Vector Search Configuration
MAX_CONTEXT_CHUNKS=8
MIN_SIMILARITY_THRESHOLD=0.35
ENABLE_CITATIONS=true
ENABLE_CONTEXT_EXPANSION=true

# Performance Configuration
MAX_CONVERSATION_HISTORY=20
MAX_CONTEXT_COMPRESSION_LENGTH=30

# Feature Flags
ENABLE_REASONING=true
ENABLE_VIDEO_SOURCES=true
ENABLE_SOURCE_CITATIONS=true

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,https://your-production-domain.com

# Logging
LOG_LEVEL=INFO
DEBUG_MODE=false
```

## 🌐 Frontend Configuration (frontend/chatbot/.env.local)

### Required Variables

```bash
# Backend API URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
BACKEND_URL=http://localhost:5000

# Application Environment
NEXT_PUBLIC_APP_ENV=development
NODE_ENV=development
```

### Optional Variables

```bash
# Application Metadata
NEXT_PUBLIC_APP_NAME=Edify AI Assistant
NEXT_PUBLIC_APP_VERSION=2.0.0

# Feature Configuration
NEXT_PUBLIC_ENABLE_REASONING=true
NEXT_PUBLIC_ENABLE_SOURCES=true
NEXT_PUBLIC_ENABLE_VIDEOS=true
NEXT_PUBLIC_DEFAULT_ROLE=user

# UI Configuration
NEXT_PUBLIC_DEFAULT_NAMESPACES=kb-psp,kb-msp
NEXT_PUBLIC_SHOW_NAMESPACE_SELECTOR=true
NEXT_PUBLIC_SHOW_ROLE_SELECTOR=false

# Performance Configuration
NEXT_PUBLIC_ENABLE_STREAMING=true
NEXT_PUBLIC_STREAM_DELAY_MS=20
NEXT_PUBLIC_API_TIMEOUT=30000

# Development Configuration
NEXT_PUBLIC_DEV_MODE=true
NEXT_PUBLIC_DEBUG_LOGGING=true
NEXT_PUBLIC_SHOW_DETAILED_ERRORS=true
```

## 🔗 How Frontend and Backend Connect

### 1. API Communication
The frontend connects to the backend through the `NEXT_PUBLIC_BACKEND_URL` environment variable:

```typescript
// frontend/chatbot/app/api/chat/route.ts
const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5000';
const response = await fetch(`${backendUrl}/api/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(requestData),
});
```

### 2. CORS Configuration
The backend allows requests from the frontend through CORS configuration:

```python
# backend/app.py
CORS(app, origins=[
    "http://localhost:3000",  # Development frontend
    "https://your-production-domain.com",  # Production frontend
])
```

### 3. Environment-Specific URLs
- **Development**: Frontend (`localhost:3000`) → Backend (`localhost:5000`)
- **Production**: Frontend (`your-domain.com`) → Backend (`your-domain.com/api`)

## 🏃‍♂️ Running the Application

### Development Mode

**Option 1: Use the run script**
```bash
# Windows
run-dev.bat

# Linux/Mac
./run-dev.sh
```

**Option 2: Run manually**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py

# Terminal 2 - Frontend
cd frontend/chatbot
npm run dev
```

### Production Mode

```bash
# Set up production environment
chmod +x setup-production.sh
./setup-production.sh

# Deploy
./deploy.sh
```

## 🔍 Troubleshooting

### Common Issues

1. **"Connection refused" error**
   - Check that backend is running on the correct port
   - Verify `NEXT_PUBLIC_BACKEND_URL` matches backend URL
   - Check CORS configuration in backend

2. **"API key not found" error**
   - Verify your API keys are set in backend/.env
   - Check that .env file is in the correct location
   - Restart the backend after changing .env

3. **Environment variables not loading**
   - Frontend: Variables must start with `NEXT_PUBLIC_` to be accessible in browser
   - Backend: Make sure python-dotenv is loading the .env file
   - Restart servers after changing environment files

### Environment Variable Debugging

**Backend:**
```python
# Add to app.py to debug
import os
print("Backend URL:", os.getenv('BACKEND_URL'))
print("Debug mode:", os.getenv('FLASK_DEBUG'))
```

**Frontend:**
```typescript
// Add to any component to debug
console.log('Backend URL:', process.env.NEXT_PUBLIC_BACKEND_URL);
console.log('App Env:', process.env.NEXT_PUBLIC_APP_ENV);
```

## 🔐 Security Considerations

### Development
- Use different secret keys for development and production
- Never commit .env files to version control
- Use placeholder values in .env.example

### Production
- Use strong, unique secret keys
- Enable HTTPS with proper SSL certificates
- Restrict CORS origins to your actual domains
- Set `DEBUG_MODE=false` and `FLASK_DEBUG=false`
- Use environment-specific API keys

## 📝 Environment Variable Reference

### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_SECRET_KEY` | ✅ | - | Flask session secret key |
| `FLASK_PORT` | ❌ | 5000 | Backend server port |
| `FLASK_DEBUG` | ❌ | false | Enable Flask debug mode |
| `PINECONE_API_KEY` | ✅ | - | Pinecone vector database API key |
| `GROQ_API_KEY` | ✅ | - | Groq LLM API key |
| `AZURE_STORAGE_CONNECTION_STRING` | ✅ | - | Azure blob storage connection |
| `MAX_CONTEXT_CHUNKS` | ❌ | 8 | Maximum context chunks for RAG |
| `ENABLE_CITATIONS` | ❌ | true | Show document citations |

### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | ✅ | http://localhost:5000 | Backend API URL |
| `NEXT_PUBLIC_APP_ENV` | ❌ | development | Application environment |
| `NEXT_PUBLIC_ENABLE_REASONING` | ❌ | true | Show AI reasoning |
| `NEXT_PUBLIC_ENABLE_SOURCES` | ❌ | true | Show source documents |
| `NEXT_PUBLIC_DEFAULT_ROLE` | ❌ | user | Default user role |
| `NEXT_PUBLIC_API_TIMEOUT` | ❌ | 30000 | API request timeout (ms) |

## 🚀 Deployment

### Development Deployment
1. Run setup script: `./setup-dev.sh` or `setup-dev.bat`
2. Configure API keys in `.env` files
3. Start servers: `./run-dev.sh` or `run-dev.bat`

### Production Deployment
1. Run production setup: `./setup-production.sh`
2. Configure production API keys
3. Set up SSL certificates
4. Deploy: `./deploy.sh`

Access your application:
- **Development**: http://localhost:3000
- **Production**: https://your-domain.com

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all required environment variables are set
3. Check server logs for detailed error messages
4. Ensure all dependencies are installed correctly