#!/usr/bin/env bash
set -e

echo "============================================"
echo "  Candidate Evaluation API - Setup"
echo "============================================"
echo ""

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not available."
    echo "Please install Docker Desktop (includes Compose): https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "Docker found: $(docker --version)"
echo ""

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ".env file created."
else
    echo ".env file already exists, skipping."
fi

echo ""
echo "Starting application with Docker Compose..."
echo "(Press Ctrl+C to stop)"
echo ""

docker compose up --build
