# AI Skill Coach - Škoda Auto Hackathon

> AI-powered career development tool for Škoda Auto employees. Helps employees identify skill gaps and generate personalized learning paths for their target roles.

## 🎯 Project Overview

The AI Skill Coach is a web application that:
- Displays employee skill and qualification profiles
- Analyzes gaps between current profile and target role requirements
- Generates AI-powered personalized learning plans
- Provides time estimates for skill development

## 🏗️ Architecture

### Frontend
- **Framework**: React + Vite
- **Styling**: Tailwind CSS with Škoda green theme
- **Components**: shadcn/ui

### Backend
- **Framework**: FastAPI
- **Data Processing**: pandas + openpyxl
- **AI Integration**: Azure GPT-4.1 compatible endpoint
- **API**: RESTful JSON endpoints

## 🚀 Quick Start

### Option 1: Docker (Recommended for Production)

**Fastest way to deploy - completely cloud-agnostic**

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# 2. Start with Docker Compose
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

**Access the application:**
- 🌐 **Frontend**: http://localhost
- 🔌 **Backend API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs

**Manage Docker containers:**
```bash
# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# Rebuild and restart after code changes
docker-compose up -d --build
```

### Option 2: Local Development (For Demo)

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- npm or yarn

### Easy Start

Use the provided scripts to start both servers:

```bash
# First time setup
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# Start both servers
./start.sh

# To stop servers
./stop.sh
```

### Manual Start

#### 1. Start the Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend will run on `http://localhost:8000`

#### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:5173`

### Configuration

#### Backend (.env)
```bash
cd backend
cp .env.example .env
# Edit .env to add LLM credentials (optional)
```

#### Frontend (.env)
Already configured to connect to `http://localhost:8000`

## 🎨 Features

### Employee Profile View
- Current skills with proficiency levels
- Active qualifications with validity dates
- Professional information

### Gap Analysis
- Missing skills identification
- Missing qualifications tracking
- Target role requirements comparison
- Role activity descriptions

### AI Learning Plan
- Personalized multi-phase learning path
- Course recommendations with duration
- Time-to-readiness estimation
- Structured progression from fundamentals to advanced

## 🔌 API Endpoints

- `GET /health` - Health check
- `GET /api/employees` - List all employees
- `GET /api/roles` - List all roles
- `GET /api/profile?personal_number=X` - Get employee profile
- `GET /api/gaps?personal_number=X&role_id=Y` - Get skill gaps
- `POST /api/ai-plan` - Generate AI learning plan

See `backend/README.md` for detailed API documentation.

## 💾 Data

The application supports real data from Excel files or mock data for development:

### Required Data Files (place in `backend/data/`)
- `ERP_SK1.Start_month - SE.xlsx` - Employee data
- `ZHRPD_VZD_STA_007.xlsx` - Course attendance
- `Skill_mapping.xlsx` - Skill mappings
- `ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx` - Qualifications
- `ZPE_KOM_KVAL.xlsx` - Required qualifications
- `Degreed.xlsx` + `Degreed_Content_Catalog.xlsx` - Degreed data

Without data files, the app uses mock data for demonstration.

## 🤖 AI Integration

The application uses an Azure GPT-4.1 compatible endpoint for generating learning plans. Configure in `backend/.env`:

```
LLM_API_BASE_URL=https://your-endpoint.openai.azure.com
LLM_API_KEY=your-key
LLM_DEPLOYMENT_NAME=hackathon-gpt-4.1
LLM_API_VERSION=2025-01-01-preview
```

Without LLM configuration, mock plans are generated.

## 🎨 Branding

- **Primary Color**: Škoda Green (#00985F / oklch(0.546 0.153 166.14))
- **Logo**: Škoda Auto logo in header
- **UI Theme**: Clean, professional with green accents