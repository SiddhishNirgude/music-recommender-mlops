# Docker Deployment Guide

## Overview

This project uses Docker to containerize the FastAPI backend and Streamlit frontend for easy deployment and reproducibility.

## Prerequisites

- Docker installed: https://docs.docker.com/get-docker/
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

### Build and Run

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode (background)
docker-compose up -d --build
```

### Access Services

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

### Stop Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Container Details

### FastAPI Container
- **Name**: music-recommender-api
- **Port**: 8000
- **Base Image**: python:3.12-slim
- **Contains**: Model, API endpoints, recommendation logic

### Streamlit Container
- **Name**: music-recommender-ui
- **Port**: 8501
- **Base Image**: python:3.12-slim
- **Contains**: Web UI, visualization

## Useful Commands

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs streamlit

# Follow logs
docker-compose logs -f
```

### Rebuild Specific Service

```bash
# Rebuild API only
docker-compose up --build api

# Rebuild Streamlit only
docker-compose up --build streamlit
```

### Check Container Status

```bash
# List running containers
docker-compose ps

# Check health
docker-compose ps
```

### Execute Commands in Container

```bash
# Access API container shell
docker-compose exec api bash

# Access Streamlit container shell
docker-compose exec streamlit bash
```

## Troubleshooting

### Port Already in Use

If ports 8000 or 8501 are in use:

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Find and kill process using port 8501
lsof -ti:8501 | xargs kill -9
```

Or modify ports in `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Change host port
```

### Container Fails to Start

```bash
# Check logs
docker-compose logs api
docker-compose logs streamlit

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Model Files Not Found

Ensure model files exist:

```bash
ls -lh models/
ls -lh data/processed/
```

If missing, train the model first:

```bash
python scripts/train_model.py
```

## Development vs Production

### Development (Current Setup)

- Uses volumes to mount local files
- Hot reload enabled
- Debug mode on

### Production Recommendations

1. Use specific image tags (not `latest`)
2. Set environment variables via `.env` file
3. Use Docker secrets for sensitive data
4. Add resource limits
5. Use production WSGI server (gunicorn)
6. Enable HTTPS
7. Add monitoring (Prometheus)

## Architecture

```
┌─────────────────┐
│   Streamlit     │  Port 8501
│   (Frontend)    │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│    FastAPI      │  Port 8000
│   (Backend)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   ALS Model     │
│   + Data        │
└─────────────────┘
```

## Network Configuration

Both containers are on the same Docker network (`music-recommender-network`), allowing them to communicate internally.

Streamlit connects to API using:
- Internal: `http://api:8000`
- External: `http://localhost:8000`

## Volume Mounts

- `./models` → `/app/models` (API container)
- `./data/processed` → `/app/data/processed` (API container)

This allows containers to access trained models and processed data without copying large files into images.

## Health Checks

Both containers have health checks:

- **API**: Checks `/health` endpoint every 30s
- **Streamlit**: Checks `/_stcore/health` every 30s

Docker Compose waits for API to be healthy before starting Streamlit.

## Notes

- First build may take 5-10 minutes (downloads dependencies)
- Subsequent builds are faster (uses cache)
- Containers restart automatically if they crash
- Logs are available via `docker-compose logs`

## Support

For issues, check:
1. Container logs: `docker-compose logs`
2. Health status: `docker-compose ps`
3. Model files exist: `ls models/`
4. API is accessible: `curl http://localhost:8000/health`
