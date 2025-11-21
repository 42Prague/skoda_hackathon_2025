# 🔥 FRONTEND UPGRADE REQUIREMENTS - Skill DNA Project

**Status:** Backend 100% complete, Frontend 30% complete
**Backend API:** http://localhost:8000 (fully functional)
**Frontend:** http://localhost:3000 or 3001 (Vite/React)
**GitHub Repo:** git@github.com:ezekaj/ai_skoda-11-2025.git

---

## ✅ WHAT'S WORKING (Backend - 100%)

### Backend API Endpoints (All Tested & Working):
```
GET  /api/genome?method=hierarchical           - D3 force-directed graph data
GET  /api/evolution                            - Time-series skill trends (2013-2025)
GET  /api/insights                             - Strategic insights (emerging/declining)
GET  /api/cluster/{cluster_id}                 - Individual cluster details
GET  /api/skill/{skill_name}                   - Individual skill analysis
GET  /api/gap-analysis                         - Skill gap analysis
GET  /api/network-analysis                     - Network analysis (hubs/bridges)
POST /api/upload-data                          - Multi-format CSV upload (5 formats)
GET  /api/supported-formats                    - Upload format documentation
GET  /api/translations/{language}              - EN/CZ translations
```

### ML Capabilities (All Functional):
- ✅ Multi-format CSV parser (5 different HR/LMS formats)
- ✅ Auto-format detection (60% column match threshold)
- ✅ Time-series forecasting (polynomial regression)
- ✅ Hierarchical clustering + DBSCAN
- ✅ UMAP dimensionality reduction
- ✅ Network analysis (PageRank, betweenness, communities)
- ✅ Skill growth rate calculation
- ✅ Mutation risk scoring
- ✅ Category health metrics
- ✅ EN/CZ bilingual support

---

## ❌ WHAT'S MISSING/BROKEN (Frontend - 30%)

### 🔴 CRITICAL FIXES NEEDED:

#### 1. **CORS Issue** (FIXED in backend, need to restart)
**Problem:** Frontend on port 3001, backend only allows 3000
**Fix:** Already added `http://localhost:3001` to CORS in `backend/api/main.py:38`
**Action:** Restart backend: `cd backend && python -m uvicorn api.main:app --port 8000 --reload`

#### 2. **Hardcoded Mock Data Instead of Real Backend Data**
**Files:** `App.tsx` uses `MOCK_GENOME_DATA`, `EVOLUTION_DATA`, `CLUSTER_INFOS` from `constants.ts`
**Problem:** Frontend shows fake data instead of real ML analysis
**Fix Needed:**
- Remove dependency on `constants.ts` mock data
- Fetch ALL data from backend on load
- Update Evolution view to use real `/api/evolution` data
- Replace hardcoded cluster cards with real `/api/insights` data

#### 3. **Missing Strategic Insights Dashboard**
**Problem:** Backend has comprehensive insights, frontend doesn't show them
**What Exists in Backend:**
- Top 10 emerging skills (with growth rates)
- Top 10 declining skills (with decline rates)
- Category health analysis (4 categories)
- Upskilling priorities (5 recommendations)
- Phase-out recommendations (5 skills to retire)
- Summary metrics (high-growth count, critical risks, thriving categories)

**What Frontend Needs:**
- New view: "INSIGHTS" tab (add to AppView enum)
- Component created: `components/InsightsDashboard.tsx` (already exists!)
- **Action Required:** Integrate `InsightsDashboard` into `App.tsx`

#### 4. **No Individual Skill Drill-Down**
**Problem:** User clicks skill in genome, sees basic info, but backend has detailed analysis
**Backend Provides:**
- Growth rate & trend classification
- 2-year forecast (polynomial regression)
- Mutation risk score (0-1)
- Similar skills (semantic embeddings)
- AI-generated insight

**Frontend Shows:**
- Only skill name and basic growth %
- No forecast chart
- No similar skills
- No mutation risk

**Fix Needed:**
- Enhance skill detail panel in Genome view
- Add forecast mini-chart (Recharts LineChart)
- Show mutation risk gauge
- Display similar skills list

#### 5. **Upload Component Missing Excel/PDF Support**
**Problem:** `DataUpload.tsx` accepts `.xlsx, .xls, .pdf` but backend needs `python-pptx` for Excel
**Fix:**
```bash
cd backend
pip install openpyxl python-pptx PyPDF2
```
**Backend:** Add Excel/PDF parsing to `multi_format_parser.py`

#### 6. **No Network Analysis Visualization**
**Problem:** Backend calculates hub skills, bridge skills, communities - frontend doesn't show
**Backend Provides:**
```json
{
  "hub_skills": ["Python", "Azure", "Docker"],  // High PageRank
  "bridge_skills": ["React", "Kubernetes"],      // High betweenness
  "communities": 4,
  "network_density": 0.23
}
```
**Fix Needed:**
- New component: `NetworkAnalysis.tsx`
- Show hub skills (most connected)
- Show bridge skills (critical connectors)
- Visualize skill communities

#### 7. **Evolution View Using Mock Data**
**Problem:** Evolution chart shows hardcoded trends from `constants.ts`
**Fix:**
- Fetch `/api/evolution` on mount
- Display real skill trends from uploaded data
- Add category filter (Legacy, Software, E-Mobility, AI)
- Add skill selection dropdown

---

## 🎯 PRIORITY FRONTEND UPGRADES (In Order):

### **PHASE 1: FIX CRITICAL ISSUES (1-2 hours)**
1. ✅ Fix CORS (restart backend with new config)
2. Replace mock data with real backend calls in `App.tsx`:
   ```typescript
   // Remove these:
   import { MOCK_GENOME_DATA, EVOLUTION_DATA, CLUSTER_INFOS } from './constants';

   // Use backend data instead:
   const [genomeData, setGenomeData] = useState(null);
   const [evolutionData, setEvolutionData] = useState(null);
   const [insights, setInsights] = useState(null);

   useEffect(() => {
     fetch('http://localhost:8000/api/genome?method=hierarchical')
       .then(r => r.json()).then(d => setGenomeData(d.data));
     fetch('http://localhost:8000/api/evolution')
       .then(r => r.json()).then(d => setEvolutionData(d.chart_data));
     fetch('http://localhost:8000/api/insights')
       .then(r => r.json()).then(d => setInsights(d.strategic_insights));
   }, []);
   ```

3. Update Evolution view cluster cards:
   ```typescript
   // Instead of CLUSTER_INFOS, use insights.category_health
   {Object.entries(insights?.category_health || {}).map(([name, data]) => (
     <div key={name} className="...">
       <div className="text-lg font-bold">{name}</div>
       <div className="text-sm">{data.health}</div>
       <div className="text-xs">Growth: {data.growth_rate}%</div>
     </div>
   ))}
   ```

### **PHASE 2: ADD INSIGHTS DASHBOARD (2-3 hours)**
4. Add INSIGHTS view to `types.ts`:
   ```typescript
   export enum AppView {
     GENOME = 'GENOME',
     EVOLUTION = 'EVOLUTION',
     INSIGHTS = 'INSIGHTS',  // ADD THIS
     MANAGER_AI = 'MANAGER_AI',
     UPLOAD = 'UPLOAD'
   }
   ```

5. Add INSIGHTS navigation button in `App.tsx`:
   ```typescript
   <button
     onClick={() => setActiveView(AppView.INSIGHTS)}
     className={`w-full flex items-center p-3 rounded-lg ...`}
   >
     <IconInsights />
     <span className="hidden lg:block ml-3">Strategic Insights</span>
   </button>
   ```

6. Import and render `InsightsDashboard`:
   ```typescript
   import { InsightsDashboard } from './components/InsightsDashboard';

   {activeView === AppView.INSIGHTS && (
     <div className="h-full overflow-y-auto">
       <InsightsDashboard />
     </div>
   )}
   ```

### **PHASE 3: ENHANCE SKILL DETAIL PANEL (2 hours)**
7. Expand skill detail panel to show:
   - Forecast chart (2-year prediction)
   - Mutation risk gauge
   - Similar skills list
   - Category badge

8. Fetch individual skill data:
   ```typescript
   const handleAnalyzeSkill = async (skillName: string) => {
     const response = await fetch(`http://localhost:8000/api/skill/${skillName}`);
     const data = await response.json();

     // data contains:
     // - growth_analysis: { growth_rate, current_popularity, trend }
     // - forecast: [{ year, predicted_popularity, confidence }]
     // - mutation_risk: 0.0-1.0
     // - similar_skills: ["skill1", "skill2", ...]
     // - ai_insight: "text description"
   };
   ```

### **PHASE 4: ADD NETWORK ANALYSIS (3 hours)**
9. Create `NetworkAnalysis.tsx` component
10. Fetch `/api/network-analysis`
11. Display:
    - Hub skills (ranked by PageRank)
    - Bridge skills (ranked by betweenness centrality)
    - Community detection results
    - Network density metrics

### **PHASE 5: POLISH & OPTIMIZATION (2 hours)**
12. Add loading states to all views
13. Add error boundaries
14. Improve mobile responsiveness
15. Add data refresh buttons
16. Add export functionality (download reports)

---

## 📊 BACKEND API RESPONSE EXAMPLES

### `/api/insights` Response:
```json
{
  "success": true,
  "strategic_insights": {
    "emerging_skills": [
      {
        "skill": "Machine Learning",
        "category": "AI/Emerging",
        "growth_rate": 25.4,
        "current_popularity": 45.2,
        "urgency": "high"
      }
    ],
    "declining_skills": [
      {
        "skill": "CATIA V5",
        "category": "Legacy Engineering",
        "decline_rate": -12.3,
        "current_popularity": 78.1,
        "risk_level": "critical"
      }
    ],
    "category_health": {
      "Legacy Engineering": {
        "growth_rate": -8.5,
        "current_avg_popularity": 65.3,
        "health": "declining",
        "skills_count": 12
      },
      "Software/Cloud": {
        "growth_rate": 15.2,
        "current_avg_popularity": 72.1,
        "health": "thriving",
        "skills_count": 18
      }
    },
    "upskilling_priorities": [
      {
        "skill": "Docker",
        "reason": "Explosive growth: +22.5%/year",
        "urgency": "high",
        "category": "Software/Cloud"
      }
    ],
    "summary": {
      "high_growth_skills": 15,
      "critical_risks": 8,
      "thriving_categories": 2
    }
  }
}
```

### `/api/skill/{skill_name}` Response:
```json
{
  "success": true,
  "skill": "Python",
  "growth_analysis": {
    "growth_rate": 18.7,
    "current_popularity": 85.3,
    "trend": "explosive"
  },
  "forecast": [
    { "year": 2026, "predicted_popularity": 92.1, "confidence": "medium" },
    { "year": 2027, "predicted_popularity": 98.5, "confidence": "medium" }
  ],
  "mutation_risk": 0.12,
  "similar_skills": ["JavaScript", "Java", "TypeScript", "Go"],
  "ai_insight": "Python shows explosive growth driven by AI/ML adoption..."
}
```

### `/api/network-analysis` Response:
```json
{
  "success": true,
  "network_insights": {
    "hub_skills": [
      { "skill": "Python", "pagerank": 0.085, "connections": 12 },
      { "skill": "Azure", "pagerank": 0.072, "connections": 9 }
    ],
    "bridge_skills": [
      { "skill": "React", "betweenness": 0.234, "role": "connects frontend to backend" }
    ],
    "communities_detected": 4,
    "network_density": 0.23,
    "avg_clustering_coefficient": 0.45
  }
}
```

---

## 🎨 DESIGN GUIDELINES

**Color Scheme (Keep Consistent):**
- Primary: Cyan (#06b6d4) - Software/Cloud
- Secondary: Purple (#8b5cf6) - AI/Emerging
- Accent: Green (#10b981) - E-Mobility
- Danger: Red (#ef4444) - Legacy/Declining
- Warning: Yellow (#eab308) - Caution
- Background: Dark slate (#0f172a, #1e293b)

**Typography:**
- Headers: `font-mono uppercase tracking-wide`
- Body: `font-sans text-slate-200`
- Metrics: `font-bold text-2xl` or `text-3xl`

**Component Style:**
- Cards: `bg-slate-900/50 border border-slate-800 rounded-lg p-6`
- Buttons: `px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded`
- Badges: Small colored pills for categories/urgency

---

## 🧪 TESTING CHECKLIST

### After Frontend Fixes:
1. ✅ CORS working (no console errors)
2. ✅ Genome loads real backend data
3. ✅ Evolution shows real trends from uploaded data
4. ✅ Insights dashboard displays all ML analysis
5. ✅ Upload works for CSV files
6. ✅ Skill detail panel shows forecast + risk
7. ✅ Network analysis view shows hubs/bridges
8. ✅ Language toggle works (EN/CZ)
9. ✅ All views responsive on mobile
10. ✅ No TypeScript errors (`npm run build` succeeds)

---

## 📁 KEY FILES TO MODIFY

### Must Edit:
- `App.tsx` - Remove mock data, add Insights view, integrate real backend
- `types.ts` - Add INSIGHTS to AppView enum
- `components/EvolutionChart.tsx` - Use real data instead of mock
- `components/GenomeGraph.tsx` - Enhance skill detail panel

### Already Created (Just Integrate):
- `components/InsightsDashboard.tsx` - Strategic insights dashboard (DONE)
- `components/DataUpload.tsx` - Upload system (DONE)
- `contexts/LanguageContext.tsx` - Translation system (DONE)

### Need to Create:
- `components/NetworkAnalysis.tsx` - Network visualization
- `components/SkillDetailPanel.tsx` - Enhanced skill drill-down
- `components/ForecastChart.tsx` - Mini forecast chart for skill panel

---

## 🚀 QUICK START COMMANDS

```bash
# Backend (Terminal 1)
cd backend
python -m uvicorn api.main:app --port 8000 --reload

# Frontend (Terminal 2)
npm run dev
# Opens on http://localhost:3000 (or 3001)

# Test API
curl http://localhost:8000/api/insights | jq
```

---

## 🎯 SUCCESS CRITERIA (100/100)

Frontend is "100% complete" when:
1. ✅ All 10 backend endpoints integrated
2. ✅ No hardcoded mock data (all from backend)
3. ✅ Strategic insights dashboard visible
4. ✅ Individual skill analysis detailed
5. ✅ Network analysis visualization
6. ✅ Upload works end-to-end (CSV → backend → refresh)
7. ✅ EN/CZ language switching functional
8. ✅ Mobile responsive
9. ✅ No console errors
10. ✅ `npm run build` succeeds

---

**Current Status:** 60/100
**With These Fixes:** 100/100

Good luck! 🚀
