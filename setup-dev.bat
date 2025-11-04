@echo off
REM ===========================================
REM EDIFY AI V2 - WINDOWS DEVELOPMENT SETUP
REM ===========================================
REM This script sets up the development environment on Windows

echo 🚀 Setting up Edify AI V2 Development Environment...

REM Check if we're in the right directory
if not exist "README.md" (
    echo ❌ Please run this script from the project root directory
    exit /b 1
)
if not exist "backend" (
    echo ❌ Backend directory not found
    exit /b 1
)
if not exist "frontend" (
    echo ❌ Frontend directory not found
    exit /b 1
)

echo ℹ️ Project root directory detected: %CD%

REM Setup Backend Environment
echo.
echo 📦 Setting up Backend Environment...

cd backend

REM Check if .env exists, if not copy from .env.example
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ✅ Created backend .env file from template
        echo ⚠️ Please edit backend\.env with your actual configuration values
    ) else (
        echo ❌ backend\.env.example not found!
        exit /b 1
    )
) else (
    echo ℹ️ Backend .env file already exists
)

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python not found! Please install Python 3.8 or higher
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

echo ℹ️ Using Python: %PYTHON_CMD%

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo ℹ️ Creating Python virtual environment...
    %PYTHON_CMD% -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ℹ️ Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo ℹ️ Installing Python dependencies...
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ Python dependencies installed
) else (
    echo ❌ requirements.txt not found!
    exit /b 1
)

REM Go back to project root
cd ..

REM Setup Frontend Environment
echo.
echo 🌐 Setting up Frontend Environment...

cd frontend\chatbot

REM Check if .env.local exists, if not copy from .env.example
if not exist ".env.local" (
    if exist ".env.example" (
        copy ".env.example" ".env.local" >nul
        echo ✅ Created frontend .env.local file from template
        echo ⚠️ Please edit frontend\chatbot\.env.local with your actual configuration values
    ) else (
        echo ❌ frontend\chatbot\.env.example not found!
        exit /b 1
    )
) else (
    echo ℹ️ Frontend .env.local file already exists
)

REM Check Node.js installation
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found! Please install Node.js 18 or higher
    exit /b 1
) else (
    echo ℹ️ Using Node.js: && node --version
)

REM Check npm installation
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm not found!
    exit /b 1
) else (
    echo ℹ️ Using npm: && npm --version
)

REM Install Node.js dependencies
echo ℹ️ Installing Node.js dependencies...
npm install
echo ✅ Node.js dependencies installed

REM Go back to project root
cd ..\..

REM Create run script for Windows
echo.
echo 📝 Creating run scripts...

REM Create development run script
(
echo @echo off
echo echo 🚀 Starting Edify AI V2 Development Servers...
echo.
echo echo 📦 Starting backend server...
echo start "Backend Server" cmd /c "cd backend && venv\Scripts\activate.bat && python app.py"
echo.
echo echo Waiting for backend to start...
echo timeout /t 3 /nobreak ^>nul
echo.
echo echo 🌐 Starting frontend server...
echo start "Frontend Server" cmd /c "cd frontend\chatbot && npm run dev"
echo.
echo echo ✅ Development servers are starting:
echo echo    🌐 Frontend: http://localhost:3000
echo echo    📦 Backend:  http://localhost:5000
echo echo.
echo echo Press any key to exit...
echo pause ^>nul
) > run-dev.bat

echo ✅ Created run-dev.bat script

REM Final instructions
echo.
echo 🎉 Development environment setup complete!
echo.
echo Next steps:
echo 1. Edit backend\.env with your actual API keys and configuration
echo 2. Edit frontend\chatbot\.env.local if needed
echo 3. Run 'run-dev.bat' to start both servers
echo.
echo Important configuration:
echo - Backend will run on: http://localhost:5000
echo - Frontend will run on: http://localhost:3000
echo - Make sure your backend\.env has the correct API keys (Groq, Pinecone, Azure^)
echo.
echo ⚠️ Don't forget to configure your environment variables before running!

pause