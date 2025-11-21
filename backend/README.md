# Skill DNA Backend - Organizational Genome Analyzer

**AI/ML Backend for Škoda Auto Hackathon Project**

Real machine learning implementation with clustering, time-series forecasting, graph analysis, and LLM-powered insights.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd skill-dna-backend
pip install -r requirements.txt
```

### 2. Configure Environment (Optional for Demo)

```bash
cp .env.example .env
# Edit .env with Azure OpenAI credentials (provided at hackathon)
```

**Note**: The system works without Azure credentials using mock embeddings for demo purposes.

### 3. Run the API Server

```bash
# From skill-dna-backend/ directory
python -m uvicorn api.main:app --reload --port 8000
```

API will be available at: `http://localhost:8000`

### 4. Test the API

Visit: `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

---

## 📊 What Gets Generated

### Synthetic Škoda Data

Running the server automatically generates:

- **`data/employees.csv`** - 500 synthetic employees with skills, departments, hire dates
- **`data/skill_evolution.csv`** - Time-series data (2013-2025) showing skill popularity trends
- **`data/skill_matrix.csv`** - Binary matrix (employees × skills) for clustering

### Skill Categories

1. **Legacy Engineering** - CAD, Mechanical Design, CNC, CATIA, AutoCAD (declining trend)
2. **Software/Cloud** - Python, React, AWS, Docker, Kubernetes (rapid growth)
3. **E-Mobility** - Battery Systems, Electric Powertrain, Charging (explosive growth after 2018)
4. **AI/Emerging** - Machine Learning, TensorFlow, PyTorch, LLM Integration (explosive after 2022)

---

## 🧠 ML/AI Capabilities

### 1. Clustering (`ai/clustering.py`)

- **DBSCAN** - Density-based clustering, identifies outliers
- **Hierarchical Clustering** - Creates skill "species" (groups)
- **UMAP** - 2D dimensionality reduction for visualization
- **Network Analysis** - PageRank, betweenness centrality, community detection
- **Cluster Characteristics** - What makes each cluster unique

### 2. Time-Series Analysis (`ai/timeseries.py`)

- **Growth Rate Calculation** - Linear regression on recent trends
- **Skill Forecasting** - Polynomial regression for 2-year predictions
- **Mutation Detection** - Identifies rapidly emerging skills
- **Extinction Risk** - Identifies declining/obsolete skills
- **Category Health** - Legacy vs. emerging technology analysis

### 3. Semantic Embeddings (`ai/embeddings.py`)

- **Azure OpenAI Integration** - GPT-4o embeddings for skill vectors
- **Semantic Similarity** - Find related skills beyond co-occurrence
- **Skill Gap Analysis** - Intelligent matching (not just exact matches)
- **AI-Generated Insights** - Strategic recommendations from GPT-4o

---

## 🔌 API Endpoints

### Core Endpoints

- **`GET /api/genome`** - Genome visualization data (replaces mock data in frontend)
- **`GET /api/evolution`** - Evolution timeline + strategic insights
- **`GET /api/insights`** - Comprehensive strategic analysis
- **`GET /api/skill/{skill_name}`** - Deep dive on specific skill
- **`GET /api/cluster/{cluster_id}`** - Cluster characteristics
- **`POST /api/gap-analysis`** - Skill gap analysis for employees
- **`POST /api/analyze-cluster`** - Custom cluster analysis (for Manager AI)
- **`GET /api/network-analysis`** - Skill network graph analysis

### Example Requests

**Get Genome Data:**
```bash
curl http://localhost:8000/api/genome?method=hierarchical
```

**Analyze Specific Skill:**
```bash
curl http://localhost:8000/api/skill/Python
```

**Gap Analysis:**
```bash
curl -X POST http://localhost:8000/api/gap-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "required_skills": ["Python", "Machine Learning", "Docker"],
    "employee_skills": ["JavaScript", "React", "AWS"]
  }'
```

---

## 🎯 Integration with Frontend

### Replace Mock Data

The frontend (React app) currently uses hardcoded mock data in `constants.ts`. Replace with API calls:

**Before** (`constants.ts`):
```typescript
export const MOCK_GENOME_DATA = { ... }  // Hardcoded
```

**After** (fetch from API):
```typescript
const response = await fetch('http://localhost:8000/api/genome?method=hierarchical');
const data = await response.json();
const genomeData = data.data;
```

### Update Frontend Services

**`services/geminiService.ts`** → **`services/apiService.ts`**:

```typescript
export const analyzeSkillCluster = async (skills: string[]): Promise<string> => {
  const response = await fetch('http://localhost:8000/api/analyze-cluster', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(skills)
  });
  const data = await response.json();
  return JSON.stringify(data.analysis, null, 2);
};
```

---

## 🏆 Hackathon Scoring Impact

### Criterion: "USE OF AI/DATA LOGIC" (Highest Weight)

**What This Backend Provides:**

✅ **Real Machine Learning**
- DBSCAN & hierarchical clustering (not random grouping)
- UMAP dimensionality reduction (proper 2D projection)
- Time-series forecasting with polynomial regression
- Graph analysis with PageRank & community detection

✅ **Advanced Data Processing**
- Skill co-occurrence matrices
- Temporal trend analysis (12 years of data)
- Semantic embeddings via Azure GPT-4o
- Network centrality metrics

✅ **LLM Integration**
- Azure OpenAI GPT-4o for embeddings
- Semantic similarity (beyond keyword matching)
- AI-generated strategic insights
- Context-aware skill gap analysis

✅ **Strategic Intelligence**
- Mutation detection (emerging skills)
- Extinction risk scoring
- Category health assessment
- Data-driven training recommendations

**This demonstrates DEEP technical sophistication** - far beyond basic dashboards or simple chatbots.

---

## 📁 Project Structure

```
skill-dna-backend/
├── ai/
│   ├── clustering.py       # DBSCAN, hierarchical, UMAP, network analysis
│   ├── timeseries.py       # Forecasting, mutation detection, trends
│   └── embeddings.py       # Azure GPT-4o embeddings, semantic analysis
├── api/
│   └── main.py             # FastAPI server with all endpoints
├── data/
│   ├── synthetic_data.py   # Generates Škoda-like test data
│   ├── employees.csv       # Generated: 500 employees
│   ├── skill_evolution.csv # Generated: Time-series 2013-2025
│   └── skill_matrix.csv    # Generated: Employee × Skill matrix
├── requirements.txt        # Python dependencies
├── .env.example            # Azure config template
└── README.md               # This file
```

---

## 🧪 Testing

### Generate New Synthetic Data

```bash
python data/synthetic_data.py
```

### Test Clustering Module

```bash
python ai/clustering.py
```

### Test Time-Series Module

```bash
python ai/timeseries.py
```

### Test Embeddings Module

```bash
python ai/embeddings.py
```

---

## 🔧 Dependencies

- **fastapi** - Modern Python web framework
- **uvicorn** - ASGI server
- **pandas** - Data manipulation
- **numpy** - Numerical computing
- **scikit-learn** - ML algorithms (clustering, regression)
- **umap-learn** - Dimensionality reduction
- **networkx** - Graph analysis
- **openai** - Azure OpenAI integration
- **python-dotenv** - Environment variables

---

## 🎓 Key Concepts

### "Organizational Genome"

Treat company skill data like biological DNA:
- **Genes** = Individual skills
- **Chromosomes** = Skill clusters/categories
- **Mutations** = Emerging skills (AI, e-mobility)
- **Evolution** = Temporal skill trends
- **Species** = Employee segments with similar skill profiles

### Why This Wins

1. **Unique Metaphor** - Memorable, differentiates from generic dashboards
2. **Deep ML** - Real algorithms, not just visualization
3. **Strategic Value** - Actionable insights for HR decisions
4. **Technical Sophistication** - Scores maximum points on "AI/DATA LOGIC"
5. **Complete System** - Backend + Frontend + Real Data Processing

---

## 🚀 Next Steps (At Hackathon)

1. ✅ **Backend Complete** - All ML/AI modules working
2. ⏳ **Connect Frontend** - Replace mock data with API calls
3. ⏳ **Azure Integration** - Use provided GPT-4o endpoint
4. ⏳ **Real Data** - Load Škoda's actual employee dataset
5. ⏳ **Fine-tune** - Adjust clustering parameters for real data
6. ⏳ **Demo Prep** - Polish UI, prepare presentation

---

## 📞 API Documentation

Full interactive API docs available at: `http://localhost:8000/docs`

---

**Built for Škoda Auto Hackathon 2025**
**November 20-21, 2025 @ 42 Prague**
