# AI Chatbot 2.0 - Full Stack with Assistant UI

A modern, full-stack AI chatbot application built with React (Next.js), Flask backend, and assistant-ui components. Features persistent chat sessions, vector database integration, and optional cloud storage.

## 🌟 Features

- **Modern UI**: Built with assistant-ui components for a ChatGPT-like experience
- **Persistent Chat Sessions**: Save and manage multiple conversation threads
- **Backend Integration**: Flask API with SQLite database for chat history
- **Vector Database**: Support for both Pinecone and FAISS for document search
- **Cloud Storage**: Optional assistant-ui cloud integration for cross-device sync
- **Real-time Chat**: Streaming responses with typing indicators
- **Session Management**: Create, switch, and delete chat sessions
- **System Monitoring**: Real-time backend status monitoring

## 🏗️ Architecture

```
frontend/chatbot/          # Next.js React frontend
├── app/                   # App router
├── components/            # React components
└── lib/                   # Utilities and runtime

backend/                   # Flask Python backend
├── app.py                 # Main Flask application
├── chatbot.py             # AI chatbot logic
├── vector_db.py          # Vector database management
└── llm_service.py        # LLM service integration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ with pip
- Node.js 18+ with npm
- Required API keys:
  - Groq API key (for LLM)
  - Pinecone API key (for vector database)
  - Azure Storage credentials (for file downloads)

### Automated Setup

**Windows Users:**
```cmd
setup-dev.bat
```

**Linux/Mac Users:**
```bash
chmod +x setup-dev.sh
./setup-dev.sh
```

This will automatically:
- Set up Python virtual environment
- Install all dependencies
- Create environment files from templates
- Create run scripts

### Manual Setup

1. **Backend Setup**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your API keys
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend/chatbot
   cp .env.example .env.local
   # Edit .env.local with your configuration
   npm install
   ```

3. **Configure Environment Variables**:

   **Backend** (`backend/.env`):
   ```env
   # LLM Configuration (Groq)
   GROQ_API_KEY=your-groq-api-key-here
   GROQ_MODEL=llama3-8b-8192
   
   # Vector Database (Pinecone)
   PINECONE_API_KEY=your-pinecone-api-key-here
   PINECONE_ENVIRONMENT=us-east-1-aws
   PINECONE_INDEX_NAME=chatbot-chunks
   
   # Azure Storage (for file downloads)
   AZURE_STORAGE_CONNECTION_STRING=your_connection_string
   AZURE_STORAGE_ACCOUNT_NAME=your_account_name
   AZURE_STORAGE_CONTAINER_NAME=your_container_name
   
   # Flask Configuration
   FLASK_SECRET_KEY=your-secret-key-here
   FLASK_PORT=5000
   FLASK_DEBUG=true
   ```

   **Frontend** (`frontend/chatbot/.env.local`):
   ```env
   # Backend Configuration
   NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
   BACKEND_URL=http://localhost:5000
   
   # Application Configuration
   NEXT_PUBLIC_APP_ENV=development
   NEXT_PUBLIC_ENABLE_REASONING=true
   NEXT_PUBLIC_ENABLE_SOURCES=true
   NEXT_PUBLIC_DEFAULT_ROLE=user
   ```

### Running the Application

**Option 1: Use Run Scripts** (After automated setup)
```bash
# Windows
run-dev.bat

# Linux/Mac
./run-dev.sh
```

**Option 2: Manual Start**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py

# Terminal 2 - Frontend  
cd frontend/chatbot
npm run dev
```

**Access the Application**:
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:5000](http://localhost:5000)

## 🔧 Configuration

### Vector Database Setup

#### Option 1: Pinecone (Recommended for production)
1. Create a Pinecone account and get your API key
2. Create an index named `chatbot-chunks` with dimension 384
3. Set `VECTOR_DB_TYPE=pinecone` in backend environment

#### Option 2: FAISS (Good for development)
1. Set `VECTOR_DB_TYPE=faiss` in backend environment
2. The FAISS index will be created automatically

### Assistant UI Cloud Setup
1. Sign up for assistant-ui cloud (if available)
2. Get your API key
3. Set `NEXT_PUBLIC_ASSISTANT_UI_API_KEY` in frontend environment
4. Enable with `NEXT_PUBLIC_ENABLE_CLOUD_STORAGE=true`

## 📊 API Endpoints

### Backend (Flask) - Port 5000

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/health` | GET | Health check |
| `/api/chat/sessions` | GET | Get all chat sessions |
| `/api/chat/sessions` | POST | Create new session |
| `/api/chat/sessions/{id}` | GET | Get session with messages |
| `/api/chat/sessions/{id}` | DELETE | Delete session |
| `/api/chat/sessions/{id}/messages` | POST | Send message |
| `/api/system/status` | GET | System status |

### Frontend (Next.js) - Port 3000

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/chat` | POST | Chat with assistant (proxy to backend) |
| `/api/sessions` | GET/POST | Session management |
| `/api/sessions/{id}` | GET/DELETE | Individual session |

## 🎯 Usage

### Basic Chat
1. Open the application
2. Start typing in the message input
3. The AI will respond with relevant information

### Session Management
- Click "New Thread" to start a fresh conversation
- Click on any session in the sidebar to switch
- Click the archive icon to delete a session

### System Monitoring
- Check the "System Status" in the sidebar
- Green indicators show healthy components
- Red indicators show issues that need attention

## 🔍 Development

### Frontend Development
```bash
cd frontend/chatbot
npm run dev      # Start development server
npm run build    # Build for production
npm run lint     # Run linting
```

### Backend Development
```bash
cd backend
source venv/bin/activate
python app.py                    # Start Flask server
python check_database.py         # Check database status
python manage_pinecone_index.py  # Manage Pinecone index
```

## � Troubleshooting

### Backend Issues
- **Database errors**: Check `backend/backend.log`
- **Vector DB connection**: Verify API keys and configuration
- **Port conflicts**: Change `FLASK_PORT` in environment

### Frontend Issues
- **Build errors**: Run `npm install` to update dependencies
- **API connection**: Verify `BACKEND_URL` matches Flask server
- **Assistant UI issues**: Check assistant-ui documentation

### Common Problems

1. **"System not ready" error**:
   - Check backend logs
   - Verify vector database configuration
   - Ensure all required environment variables are set

2. **Sessions not loading**:
   - Check backend is running on correct port
   - Verify CORS configuration
   - Check browser console for errors

3. **Chat responses not working**:
   - Verify OpenAI API key
   - Check backend logs for LLM service errors
   - Ensure proper session creation

## 📁 Project Structure

```
chatbot-2.0/
├── frontend/chatbot/              # Next.js frontend
│   ├── app/                       # App router
│   │   ├── api/                   # API routes
│   │   ├── assistant.tsx          # Main assistant component
│   │   └── page.tsx              # Home page
│   ├── components/                # React components
│   │   ├── assistant-ui/          # Assistant UI components
│   │   └── ui/                    # Base UI components
│   ├── lib/                       # Utilities
│   │   ├── backend-runtime.ts     # Backend integration
│   │   ├── chat-runtime.ts       # Enhanced chat runtime
│   │   └── chat-context.ts       # React context
│   └── package.json              # Dependencies
├── backend/                       # Flask backend
│   ├── app.py                     # Main application
│   ├── chatbot.py                # Chatbot logic
│   ├── vector_db.py              # Vector database
│   ├── llm_service.py            # LLM integration
│   └── requirements.txt          # Python dependencies
├── setup.sh                      # Setup script (Unix)
├── setup.bat                     # Setup script (Windows)
└── README.md                     # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## � Environment Configuration

For detailed environment setup instructions, see [ENVIRONMENT_SETUP_GUIDE.md](ENVIRONMENT_SETUP_GUIDE.md).

### Key Environment Files:
- `backend/.env` - Backend configuration (API keys, database settings)
- `frontend/chatbot/.env.local` - Frontend configuration (backend URL, features)
- `backend/.env.example` - Backend template with all variables
- `frontend/chatbot/.env.example` - Frontend template with all variables

### Setup Scripts:
- `setup-dev.sh` / `setup-dev.bat` - Automated development setup
- `run-dev.sh` / `run-dev.bat` - Start both servers
- `setup-production.sh` - Production deployment setup

## �📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Assistant UI](https://assistant-ui.com/) for the React components
- [Groq](https://groq.com/) for fast LLM inference
- [Pinecone](https://pinecone.io/) for vector database
- [Next.js](https://nextjs.org/) for the React framework
- [Flask](https://flask.palletsprojects.com/) for the backend framework
