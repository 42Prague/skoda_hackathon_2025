# SkillBridge AI - AI Skill Coach Platform

![PR Checks](https://github.com/ayermeko/AI_Skoda_Hackathon/workflows/Pull%20Request%20Checks/badge.svg)

Internal Career Development Platform for Škoda - AI-powered skill development and career coaching.

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running

### Setup

```bash
# 1. Clone and navigate
git clone https://github.com/ayermeko/AI_Skoda_Hackathon.git
cd AI_Skoda_Hackathon

# 2. Configure environment (first time only)
cp backend/env.example backend/.env
# Edit backend/.env with your Azure OpenAI credentials

# 3. Start everything
make start

# 4. Open in browser
open http://localhost:8080
```

### Demo Login
- **Manager**: `karel.vagner@skoda.cz` / `password123`
- **Employee**: `martin.svoboda@skoda.cz` / `password123`

---

## 📋 Commands

```bash
make start         # Start all services
make stop          # Stop all services  
make restart       # Restart services
make logs          # View logs
make status        # Check status
make clean         # Remove everything
make help          # Show all commands
```

See **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** for complete reference.

---

## 🎯 Features

### For Employees
- Personal skills with proficiency levels
- AI-powered skill risk assessments
- Recommended career paths
- Course recommendations
- Progress tracking with AI feedback

### For Managers
- Team overview
- Skill gap analysis
- Employee profiles
- Data-driven decisions

---

## 📁 Project Structure

```
├── backend/                # Node.js + Express + Prisma
├── skillbridge-ai/         # React + TypeScript + Vite
├── fitness_prediction/     # Python AI prediction scripts
├── data/                   # CSV files (gitignored)
├── docker-compose.yml      # Docker configuration
└── Makefile               # Management commands
```

---

## 🔧 Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: Node.js, Express, Prisma
- **Database**: PostgreSQL
- **AI**: Azure OpenAI (GPT-4)
- **DevOps**: Docker, GitHub Actions

---

## 🔐 Configuration

Copy `backend/env.example` to `backend/.env` and configure:

```bash
# Database (configured in docker-compose.yml)
DATABASE_URL=postgresql://...

# Azure OpenAI (required for AI features)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

---

## 🐛 Troubleshooting

```bash
make logs          # Check errors
make restart       # Restart services
make clean         # Fresh start
```

---

## 📖 Documentation

- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - Command reference
- **[CI_CD.md](CI_CD.md)** - CI/CD pipeline
- **[fitness_prediction/README.md](fitness_prediction/README.md)** - Python scripts

---

**Developed for Škoda AI Hackathon 2025**
