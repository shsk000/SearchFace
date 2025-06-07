# SearchFace

Face recognition and similarity search application using Python FastAPI backend and Next.js frontend with Turso database.

## Quick Setup

1. **Database Setup (Required)**
   ```bash
   # Create .env file from sample
   cp .env.sample .env
   
   # Edit .env with your Turso credentials
   # TURSO_DATABASE_URL=libsql://your-database-name.turso.io
   # TURSO_AUTH_TOKEN=your-auth-token-here
   
   # Run database schema setup
   turso db shell your-database-name < database_schema.sql
   ```

2. **Start Application**
   ```bash
   docker-compose up
   ```

## Development Commands

```bash
source venv/bin/activate
```

# 検索エンジンの手動確認

https://programmablesearchengine.google.com/controlpanel/all

# 検索

curl -s "" |
curl -X POST "http://localhost:10000/api/search" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@-"

curl -X POST "http://localhost:10000/api/search" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@data/images/input.jpg"

# docker build

docker build -t searchface:latest .

# docker run

docker run -p 10000:10000 --name searchface searchface:latest

# install

pip install --use-pep517 -r requirements.txt