# ŠKODA AI Skill Coach

A comprehensive AI-powered skill management and learning platform for ŠKODA Auto employees, featuring intelligent chatbots, analytics dashboards, and personalized learning recommendations.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Data Flow](#data-flow)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)

## 🎯 Overview

The ŠKODA AI Skill Coach is an enterprise-grade application designed to help employees manage their skills, track learning progress, and receive AI-powered recommendations for career development. The system combines:

- **RAG (Retrieval Augmented Generation)** chatbot for answering questions about courses, skills, and company information
- **Analytics dashboards** for visualizing employee skills, learning progress, and team capabilities
- **Document management** for indexing and searching company knowledge base
- **PKI card authentication** for secure employee access

## ⚡ Quick Reference

### Common Commands

```bash
# Build and start all services
docker-compose up -d --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Check service status
docker-compose ps

# Access services
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Quick Access URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Open WebUI**: http://localhost:3000
- **Adminer (DB Admin)**: http://localhost:8081
- **Skills Extractor API** (optional): http://localhost:8002
- **Neo4j Browser** (optional): http://localhost:7474

## 🏗️ Architecture

The application follows a microservices architecture with the following components:

### Backend Services

1. **FastAPI Backend** (`backend-fastapi/`)
   - RESTful API endpoints
   - RAG pipeline for intelligent document retrieval
   - Analytics data processing
   - Authentication and authorization

2. **PostgreSQL Database**
   - Stores employee data, skills, qualifications, learning history
   - Relational data for HR analytics

3. **DuckDB Database**
   - Analytical database for chat messages, document metadata, retrieval logs
   - Stored in MinIO for persistence
   - Optimized for analytical queries

4. **Qdrant Vector Database**
   - Multi-vector storage for embeddings
   - Named vectors: `text`, `chunk`, `image`, `profile`, `goal`
   - Semantic search for RAG

5. **MinIO Object Storage**
   - Stores document files (PDFs, JSON, etc.)
   - Stores DuckDB database backups
   - Stores Parquet exports

6. **Open WebUI** (Optional)
   - Proxy for OpenAI API calls
   - Alternative to direct OpenAI API usage

### Frontend

- **React Application** (`frontend/`)
  - Material-UI components
  - MUI X Charts for visualizations
  - React Router for navigation
  - Context API for state management

### Data Flow

1. **Document Processing Pipeline**:
   - Upload → MinIO (file storage)
   - Extract text → PDF/JSON parsing
   - Chunk text → 512-1024 token chunks
   - Generate embeddings → OpenAI or local model
   - Store vectors → Qdrant (multi-vector)
   - Store metadata → DuckDB

2. **Chat Pipeline**:
   - User query → Embedding generation
   - Vector search → Qdrant (similar messages + documents)
   - Retrieve full content → DuckDB
   - Context building → LLM prompt
   - Response generation → OpenAI/Open WebUI
   - Store conversation → DuckDB + Qdrant

3. **Analytics Pipeline**:
   - Query PostgreSQL → Employee/skill data
   - Data normalization → Czech/English skill mapping
   - Aggregation → Skill profiles, recommendations
   - JSON formatting → Frontend-ready data

## ✨ Features

### Chatbot
- **RAG-powered Q&A**: Answers questions using company knowledge base
- **Context-aware**: Retrieves relevant past conversations and documents
- **Multi-source retrieval**: Searches both chat history and document chunks
- **Markdown formatting**: Rich text responses with lists and formatting

### Analytics Dashboards
- **Employee Skill Profile**: Visualize individual skills, expertise levels, and expiring qualifications
- **Learning Recommendations**: AI-powered course suggestions based on skill gaps
- **Career Path Analysis**: Readiness scores and blocking skills for target positions
- **Team Heatmap**: Visualize team skill distribution across members
- **Company Skill Trends**: Track emerging and obsolete skills over time

### Document Management
- **Upload & Index**: Upload PDFs, JSON files, and text documents
- **Automatic Chunking**: Intelligent text chunking with page awareness
- **Vector Search**: Semantic search across all indexed documents
- **Batch Processing**: Process files directly from MinIO

### Authentication
- **PKI Card Login**: Secure authentication using card ID and PIN
- **Role-based Access**: Admin, HR, and User roles
- **Session Management**: Track user sessions and activity

## 🛠️ Technology Stack

### Backend
- **FastAPI** 0.104.1 - Modern Python web framework
- **LangChain** - LLM orchestration and RAG
- **OpenAI API** - GPT models and embeddings (or local alternatives)
- **Qdrant** - Vector database for embeddings
- **DuckDB** - Analytical database
- **PostgreSQL** - Relational database
- **MinIO** - S3-compatible object storage
- **SQLAlchemy** - Database ORM
- **Pandas** - Data processing

### Frontend
- **React** 18.2.0 - UI framework
- **Material-UI (MUI)** 5.14.20 - Component library
- **MUI X Charts** 7.0.0 - Data visualization
- **React Router** 7.9.6 - Navigation
- **Vite** 5.0.8 - Build tool

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Web server (frontend)

## 📁 Project Structure

```
hackathon-2025-skoda/
├── backend-fastapi/          # FastAPI backend application
│   ├── app/
│   │   ├── core/            # Core business logic
│   │   │   ├── chunking.py      # Text chunking utilities
│   │   │   ├── data_engine.py   # Analytics data processing
│   │   │   ├── database.py      # DuckDB management
│   │   │   ├── pdf_reader.py    # PDF text extraction
│   │   │   ├── storage.py       # MinIO operations
│   │   │   └── vector_store.py  # Qdrant operations
│   │   ├── routes/          # API endpoints
│   │   │   ├── analytics.py    # Analytics endpoints
│   │   │   ├── auth.py         # Authentication
│   │   │   ├── chatbot.py      # Chat endpoints
│   │   │   ├── documents.py    # Document management
│   │   │   └── health.py       # Health checks
│   │   └── main.py          # FastAPI app initialization
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── dashboards/      # Dashboard components
│   │   │   ├── AdminRoute.jsx
│   │   │   ├── Navbar.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── UserRoute.jsx
│   │   ├── context/         # React context
│   │   │   └── AuthContext.jsx
│   │   ├── pages/          # Page components
│   │   │   ├── ChatPage.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Home.jsx
│   │   │   ├── Login.jsx
│   │   │   └── UserManagement.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── scripts/                  # Utility scripts
│   ├── embed_course.py      # Course embedding script
│   ├── generate_synthetic_data.py
│   └── load_postgres.py     # PostgreSQL data loader
│
├── course_files/            # Course JSON files
├── synthetic_data/          # CSV data files
├── docker-compose.yml        # Docker Compose configuration
└── README.md                # This file
```

## 🚀 Getting Started

### Prerequisites

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **OpenAI API key** (or Open WebUI setup)
- **Git** (to clone the repository)

### Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd push1
   ```

2. **Create `.env` file** in the project root:
   ```bash
   cp .env.example .env  # If you have an example file
   # Or create manually (see Environment Variables section below)
   ```

3. **Build and start all services**:
   ```bash
   docker-compose up -d --build
   ```

4. **Check service status**:
   ```bash
   docker-compose ps
   ```

5. **Access the application** (see Ports section below)

### 📡 Ports and Services

The application uses the following ports:

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **Frontend** | `5173` | http://localhost:5173 | React application (Vite dev server) |
| **Backend API** | `8000` | http://localhost:8000 | FastAPI REST API |
| **API Documentation** | `8000` | http://localhost:8000/docs | Swagger UI |
| **API ReDoc** | `8000` | http://localhost:8000/redoc | ReDoc documentation |
| **PostgreSQL** | `5432` | `localhost:5432` | Database (internal use) |
| **MinIO API** | `9000` | http://localhost:9000 | Object storage API |
| **MinIO Console** | `9001` | http://localhost:9001 | MinIO web interface |
| **Qdrant API** | `6333` | http://localhost:6333 | Vector database API |
| **Qdrant Dashboard** | `6333` | http://localhost:6333/dashboard | Qdrant web UI |
| **Qdrant gRPC** | `6334` | `localhost:6334` | Qdrant gRPC (internal) |
| **Open WebUI** | `3000` | http://localhost:3000 | OpenAI proxy interface |
| **Adminer** | `8081` | http://localhost:8081 | Database management tool |
| **Skills Extractor API** | `8002` | http://localhost:8002 | Skills taxonomy API (optional) |
| **Neo4j Browser** | `7474` | http://localhost:7474 | Neo4j graph database UI (optional) |
| **Neo4j Bolt** | `7687` | `localhost:7687` | Neo4j database connection (optional) |

**Note**: Make sure these ports are not already in use on your system. Skills Extractor service is optional and runs separately.

### 🔧 Building the Application

#### Build All Services

```bash
# Build all Docker images
docker-compose build

# Build and start in detached mode
docker-compose up -d --build
```

#### Build Individual Services

```bash
# Build only backend
docker-compose build backend

# Build only frontend
docker-compose build frontend
```

#### Rebuild After Code Changes

```bash
# Rebuild and restart specific service
docker-compose up -d --build backend
docker-compose up -d --build frontend

# Or rebuild all
docker-compose up -d --build
```

### 🌐 Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_BASE_URL=http://open-webui:8080/api/v1  # Optional: use Open WebUI proxy

# Open WebUI (Optional - if using proxy)
OPEN_WEBUI_API_KEY=your_open_webui_api_key
WEBUI_SECRET_KEY=your_secret_key

# Database Configuration
POSTGRES_DB=skoda_user
POSTGRES_USER=skoda_user
POSTGRES_PASSWORD=skoda_password
DATABASE_URL=postgresql://skoda_user:skoda_password@postgres:5432/skoda_user

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Qdrant Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# DuckDB Configuration
DUCKDB_PATH=/app/data/chatbot.db

# Embeddings Configuration
USE_LOCAL_EMBEDDINGS=false
LOCAL_EMBEDDING_MODEL=all-mpnet-base-v2

# Data Directory (for data ingestion)
DATA_DIR=/path/to/your/dataset

# Debug
DEBUG_RAG=true
```

### 🏃 Running the Application

#### Start All Services

```bash
docker-compose up -d
```

#### Start Specific Services

```bash
# Start only infrastructure services
docker-compose up -d minio qdrant postgres

# Start backend and frontend
docker-compose up -d backend frontend
```

#### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

#### View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# View last 100 lines
docker-compose logs --tail=100 backend
```

#### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Initial Setup

After starting the services, perform these initial setup steps:

1. **Wait for services to be ready**:
   ```bash
   # Check all services are healthy
   docker-compose ps
   
   # Wait for backend to be ready (check logs)
   docker-compose logs -f backend
   # Press Ctrl+C when you see "Application startup complete"
   ```

2. **Load PostgreSQL data** (if you have data files):
   ```bash
   # Copy data files to backend container (if needed)
   docker cp synthetic_data/. skoda-chatbot-backend:/app/data/
   
   # Run data loading script
   docker-compose exec backend python scripts/load_postgres.py
   ```

3. **Upload course documents**:
   ```bash
   # Upload course JSON files
   curl -X POST "http://localhost:8000/api/upload" \
     -F "file=@course_files/SKODA-001_course.json"
   
   # Or upload multiple files
   for file in course_files/*.json; do
     curl -X POST "http://localhost:8000/api/upload" \
       -F "file=@$file"
   done
   ```

4. **Process files from MinIO** (if files already uploaded):
   ```bash
   curl -X POST "http://localhost:8000/api/process-from-minio?process_all=true"
   ```

5. **Verify setup**:
   ```bash
   # Check health endpoint
   curl http://localhost:8000/api/health
   
   # Check MinIO buckets
   curl http://localhost:8000/api/list-minio-files?bucket_name=documents
   ```

## 📚 API Documentation

### Authentication

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "card_id": "PKI-USER-001",
  "pin": "1234",
  "user_role": "user"
}
```

**Mock PKI Cards**:
- Admin: `PKI-ADMIN-001`, PIN: `0000`
- HR: `PKI-HR-001`, PIN: `1111`
- User: `PKI-USER-001`, PIN: `1234`
- User: `PKI-USER-002`, PIN: `2345`
- User: `PKI-USER-003`, PIN: `3456`

### Chatbot

#### Send Message
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What courses are available for Python programming?",
  "user_id": "PN-000001",
  "session_id": "optional-session-id",
  "use_context": true
}
```

#### Search Messages
```http
GET /api/search?query=python&limit=5&user_id=PN-000001
```

### Analytics

#### Get Employee Skill Profile
```http
GET /api/analytics/employee/{employee_id}/skill-profile
```

#### Get Learning Recommendations
```http
GET /api/analytics/employee/{employee_id}/learning-recommendations
```

#### Get Team Heatmap
```http
GET /api/analytics/team/{team_id}/heatmap?member_ids=PN-000001&member_ids=PN-000002
```

#### Get Position Readiness
```http
GET /api/analytics/employee/{employee_id}/position-readiness?target_role=Senior%20Developer
```

#### Get Company Skill Trends
```http
GET /api/analytics/company/skill-trends
```

### Documents

#### Upload Document
```http
POST /api/upload
Content-Type: multipart/form-data

file: <file>
user_id: optional-user-id
```

#### Process Files from MinIO
```http
POST /api/process-from-minio?bucket_name=documents&process_all=true
```

#### List MinIO Files
```http
GET /api/list-minio-files?bucket_name=documents&prefix=
```

#### Export to Parquet
```http
POST /api/export/parquet
```

## 🔄 Data Flow

### Document Indexing Flow

```
1. User uploads document
   ↓
2. File stored in MinIO
   ↓
3. Text extracted (PDF/JSON/Text)
   ↓
4. Text chunked (512-1024 tokens)
   ↓
5. Embeddings generated (OpenAI or local)
   ↓
6. Vectors stored in Qdrant (chunk vector)
   ↓
7. Metadata stored in DuckDB
```

### Chat Flow

```
1. User sends message
   ↓
2. Message stored in DuckDB
   ↓
3. Message embedding stored in Qdrant (text vector)
   ↓
4. Query embedding generated
   ↓
5. Vector search in Qdrant:
   - Similar messages (text vector)
   - Relevant documents (chunk vector)
   ↓
6. Full content retrieved from DuckDB
   ↓
7. Context built for LLM
   ↓
8. LLM generates response
   ↓
9. Response stored in DuckDB + Qdrant
```

### Analytics Flow

```
1. Frontend requests analytics data
   ↓
2. Backend queries PostgreSQL
   ↓
3. Data normalized (Czech/English skills)
   ↓
4. Business logic applied:
   - Skill gap analysis
   - Readiness calculations
   - Recommendation generation
   ↓
5. JSON formatted for frontend
   ↓
6. MUI X Charts visualization
```

## ⚙️ Configuration

### Multi-Vector Architecture

The system uses Qdrant's multi-vector architecture with named vectors:

- **`text`**: Chat messages and user queries
- **`chunk`**: Document chunks
- **`image`**: Image embeddings (future)
- **`profile`**: User profile embeddings (future)
- **`goal`**: Career goal embeddings (future)

### Embedding Models

**OpenAI** (default):
- Model: `text-embedding-3-large`
- Dimensions: 1536

**Local** (optional):
- Model: `all-mpnet-base-v2`
- Dimensions: 768
- Set `USE_LOCAL_EMBEDDINGS=true`

### Chunking Strategy

- **Size**: 512-1024 tokens per chunk
- **Overlap**: ~10% (50 tokens)
- **Page-aware**: PDFs chunked by pages when possible

## 🧪 Development

### Development Mode

The application runs in development mode by default with hot-reload enabled:

- **Backend**: Auto-reloads on code changes (via `--reload` flag)
- **Frontend**: Vite dev server with HMR (Hot Module Replacement)
- **Volumes**: Source code is mounted for live editing

### Backend Development

#### Option 1: Docker (Recommended)

The backend runs in Docker with volume mounting for live code changes:

```bash
# Backend code is mounted at ./backend-fastapi/app
# Changes are automatically reflected (with reload)
docker-compose logs -f backend
```

#### Option 2: Local Development

```bash
cd backend-fastapi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key
export DATABASE_URL=postgresql://skoda_user:skoda_password@localhost:5432/skoda_user
export MINIO_ENDPOINT=localhost:9000
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

#### Option 1: Docker (Recommended)

The frontend runs in Docker with volume mounting:

```bash
# Frontend code is mounted at ./frontend
# Changes are automatically reflected (Vite HMR)
docker-compose logs -f frontend
```

#### Option 2: Local Development

```bash
cd frontend

# Install dependencies
npm install

# Set API URL (if running backend locally)
export VITE_API_URL=http://localhost:8000

# Run dev server
npm run dev
```

**Note**: When running frontend locally, update `vite.config.js` proxy target to `http://localhost:8000` instead of `http://skoda-chatbot-backend:8000`.

### Skills Extractor Service (Optional)

The project includes a separate skills-extractor service for skill taxonomy management. This service runs independently from the main application:

```bash
cd skills-extractor

# Start Neo4j and skills-extractor API
docker-compose up -d

# Access services:
# - Neo4j Browser: http://localhost:7474
# - Skills API: http://localhost:8002
```

**Skills Extractor Ports**:
- Neo4j HTTP: `7474` - Graph database browser
- Neo4j Bolt: `7687` - Database connection protocol
- Skills API: `8002` - REST API for skill queries

### Running Tests

```bash
# Backend tests (if available)
cd backend-fastapi
pytest

# Frontend tests (if available)
cd frontend
npm test
```

### Code Style

- **Backend**: Follow PEP 8, use type hints
- **Frontend**: ESLint + Prettier configured

### Troubleshooting

#### Port Already in Use

If a port is already in use, you can change it in `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "3000:5173"  # Change host port from 5173 to 3000
```

#### Services Not Starting

1. Check Docker is running: `docker ps`
2. Check logs: `docker-compose logs <service-name>`
3. Check port availability: `lsof -i :<port>` (macOS/Linux)
4. Rebuild containers: `docker-compose up -d --build --force-recreate`

#### Database Connection Issues

- Ensure PostgreSQL is healthy: `docker-compose ps postgres`
- Check connection string in `.env` file
- Verify network: `docker network ls` and `docker network inspect push1_skoda-network`

## 🚢 Deployment

### Production Build

#### Frontend Production Build

The frontend Dockerfile includes a commented production stage. To build for production:

1. **Uncomment production stages** in `frontend/Dockerfile`:
   ```dockerfile
   # Uncomment the build-prod and nginx stages
   ```

2. **Build production image**:
   ```bash
   cd frontend
   docker build -t skoda-ui:prod --target build-prod .
   ```

3. **Or use multi-stage build**:
   ```bash
   docker build -t skoda-ui:prod .
   ```

#### Backend Production Build

```bash
# Build backend production image
docker-compose build backend

# Or build without cache
docker-compose build --no-cache backend
```

#### Production Docker Compose

Create a `docker-compose.prod.yml` file:

```yaml
version: '3.8'

services:
  frontend:
    build:
      target: build-prod  # Use production stage
    ports:
      - "80:80"  # Standard HTTP port
    environment:
      - VITE_API_URL=https://api.yourdomain.com
    restart: always

  backend:
    environment:
      - DEBUG_RAG=false
    restart: always
    # Remove --reload flag in production
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Then run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Production Considerations

1. **Environment Variables**: 
   - Use secrets management (Docker secrets, Kubernetes secrets, etc.)
   - Never commit `.env` files to version control
   - Use different keys for production

2. **Security**:
   - Configure CORS with specific allowed origins (not `*`)
   - Enable HTTPS/SSL/TLS
   - Use strong passwords for databases
   - Enable authentication for MinIO console
   - Secure API endpoints with rate limiting

3. **Database Backups**: 
   - Regular DuckDB syncs to MinIO (automatic on shutdown)
   - PostgreSQL: Set up automated backups
   - Qdrant: Backup volumes regularly
   - MinIO: Configure backup to S3 or other storage

4. **Monitoring**: 
   - Add health checks (already configured)
   - Set up logging aggregation
   - Monitor resource usage
   - Set up alerts for service failures

5. **Scaling**: 
   - Consider horizontal scaling for backend
   - Use load balancer for multiple backend instances
   - Configure Qdrant clustering for high availability

6. **Performance**:
   - Use production-grade database connections
   - Enable connection pooling
   - Configure appropriate worker counts
   - Cache frequently accessed data

### Backup Strategy

- **DuckDB**: Automatically synced to MinIO on shutdown
- **PostgreSQL**: Use `pg_dump` or automated backup tools
- **Qdrant**: Backup volumes regularly (`docker cp` or volume backup)
- **MinIO**: Configure MinIO backup to S3 or other storage
- **Application Data**: Regular backups of mounted volumes

### Health Checks

All services include health checks. Monitor with:

```bash
# Check service health
docker-compose ps

# Manual health check
curl http://localhost:8000/api/health
```

## 📊 Database Schemas

### DuckDB Tables

- **`messages`**: Chat messages with token counts
- **`documents`**: Document metadata
- **`chunks`**: Document chunk metadata
- **`analytics_events`**: Analytics event tracking
- **`retrieval_logs`**: RAG retrieval operation logs

### PostgreSQL Tables

- **`employees`**: Employee information
- **`skill_mapping`**: Employee skills
- **`doklad_kvalifikace_komplet`**: Qualifications
- **`degreed_data`**: Learning activity
- **`degreed_catalog`**: Learning content catalog
- **`pki_cards`**: PKI authentication cards
- **`testovani_pisemne_dovednosti`**: Test results

## 🔒 Security

- **PKI Card Authentication**: Secure card-based login
- **PIN Hashing**: SHA-256 (production: use bcrypt)
- **Role-based Access Control**: Admin, HR, User roles
- **CORS Configuration**: Configure allowed origins
- **API Key Protection**: Environment variables only

## 📝 License

This project is developed for ŠKODA Auto hackathon 2025.

## 🤝 Contributing

This is a hackathon project. For production use, consider:
- Adding comprehensive tests
- Implementing proper error handling
- Adding monitoring and logging
- Security audit and hardening
- Performance optimization
- Documentation improvements

## 📞 Support

For issues or questions, please refer to the project documentation or contact the development team.

---

**Built with ❤️ for ŠKODA Auto**

