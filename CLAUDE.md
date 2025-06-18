# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project rules

**CRITICAL: 以下のルールは必須です。例外なく従ってください。**

### Task Management Rules (最重要)

1. **ユーザーからの指示を受けた際の必須プロセス:**
  - 命令を遂行する前に**必ず**`.cursor/rules/first.mdc`ファイルを読み込む
  - プロジェクトの詳細な設定は `.cursor/rules/project.mdc` を参照してください
  - Python開発に関する詳細な設定は `.cursor/rules/python.mdc` を参照してください
  - データベースに関する詳細な設定は `.cursor/rules/db.mdc` を参照してください
  - API仕様に関する詳細な設定は `.cursor/rules/api.mdc` を参照してください
  - フロントエンド開発に関する詳細な設定は `.cursor/rules/frontend.mdc` を参照してください

### Development Rules

- `.cursor/rules/`配下のすべてのルールファイルに従う
- コーディングガイドライン、API仕様、データベース設計はすべて`.cursor/rules/`で管理
- やり取りする上で明確になったルール、変更になったルールは都度`.cursor/rules/`に反映する

### **🚨 CRITICAL DATABASE PROTECTION RULES 🚨**

**絶対に守らなければならないルール:**

1. **本番データベース保護 (ABSOLUTE RULE):**
   - `data/` ディレクトリ内のSQLiteデータベース（`face_database.db`等）を**絶対に変更・更新してはいけない**
   - `data/` ディレクトリ内のFAISSインデックス（`face.index`等）を**絶対に変更・更新してはいけない**
   - テストコードで本番データベースに接続することを**絶対に禁止**

2. **テスト実行時の必須要件:**
   - 全てのテストは一時的なデータベースファイル（`/tmp/`配下）を使用すること
   - `PersonDatabase`, `FaceIndexDatabase`の初期化時は必ず本番パスをモックすること
   - `CREATE TABLE`, `INSERT`, `UPDATE`, `DELETE`等のDB変更操作は一時ファイルでのみ実行すること

3. **違反時の対応:**
   - 本番データベースへの接続・変更を検出した場合は**即座に処理を停止**すること
   - テストコードが`data/`ディレクトリにアクセスしていることを発見した場合は**緊急修正**すること

**このルールは例外なく適用され、どのような理由があっても違反してはいけません。**

### **📋 Test Database Utilities (推奨)**

安全なテストのため、以下のutility関数を使用してください：

```python
# tests/utils/database_test_utils.py
from tests.utils.database_test_utils import (
    isolated_test_database,     # 自動クリーンアップ付きテストDB
    create_test_person_data,    # 安全なテストデータ作成
    create_test_database_with_schema  # スキーマ付きテストDB作成
)

# 使用例：安全な統合テスト
with isolated_test_database() as (conn, db_path):
    person_id = create_test_person_data(conn, "Test Person", "/tmp/test.jpg")
    # テスト実行...
    # 自動的にクリーンアップされる
```

**利点:**
- **単一ソース管理**: `sqlite_schema.sql`を使用してスキーマの重複管理を回避
- **実装との一致保証**: プロジェクトの公式スキーマファイルを使用
- **本番データベースアクセスの完全防止**: 全て一時ファイルで動作
- **自動ファイルクリーンアップ**: メモリリークやディスク容量の問題を防止
- **セキュリティチェック内蔵**: 本番パスアクセスを自動検出・拒否

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

# Run backend tests
docker-compose exec backend python -m pytest

# Access backend container shell
docker-compose exec backend bash

# Build backend image only
docker build -t searchface:latest .
```

### Frontend Commands (via Docker)
```bash
# Execute frontend commands in container
# ⚠️ WARNING: DO NOT run npm run build - it breaks the development environment
# Frontend uses hot reload with automatic file watching - just save files to see changes
docker-compose exec frontend npm run format
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run check

# Run frontend tests
docker-compose exec frontend npm run test
docker-compose exec frontend npm run test:ui

# Access frontend container shell
docker-compose exec frontend bash

# Install new dependencies
docker-compose exec frontend npm install [package-name]
```

### Development Workflow (Updated with Testing)
```bash
# 1. Start development environment
docker-compose up

# 2. Make code changes (hot reload enabled)
# Frontend: Changes auto-reload via npm run dev
# Backend: Changes auto-reload when DEBUG=true

# 3. Create/Update tests for your changes
# Backend: Create test files in tests/ directory
# Frontend: Create test files co-located with source files

# 4. Run tests to ensure they pass
# Backend tests
docker-compose exec backend python -m pytest

# Frontend tests
docker-compose exec frontend npm run test

# 5. Run linting/formatting (frontend only)
docker-compose exec frontend npm run check

# 6. Frontend verification (NO BUILD NEEDED - uses hot reload)
# Just save files to see changes automatically

# 7. Test API manually (optional)
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
- **Testing**: pytest (Backend), vitest + React Testing Library + MSW (Frontend)
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
- **Test-driven development**: All new features and changes must include tests
- Clear separation between backend API and frontend UI
- Comprehensive error handling with user-friendly messages
- Performance optimization for real-time face search
- Modular architecture for maintainability

## Testing Guidelines

### Backend Testing (pytest)
- **Location**: Tests located in `tests/` directory
- **Structure**: Mirror the `src/` directory structure in `tests/`
- **Coverage**: Unit tests for all API endpoints, database operations, and utility functions
- **Fixtures**: Use pytest fixtures for database setup and mock data
- **Command**: `docker-compose exec backend python -m pytest`

### Frontend Testing (vitest + React Testing Library + MSW)
- **Location**: Tests co-located with source files (same directory)
- **Naming**: `*.test.ts` or `*.test.tsx` for test files
- **Coverage**: API functions, Server Actions, UI Components, Utility functions
- **Mocking**: Use MSW (Mock Service Worker) for realistic API mocking
- **Commands**:
  - `docker-compose exec frontend npm run test` - Run tests
  - `docker-compose exec frontend npm run test:ui` - Run with UI
  - `docker-compose exec frontend npm run check` - Lint/format check

### Testing Requirements
- **All new features**: Must include corresponding tests
- **Bug fixes**: Must include regression tests
- **Code changes**: Must ensure existing tests still pass
- **Coverage**: Aim for comprehensive test coverage of critical paths

## Docker Container Guidelines

- **Always use docker-compose exec** for running commands inside containers
- **Frontend builds**: Use `docker-compose exec frontend npm run build`
- **Backend testing**: Use `docker-compose exec backend python -m pytest`
- **Frontend testing**: Use `docker-compose exec frontend npm run test`
- **Code quality**: Use `docker-compose exec frontend npm run check` for linting
- **Hot reload**: Both frontend and backend support hot reload in development mode

## File Update and Restart Procedures

When updating code files, follow these container restart procedures to ensure changes take effect:

### Frontend File Updates
```bash
# Frontend files (.tsx, .ts, .js, .css, etc.) are automatically updated via hot reload
# No restart required - just save the file and changes will be reflected immediately

# Only restart if frontend container stops responding or has issues
docker-compose restart frontend

# Alternative: If frontend container stops responding
docker-compose down
docker-compose up frontend
```

### Backend File Updates
```bash
# After updating backend Python files (.py)
docker-compose restart backend

# For database schema changes or major updates
docker-compose down
docker-compose up backend
```

### Full Stack Updates
```bash
# When updating both frontend and backend files
docker-compose restart

# For major changes or if issues persist
docker-compose down
docker-compose up
```

### Verification Steps After Updates
1. **Check container status**: `docker-compose ps`
2. **View logs for errors**: `docker-compose logs -f [service_name]`
3. **Run tests to verify functionality**:
   ```bash
   # Backend tests
   docker-compose exec backend python -m pytest
   
   # Frontend tests
   docker-compose exec frontend npm run test
   
   # Frontend linting
   docker-compose exec frontend npm run check
   ```
4. **Test API endpoints**:
   ```bash
   # Test backend API
   curl -X GET "http://0.0.0.0:10000/api/ranking?limit=5"

   # Test frontend access
   curl -X GET "http://0.0.0.0:3000"
   ```
5. **Frontend accessibility**: Open browser to `http://localhost:3000`
6. **Backend API docs**: Open browser to `http://localhost:10000/docs`

### Common Issues and Solutions
- **Frontend hot reload not working**: Restart frontend container
- **Backend changes not reflected**: Restart backend container
- **Database connection issues**: Check environment variables and restart backend
- **Port conflicts**: Use `docker-compose down` then `docker-compose up`
- **Build errors**: Check logs with `docker-compose logs [service_name]`

### Important Notes
- **Frontend**: Uses Next.js with hot reload - file changes are automatically reflected without restart
- **Backend**: Python code changes require container restart to take effect
- **Database**: Schema changes need backend restart and possibly manual migration
- **Environment variables**: Changes require full container restart

# CRITICAL TESTING WORKFLOW REQUIREMENTS

**MANDATORY: All code changes must follow this workflow:**

1. **Implementation**: Make the requested code changes
2. **Test Creation**: Create/update corresponding test files
   - Backend: `tests/` directory structure mirroring `src/`
   - Frontend: Co-located `*.test.ts` or `*.test.tsx` files
3. **Test Execution**: Verify all tests pass
   - Backend: `docker-compose exec backend python -m pytest`
   - Frontend: `docker-compose exec frontend npm run test`
4. **Code Quality**: Ensure lint checks pass (frontend only)
   - Frontend: `docker-compose exec frontend npm run check`
5. **Verification**: Confirm no regressions in existing functionality

**NO EXCEPTIONS**: This workflow must be followed for every code change, regardless of size.

# Frontend Development Critical Notes

## ⚠️ CRITICAL FRONTEND RULES

**NEVER run `npm run build` in development environment:**
- Frontend uses hot reload with automatic file watching
- Running `npm run build` breaks the development environment
- Simply save files to see changes automatically reflected
- Only use `npm run test` and `npm run check` for verification

**Development Workflow:**
1. Save files → Changes auto-reload immediately
2. Run tests: `docker-compose exec frontend npm run test`
3. Run linting: `docker-compose exec frontend npm run check`
4. NO BUILD STEP NEEDED - hot reload handles everything

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
