# Deployment Guide - Skill DNA Organizational Genome

## ✅ Frontend Deployment (COMPLETED)

**Platform**: Vercel
**Status**: ✅ DEPLOYED
**URL**: https://skill-dna-organizational-genome-utqig7dox-elvi-zekajs-projects.vercel.app

### What Was Deployed:
- ✅ React + TypeScript + Vite app
- ✅ Genome visualization with zoom functionality
- ✅ Evolution timeline charts
- ✅ Insights dashboard with ML analysis
- ✅ Network analysis (hub/bridge skills)
- ✅ Skill detail panels with forecasts
- ✅ Error boundaries for production stability

### Frontend Features:
1. **Genome View** - D3.js force-directed graph with zoom in/out
2. **Evolution View** - Time-series charts with category health
3. **Insights View** - Strategic ML insights + network topology
4. **Manager AI** - (requires backend)
5. **Upload View** - Excel/PDF/CSV upload (requires backend)

---

## ⏳ Backend Deployment (PENDING - Requires User Action)

**Platform**: Railway (recommended) or Render
**Status**: ⏳ READY TO DEPLOY (requires login)
**Files Ready**:
- ✅ `backend/Dockerfile` - Production container
- ✅ `backend/railway.json` - Railway configuration
- ✅ `backend/requirements.txt` - Python dependencies

### Deployment Steps (Railway):

1. **Login to Railway**:
   ```bash
   cd backend
   railway login
   ```
   This will open browser for authentication.

2. **Initialize Project**:
   ```bash
   railway init
   # Choose: Create new project
   # Name: skill-dna-backend
   ```

3. **Deploy**:
   ```bash
   railway up --detach
   ```

4. **Get Backend URL**:
   ```bash
   railway domain
   ```
   Example: `https://skill-dna-backend-production.up.railway.app`

5. **Update Frontend Environment Variable**:
   - Go to Vercel dashboard: https://vercel.com/elvi-zekajs-projects/skill-dna-organizational-genome
   - Settings → Environment Variables
   - Add: `VITE_API_URL` = `https://your-backend-url.railway.app`
   - Redeploy frontend: `vercel --prod`

### Alternative: Render Deployment

1. **Go to**: https://dashboard.render.com/
2. **New → Web Service**
3. **Connect GitHub**: `ezekaj/ai_skoda-11-2025`
4. **Settings**:
   - Name: `skill-dna-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - Plan: Free
5. **Click Create Web Service**

---

## 🧪 Testing Deployment

### 1. Test Frontend (Already Live):
```bash
curl https://skill-dna-organizational-genome-utqig7dox-elvi-zekajs-projects.vercel.app
```
Expected: HTML page loads

### 2. Test Backend (After Deployment):
```bash
# Replace with your Railway/Render URL
curl https://your-backend-url/api/genome?method=hierarchical
```
Expected: JSON with skills data

### 3. Test Excel Upload:
1. Go to deployed frontend URL
2. Navigate to UPLOAD tab
3. Upload `test_data/test_lms_cz.csv` or any Excel file
4. Should see success message and data processing

---

## 📊 What to Test in Production

### Critical Features:
1. ✅ **Genome visualization loads** with real ML data
2. ✅ **Zoom in/out works** on genome graph
3. ✅ **Evolution charts show** time-series data
4. ✅ **Insights dashboard displays** strategic analysis
5. ⏳ **Network analysis** (fix 500 error first)
6. ⏳ **Excel/PDF upload** (primary test target)

### Known Issues to Verify:
1. **Network Analysis Endpoint** - Currently returns 500 errors
   - File: `backend/api/main.py` line ~200
   - Check: Graph building logic in network analysis

2. **Excel Upload Parser** - Field count mismatches
   - File: `backend/parsers/multi_format_parser.py`
   - Dependencies: openpyxl, python-pptx, PyPDF2 (all installed)

---

## 🔧 Environment Variables

### Frontend (.env):
```
VITE_API_URL=https://your-backend-url.railway.app
```

### Backend (Railway/Render):
```
PORT=8000  # Auto-set by Railway/Render
PYTHONUNBUFFERED=1
```

---

## 📁 Project Structure

```
skill-dna---organizational-genome/
├── components/          # React components
│   ├── GenomeGraph.tsx  # Force-directed graph with zoom
│   ├── InsightsDashboard.tsx
│   ├── NetworkAnalysis.tsx
│   ├── SkillDetailPanel.tsx
│   ├── ForecastChart.tsx
│   └── ErrorBoundary.tsx
├── backend/
│   ├── api/main.py      # FastAPI endpoints
│   ├── ai/clustering.py # ML clustering logic
│   ├── ai/timeseries.py # Evolution forecasts
│   ├── parsers/         # Excel/CSV/PDF parsers
│   ├── Dockerfile       # Production container
│   └── requirements.txt # Python deps
├── Dockerfile           # Frontend container
└── vercel.json          # Vercel config
```

---

## 🚀 Quick Commands

### Local Development:
```bash
# Frontend
npm run dev  # http://localhost:3001

# Backend
cd backend
python -m uvicorn api.main:app --port 8000 --reload
```

### Production Deployment:
```bash
# Frontend (Already Done)
vercel --prod --yes --name skill-dna-organizational-genome

# Backend (Pending)
cd backend
railway login
railway init
railway up --detach
railway domain  # Get URL
```

### Redeploy:
```bash
# Frontend
vercel --prod

# Backend
cd backend
railway up
```

---

## ✅ Deployment Checklist

- [x] Frontend deployed to Vercel
- [x] Zoom functionality integrated from sena-frontend branch
- [x] All changes committed and pushed to GitHub
- [x] Vercel config created (vercel.json)
- [x] Railway config created (railway.json)
- [x] Dockerfiles ready for both frontend/backend
- [ ] Backend deployed to Railway/Render (requires user login)
- [ ] Environment variables configured
- [ ] Excel/PDF upload tested in production
- [ ] Network analysis endpoint fixed

---

## 🎯 Next Steps (User Action Required)

1. **Deploy Backend**:
   - Login to Railway: `railway login`
   - Initialize: `railway init`
   - Deploy: `railway up`

2. **Update Frontend Environment**:
   - Add backend URL to Vercel env vars
   - Redeploy frontend

3. **Test Excel Upload**:
   - Upload test files from `test_data/`
   - Verify parsing works in production

4. **Monitor & Fix**:
   - Check Railway logs for errors
   - Fix network analysis 500 errors
   - Verify all API endpoints respond

---

**Created**: 2025-11-20
**Frontend URL**: https://skill-dna-organizational-genome-utqig7dox-elvi-zekajs-projects.vercel.app
**GitHub**: https://github.com/ezekaj/ai_skoda-11-2025
