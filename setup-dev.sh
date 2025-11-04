#!/bin/bash
# ===========================================
# EDIFY AI V2 - DEVELOPMENT SETUP SCRIPT
# ===========================================
# This script sets up the development environment

echo "🚀 Setting up Edify AI V2 Development Environment..."

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

# Setup Backend Environment
echo -e "\n${BLUE}📦 Setting up Backend Environment...${NC}"

cd backend

# Check if .env exists, if not copy from .env.example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Created backend .env file from template"
        print_warning "Please edit backend/.env with your actual configuration values"
    else
        print_error "backend/.env.example not found!"
        exit 1
    fi
else
    print_info "Backend .env file already exists"
fi

# Check Python installation
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    print_error "Python not found! Please install Python 3.8 or higher"
    exit 1
fi

print_info "Using Python: $($PYTHON_CMD --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
    print_status "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_info "Installing Python dependencies..."
source venv/bin/activate || source venv/Scripts/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Go back to project root
cd ..

# Setup Frontend Environment
echo -e "\n${BLUE}🌐 Setting up Frontend Environment...${NC}"

cd frontend/chatbot

# Check if .env.local exists, if not copy from .env.example
if [ ! -f ".env.local" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        print_status "Created frontend .env.local file from template"
        print_warning "Please edit frontend/chatbot/.env.local with your actual configuration values"
    else
        print_error "frontend/chatbot/.env.example not found!"
        exit 1
    fi
else
    print_info "Frontend .env.local file already exists"
fi

# Check Node.js installation
if command -v node &> /dev/null; then
    print_info "Using Node.js: $(node --version)"
else
    print_error "Node.js not found! Please install Node.js 18 or higher"
    exit 1
fi

# Check npm installation
if command -v npm &> /dev/null; then
    print_info "Using npm: $(npm --version)"
else
    print_error "npm not found!"
    exit 1
fi

# Install Node.js dependencies
print_info "Installing Node.js dependencies..."
npm install
print_status "Node.js dependencies installed"

# Go back to project root
cd ../..

# Create run scripts
echo -e "\n${BLUE}📝 Creating run scripts...${NC}"

# Create development run script
cat > run-dev.sh << 'EOF'
#!/bin/bash
# Development runner script

echo "🚀 Starting Edify AI V2 Development Servers..."

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start backend server
echo "📦 Starting backend server..."
cd backend
source venv/bin/activate || source venv/Scripts/activate
python app.py &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID"
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "🌐 Starting frontend server..."
cd frontend/chatbot
npm run dev &
FRONTEND_PID=$!
echo "Frontend server started with PID: $FRONTEND_PID"
cd ../..

echo ""
echo "✅ Development servers are running:"
echo "   🌐 Frontend: http://localhost:3000"
echo "   📦 Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID
EOF

chmod +x run-dev.sh
print_status "Created run-dev.sh script"

# Final instructions
echo -e "\n${GREEN}🎉 Development environment setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Edit backend/.env with your actual API keys and configuration"
echo "2. Edit frontend/chatbot/.env.local if needed"
echo "3. Run './run-dev.sh' to start both servers"
echo ""
echo -e "${BLUE}Important configuration:${NC}"
echo "- Backend will run on: http://localhost:5000"
echo "- Frontend will run on: http://localhost:3000"
echo "- Make sure your backend/.env has the correct API keys (Groq, Pinecone, Azure)"
echo ""
print_warning "Don't forget to configure your environment variables before running!"