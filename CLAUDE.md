# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project rules

命令を遂行する前に**必ず**`.cursor/rules/first.mdc`ファイルを読み込んだ上、進行してください。

## Project Overview

SearchFace is a face recognition and similarity search application built with Python FastAPI backend and Next.js frontend. Users can upload images to find similar faces from a pre-built database using FAISS vector similarity search. The application uses Turso (SQLite-compatible cloud database) for data storage.

## Development Commands

**IMPORTANT: This project runs in Docker containers. All development and build commands should be executed within Docker containers.**

### Docker Development (Primary Method)
```bash
# Start full stack with docker-compose (recommended for development)
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Backend Commands (via Docker)
```bash
# Execute commands in backend container
docker-compose exec backend python src/run_api.py --sync-db

# Access backend container shell
docker-compose exec backend bash

# Build backend image only
docker build -t searchface:latest .
```

### Frontend Commands (via Docker)
```bash
# Execute frontend commands in container
docker-compose exec frontend npm run build
docker-compose exec frontend npm run format
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run check

# Access frontend container shell
docker-compose exec frontend bash

# Install new dependencies
docker-compose exec frontend npm install [package-name]
```

### Development Workflow
```bash
# 1. Start development environment
docker-compose up

# 2. Make code changes (hot reload enabled)
# Frontend: Changes auto-reload via npm run dev
# Backend: Changes auto-reload when DEBUG=true

# 3. Run linting/formatting (in frontend container)
docker-compose exec frontend npm run check

# 4. Build for testing (in frontend container)
docker-compose exec frontend npm run build

# 5. Test API
curl -X POST "http://localhost:10000/api/search" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@data/images/input.jpg"
```

### Local Development (Not Recommended)
Use only when Docker is not available:

**Backend (Python FastAPI)**
```bash
source venv/bin/activate
pip install --use-pep517 -r requirements.txt
python src/run_api.py
```

**Frontend (Next.js)**
```bash
cd frontend
npm install
npm run dev
npm run build  # For production builds
npm run check  # For linting/formatting
```


## Architecture Overview

### Backend Structure (`src/`)
- **api/**: FastAPI application with routes and models
- **database/**: Turso (SQLite-compatible) + FAISS vector database layer
- **face/**: Face detection and encoding using face_recognition library
- **image/**: Image processing, collection, and storage (Cloudflare R2)
- **core/**: Error handling, exceptions, and middleware
- **utils/**: Shared utilities (logging, similarity calculations, R2 uploader)

### Frontend Structure (`frontend/src/`)
- **app/**: Next.js App Router with main page
- **actions/search/**: Server actions for API communication
- **features/**: Feature-specific components (image upload, background)
- **components/**: Reusable UI components (shadcn/ui based)

### Key Technologies
- **Backend**: FastAPI, face_recognition, FAISS, SQLite, Cloudflare R2, uvicorn
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Radix UI
- **Tools**: Biome (formatting/linting), Docker, docker-compose

## Face Recognition Pipeline

1. **Image Upload**: Users upload image via drag-and-drop interface
2. **Face Detection**: Extract single face encoding (128-dimensional vector)
3. **Similarity Search**: Query FAISS index for nearest neighbors
4. **Results**: Return top matches with similarity scores and metadata

## Important Constraints

- **Single Face Enforcement**: Images must contain exactly one detectable face
- **File Limits**: 5MB max upload size, supports .jpg/.jpeg/.png
- **Performance Target**: < 500ms response time for search operations
- **Database**: Uses custom face_recognition Docker base image for CV dependencies

## Configuration Notes

- **Ports**: Backend (10000), Frontend (3000)
- **Environment**: Set DEBUG=true for hot reload in development
- **Database**: 
  - FAISS index stored in `/data/` directory (face.index)
  - SQLite data managed by Turso cloud database
  - Required environment variables: TURSO_DATABASE_URL, TURSO_AUTH_TOKEN
- **Docker Network**: Uses bridge network with subnet 172.20.0.0/16

## Database Setup (Turso)

1. Create a `.env` file from `.env.sample`
2. Set your Turso database credentials:
   ```bash
   TURSO_DATABASE_URL=libsql://your-database-name.turso.io
   TURSO_AUTH_TOKEN=your-auth-token-here
   ```
3. **IMPORTANT**: Run the database schema setup before starting the application:
   ```bash
   # Using Turso CLI
   turso db shell your-database-name < database_schema.sql
   
   # Or copy the contents of database_schema.sql and execute in Turso web console
   ```
4. The schema file creates the required tables for search history and ranking features

## Code Style Guidelines

- **Python**: Follows PEP 8, uses type hints, comprehensive error handling
- **Frontend**: Uses Biome for formatting/linting, TypeScript strict mode
- **Error Handling**: Structured error codes defined in `src/core/errors.py`
- **Logging**: Centralized logging via `src/utils/log_utils.py`

## Development Workflow Notes

This project follows a structured development approach with task management files in `.cursor/rules/`. The codebase emphasizes:
- **Docker-first development**: All commands should be run in containers
- Clear separation between backend API and frontend UI
- Comprehensive error handling with user-friendly messages
- Performance optimization for real-time face search
- Modular architecture for maintainability

## Docker Container Guidelines

- **Always use docker-compose exec** for running commands inside containers
- **Frontend builds**: Use `docker-compose exec frontend npm run build`
- **Backend testing**: Use `docker-compose exec backend python [script]`
- **Code quality**: Use `docker-compose exec frontend npm run check` for linting
- **Hot reload**: Both frontend and backend support hot reload in development mode
