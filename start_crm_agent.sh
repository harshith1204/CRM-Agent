#!/bin/bash

# CRM Agent Full-Stack Startup Script

set -e

echo "🚀 Starting CRM Agent Full-Stack Application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if MongoDB is running
check_mongodb() {
    print_status "Checking MongoDB connection..."
    if python3 -c "
import pymongo
try:
    client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
    client.server_info()
    print('MongoDB is running')
except:
    print('MongoDB not accessible')
    exit(1)
" 2>/dev/null; then
        print_status "✅ MongoDB is running"
    else
        print_error "❌ MongoDB is not accessible"
        print_status "Starting MongoDB with Docker..."
        docker run -d -p 27017:27017 --name crm-mongodb mongo:latest 2>/dev/null || {
            print_warning "Docker not available or MongoDB container already exists"
            print_error "Please ensure MongoDB is running on localhost:27017"
            exit 1
        }
        sleep 5
        print_status "✅ MongoDB started"
    fi
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
MONGO_URI=mongodb://localhost:27017
MONGO_DB=crm
ALLOWED_COLLECTIONS=leads,tasks,notes,call_logs,activity
LLM_PROVIDER=json_stub
EOF
        print_status "✅ Created .env file"
    fi
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip3 install -r requirements.txt > /dev/null 2>&1 || {
        print_error "Failed to install Python dependencies"
        exit 1
    }
    print_status "✅ Python dependencies installed"
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    cd frontend
    
    # Install npm dependencies
    if [ ! -d node_modules ]; then
        print_status "Installing frontend dependencies..."
        npm install > /dev/null 2>&1 || {
            print_error "Failed to install frontend dependencies"
            exit 1
        }
        print_status "✅ Frontend dependencies installed"
    fi
    
    cd ..
}

# Initialize database
init_database() {
    print_status "Initializing database with sample data..."
    python3 setup_full_stack.py > /dev/null 2>&1 || {
        print_warning "Database initialization failed, continuing anyway..."
    }
    print_status "✅ Database initialized"
}

# Start services
start_services() {
    print_status "Starting services..."
    
    # Start backend in background
    print_status "Starting backend API server..."
    python3 crm_agent_full.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid
    
    # Wait for backend to start
    sleep 3
    
    # Check if backend is running
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "✅ Backend API is running on http://localhost:8000"
    else
        print_error "❌ Backend failed to start"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    
    # Start frontend in background
    print_status "Starting frontend development server..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../.frontend.pid
    cd ..
    
    # Wait for frontend to start
    sleep 5
    
    print_status "✅ Frontend is running on http://localhost:5173"
}

# Cleanup function
cleanup() {
    print_status "Shutting down services..."
    
    if [ -f .backend.pid ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm .backend.pid
        print_status "✅ Backend stopped"
    fi
    
    if [ -f .frontend.pid ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm .frontend.pid
        print_status "✅ Frontend stopped"
    fi
    
    print_status "👋 CRM Agent stopped"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    cd "$(dirname "$0")"
    
    check_mongodb
    setup_environment
    setup_frontend
    init_database
    start_services
    
    echo ""
    echo -e "${GREEN}🎉 CRM Agent is now running!${NC}"
    echo ""
    echo -e "${BLUE}📱 Frontend:${NC} http://localhost:5173"
    echo -e "${BLUE}🔧 Backend API:${NC} http://localhost:8000"
    echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
    
    # Keep script running
    while true; do
        sleep 1
    done
}

# Run main function
main