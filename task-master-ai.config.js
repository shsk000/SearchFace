const config = {
  // Project Information
  projectName: "SearchFace",
  projectDescription: "Face recognition and similarity search application built with Python FastAPI backend and Next.js frontend",
  
  // Development Environment
  environment: "development",
  
  // Available Commands for the project
  commands: {
    // Docker Development Commands
    "start": "docker-compose up",
    "start-detached": "docker-compose up -d",
    "stop": "docker-compose down",
    "logs": "docker-compose logs -f",
    "restart": "docker-compose restart",
    
    // Backend Commands (via Docker)
    "backend-shell": "docker-compose exec backend bash",
    "backend-sync-db": "docker-compose exec backend python src/run_api.py --sync-db",
    "backend-test": "docker-compose exec backend python -m pytest",
    "backend-start": "docker-compose up backend",
    
    // Frontend Commands (via Docker)
    "frontend-shell": "docker-compose exec frontend bash",
    "frontend-format": "docker-compose exec frontend npm run format",
    "frontend-lint": "docker-compose exec frontend npm run lint",
    "frontend-check": "docker-compose exec frontend npm run check",
    "frontend-test": "docker-compose exec frontend npm run test",
    "frontend-test-ui": "docker-compose exec frontend npm run test:ui",
    "frontend-start": "docker-compose up frontend",
    
    // Full Development Workflow
    "dev": "docker-compose up",
    "test-all": "docker-compose exec backend python -m pytest && docker-compose exec frontend npm run test",
    "check-quality": "docker-compose exec frontend npm run check",
    
    // API Testing
    "test-api": "curl -X GET 'http://localhost:10000/api/ranking?limit=5'"
  },
  
  // Development Workflow
  workflow: [
    "start development environment with: npm run start or docker-compose up",
    "make code changes (hot reload enabled for both frontend and backend)",
    "run tests: npm run test-all",
    "check code quality: npm run check-quality",
    "frontend changes are auto-reloaded, backend needs restart for changes"
  ],
  
  // Important Notes
  notes: [
    "This project runs in Docker containers - all commands should be executed via docker-compose",
    "Frontend uses hot reload - no build step needed in development",
    "Backend changes require container restart",
    "Never run 'npm run build' in development - it breaks hot reload",
    "All development commands are defined in CLAUDE.md",
    "Follow testing workflow: Implementation -> Test Creation -> Test Execution -> Code Quality Check"
  ],
  
  // File Structure
  structure: {
    backend: "src/",
    frontend: "frontend/src/",
    tests: {
      backend: "tests/",
      frontend: "frontend/src/ (co-located with source files)"
    },
    docker: {
      compose: "docker-compose.yml",
      backend: "Dockerfile",
      frontend: "frontend/Dockerfile"
    },
    config: {
      rules: ".cursor/rules/",
      docs: "CLAUDE.md"
    }
  },
  
  // Technology Stack
  stack: {
    backend: ["Python", "FastAPI", "face_recognition", "FAISS", "SQLite", "Turso", "Cloudflare R2"],
    frontend: ["Next.js 15", "React 19", "TypeScript", "Tailwind CSS", "Radix UI"],
    testing: ["pytest (Backend)", "vitest + React Testing Library + MSW (Frontend)"],
    tools: ["Docker", "docker-compose", "Biome (formatting/linting)"]
  },
  
  // Port Configuration
  ports: {
    backend: 10000,
    frontend: 3000
  }
};

module.exports = config;