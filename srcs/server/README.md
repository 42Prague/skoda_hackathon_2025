# Employee Skills Analyzer Server

A professional Python server with separated business logic for analyzing employee data and providing intelligent skill suggestions. Built with Flask using modern architectural patterns (application factory + service layer) for scalability and maintainability.

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd srcs\server
pip install -r requirements.txt
```

### 2. Start the Server

```powershell
python run.py
```

Server default: http://localhost:5000
(Configure host/port in `config/settings.py`)

### 3. Test the API

```powershell
python test_api.py
```

## 📊 What This Server Does

Core features:
- Employee Management (CRUD, filtering)
- Skill Analysis (gap + trends + benchmarks)
- Smart Suggestions (multiple strategies)
- Team Compatibility & Risk Assessment
- Learning Path & Team Building Recommendations

Sample data is auto-loaded for quick experimentation.

## 🛠 API Endpoints (v1)

Base prefix: `/api/v1`

General:
- GET `/` – API root info
- GET `/health` – Basic health
- GET `/health/detailed` – System metrics (uses psutil)

Employees:
- GET `/api/v1/employees` – List (query params: department, position, min_experience)
- GET `/api/v1/employees/<id>` – Detail
- POST `/api/v1/employees` – Create
- PUT `/api/v1/employees/<id>` – Update
- DELETE `/api/v1/employees/<id>` – Remove
- POST `/api/v1/employees/<id>/skills` – Add skills (JSON: {"skills": [...]})
- DELETE `/api/v1/employees/<id>/skills/<skill>` – Remove a skill

Skills & Analysis:
- GET  `/api/v1/skills/suggestions/<id>` – Multi-category suggestions
- POST `/api/v1/skills/analyze/gap` – Gap analysis (JSON optional: {"department": "IT", "position": "Developer"})
- GET  `/api/v1/skills/trends?department=IT&limit=10` – Trending skills
- POST `/api/v1/skills/compatibility` – Team compatibility (JSON: {"employee_ids": [1,2,3]})
- GET  `/api/v1/skills/learning-path/<id>?target_position=Senior%20Developer` – Learning path
- GET  `/api/v1/skills/benchmarks?position=Developer` – Benchmarks (simplified placeholder)
- POST `/api/v1/skills/recommendations/team` – Team building (JSON: {"required_skills": ["python","sql"], "team_size": 4})

## 🔍 Example Usage (PowerShell / curl)

List employees:
```powershell
curl http://localhost:5000/api/v1/employees
```

Create employee:
```powershell
curl -X POST http://localhost:5000/api/v1/employees -H "Content-Type: application/json" -d '{
  "name": "John Smith", "position": "Data Scientist", "skills": ["Python","Machine Learning","SQL"], "experience_years": 3, "department": "Analytics"
}'
```

Get suggestions:
```powershell
curl http://localhost:5000/api/v1/skills/suggestions/1
```

Gap analysis (department IT):
```powershell
curl -X POST http://localhost:5000/api/v1/skills/analyze/gap -H "Content-Type: application/json" -d '{"department":"IT"}'
```

## 📁 Project Structure

```
srcs/server/
├── run.py                  # Entry point
├── app_factory.py          # Application factory
├── config/
│   ├── settings.py         # Global & env settings
├── api/                    # Route layer (HTTP only)
│   ├── routes.py
│   ├── employee_routes.py
│   ├── skill_routes.py
│   ├── health_routes.py
├── services/               # Business logic layer
│   ├── employee_service.py
│   ├── skill_service.py
├── models/                 # Data models
│   ├── employee.py
│   └── skill_analyzer.py   # Legacy/simple analyzer (optional)
├── utils/                  # Helpers & validation
│   ├── response_helpers.py
│   ├── validators.py
├── requirements.txt
├── test_api.py             # Demo tests
└── MIGRATION_GUIDE.md      # Simple -> Pro structure guide
```

## 🏗 Architecture Layers

- API (Blueprints): translate HTTP <-> service calls, no business logic.
- Services: reusable domain logic (analysis, suggestions, transformations).
- Models: data structures & simple behavior.
- Utils: cross-cutting helpers (responses, validation).
- Config: central configuration & environment toggles.

## 🤖 Suggestion Engine (SkillService)

Returns multiple categories:
- similar_roles: common skills among similar employees
- trending: frequently appearing new/department skills
- career_advancement: weighted by more experienced peers
- complementary: predefined semantic complements (e.g. python -> data science)
- priority_score: numeric importance indicator per skill

Extend easily by adding new private methods in `skill_service.py` and merging into the result.

## 📈 Gap & Risk Analysis

Gap levels: Low | Medium | High | Critical (based on coverage %)  
Risk levels: High if single holder or very low coverage.  
Recommendations auto-generated to highlight urgent training & mentoring targets.

## 🧪 Testing & Validation

Use `test_api.py` after server startup for a guided flow.  
Validation functions live in `utils/validators.py` (extend here for new fields).  
Responses standardized via `utils/response_helpers.py`.

## 🐛 Troubleshooting

- Import errors: ensure you run commands from `srcs/server` root.
- Port conflict: change `PORT` in `config/settings.py`.
- Missing module: `pip install -r requirements.txt`.
- psutil errors: ensure Windows build tools or use `pip install --upgrade pip wheel` first.

## 🔐 Common Extensions

Add persistence (example choices):
- SQLite / SQLAlchemy
- PostgreSQL
- MongoDB / Redis (for caching skill trends)

Add auth:
```powershell
pip install flask-jwt-extended
```
Integrate decorators at route layer.

Add background tasks (learning path generation):
- RQ / Celery / APScheduler

## 📝 Sample Suggestion Response

```json
{
  "success": true,
  "data": {
    "employee": {"employee_id": 1, "name": "John Doe", "position": "Software Developer"},
    "suggestions": {
      "similar_roles": {"skills": ["react","typescript"], "explanation": "Skills commonly found in similar positions"},
      "trending": {"skills": ["react","cloud computing"], "explanation": "Currently trending skills in your department"},
      "career_advancement": {"skills": ["architecture","leadership"], "explanation": "Skills that could accelerate career growth"},
      "complementary": {"skills": ["machine learning","django"], "explanation": "Skills that complement your existing expertise"}
    },
    "priority_score": {"react": 0.85, "architecture": 0.72}
  }
}
```

## 🧩 Adding New Features (Pattern)

1. Model change: update `models/employee.py`.
2. Validation: add to `utils/validators.py`.
3. Business logic: implement in `services/*.py`.
4. Endpoint: add route in `api/*_routes.py`.
5. Docs: update this README.

## 🧭 Migration Notes

Original monolithic `app.py` replaced by `run.py` + `app_factory.py`.  
Legacy `skill_analyzer.py` retained for reference; all new logic lives in `services/skill_service.py`.

## 🎉 Next Steps

- Adjust sample data to match real roles.
- Integrate persistence (DB) for hackathon scoring.
- Add metrics endpoint & logging.
- Enhance similarity with embedding models (future upgrade).

Happy building! 🚀
