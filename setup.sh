#!/bin/bash

# Setup script for Collaborative Code Editor
# This script sets up the development environment

set -e

echo "=========================================="
echo "Collaborative Code Editor - Setup Script"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env files from examples
echo "Creating environment files..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "Created backend/.env"
fi

if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "Created frontend/.env"
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start the application with Docker:"
echo "  docker-compose up"
echo ""
echo "To start for local development:"
echo ""
echo "1. Start Redis:"
echo "   docker run -d -p 6379:6379 redis:7-alpine"
echo ""
echo "2. Start Backend:"
echo "   cd backend"
echo "   python -m venv venv"
echo "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo "   pip install -r requirements.txt"
echo "   uvicorn main:app --reload"
echo ""
echo "3. Start Frontend:"
echo "   cd frontend"
echo "   npm install"
echo "   npm run dev"
echo ""
echo "Access the application at http://localhost:3000"
echo "API documentation at http://localhost:8000/docs"
