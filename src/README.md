# Škoda AI Skill Coach — TeamSAC Delivery

## 1. Project Overview
Škoda AI Skill Coach is a full-stack workforce intelligence platform that TeamSAC built for the Škoda hackathon. It combines a FastAPI backend, a Postgres 15 data store, Azure OpenAI-powered reasoning, and a Vite/React front-end styled with Chakra UI to give three personas—**Managers**, **HR Business Partners (HRBP)**, and **Employees**—a real-time view of skills, risks, promotion readiness, and long-term career paths.  
Managers land on a capability overview and drill into skill risks or promotion pipelines, HRBPs get org-wide dashboards plus Azure-generated forecasts, and employees receive AI-personalised career paths. The system ingests raw HR XLSX/CSV files, normalises them into SQLModel tables (`EmployeeRecord`, `QualificationRecord`, `LearningHistory`, etc.), exposes both summary and detailed endpoints, caches expensive aggregates with a TTL cache, and drives the multi-persona UI through TanStack Query hooks.

## 2. Current Implementation (Feature List)
- **Team Capability Engine** – `TeamCapabilityService` computes six-dimensional capability vectors, levels, and gap narratives.
- **Skill Risk Radar** – `RiskRadarService` joins employee, qualification, and learning data to surface expired/expiring certifications, missing trainings, and severity-weighted risk scores.
- **Promotion Readiness Engine** – `PromotionReadinessService` batches qualifications and learning history to classify “Ready now / Ready soon / Developing”.
- **Career Path Engine (Azure)** – `CareerPathService` streams employee context into Azure OpenAI (with heuristic fallback) for top-three next roles and personalised recommendations.
- **Five-Year Skill Forecast (Azure)** – `ForecastService` aggregates skill distributions and prompts Azure OpenAI for emerging/declining skills, shortages, hiring, and training plans.
- **Multi-persona views** – Manager, HRBP, and Employee layouts share a `MainLayout` with a persistent `RoleSwitcher`.
- **Fully wired backend and frontend** – `frontend/src/src/hooks/useBackendEndpoints.ts` maps TanStack Query hooks to the FastAPI routes with shared unified responses.
- **Summary endpoints + full endpoints** – Each engine returns a `<feature>_summary` block along with detailed arrays; lightweight `/summary` variants are exposed for dashboards while the full routes serve the advanced pages.
- **Summary endpoints + full endpoints** – `GET /api/team/{team_id}/{engine}/summary` serves cached summary cards, and `GET /api/team/{team_id}/{engine}` streams full detail.
- **Lazy loading + progressive loading** – Pages render Chakra Skeletons, load summary blocks first via cached hooks, and fetch detailed tables/radars when navigated.
- **TTL caching for heavy routes** – `swx_api/app/utils/cache.py` provides a 60‑second namespace TTL cache that backs dashboard, analytics, and ontology routes.
- **Complete ingestion pipeline and data normalization** – `scripts/ingest_skoda_datasets.py` orchestrates discovery, schema inference, dependency-aware loading, and uses `SkodaDataAdapter` for multilingual normalisation.
- **Demo data flow (team SE, employee 9186)** – Hooks default to `DEMO_TEAM_ID='SE'` and `DEMO_EMPLOYEE_ID=9186`, matching the curated demo dataset.
- **Skeleton loaders and error handling** – Every wired page renders Chakra Skeletons/spinners and fallback alerts when hooks fail.

## 3. System Requirements
- **Python**: 3.10 – 3.12 (per `pyproject.toml`).
- **Node.js**: ≥ 20.x (Vite 6 and React 18 expect modern ESM tooling).
- **PostgreSQL**: 15.x (docker-compose pins `postgres:15-alpine`).
- **Docker / Docker Compose**: optional but recommended for parity.
- **Azure OpenAI**: Endpoint, API key, deployment name, and API version (2025-01-01-preview) for AI-backed endpoints.

## 4. Backend Setup
### 4.1 Create a virtual environment
```bash
cd /home/user001/PycharmProjects/skodaAuto/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

### 4.2 Environment variables
Copy `env.local.example` to `.env` (or export variables) and fill in at least:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL`, `SQLALCHEMY_DATABASE_URI`, `SQLALCHEMY_ASYNC_DATABASE_URI` | Point SQLModel/Alembic to Postgres |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Connection pieces used outside SQLAlchemy |
| `ENVIRONMENT`, `LOG_LEVEL`, `ROUTE_PREFIX` | FastAPI runtime and routing behaviour |
| `BACKEND_CORS_ORIGINS`, `BACKEND_HOST`, `FRONTEND_HOST` | Allowed origins and self-references |
| `SECRET_KEY`, `REFRESH_SECRET_KEY`, `DEMO_API_TOKEN` | Token-less demo but keys still required |
| `SKILL_LLM_PROVIDER` (`azure` for prod, `heuristic` for offline) | Controls which LLM client is used |
| `AI_FORCE_FALLBACK` | Must be `false` when `SKILL_LLM_PROVIDER=azure` (validated in `AppSettings`) |
| `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT_NAME`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_MODEL` | Required for Azure OpenAI calls |
| `FEATHERLESS_*`, `OPENAI_*`, `OLLAMA_*` | Optional alternate providers |
| `SENTRY_DSN`, `USE_TONE`, `SKODA_DATA_ROOT` | Observability and data path overrides |

> Azure configuration is validated at startup (`swx_api/app/config/settings.py`). If `SKILL_LLM_PROVIDER=azure`, the service aborts unless all Azure variables are present and `AI_FORCE_FALLBACK=false`.

### 4.3 Database migrations
```bash
cd /home/user001/PycharmProjects/skodaAuto/backend
alembic upgrade head
```
`alembic.ini` points at `SQLALCHEMY_DATABASE_URI`, so ensure the environment is loaded before running migrations.

### 4.4 Seed data / ingest XLSX files
1. Drop the Škoda datasets (e.g., `ERP_SK1.Start_month - SE.xlsx`, `Degreed.xlsx`, `ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx`) into `data/raw/skoda` (either under `/home/user001/PycharmProjects/skodaAuto/data/raw/skoda` for local runs or `/app/data/raw/skoda` inside Docker).
2. Execute the orchestrator:
   ```bash
   cd /home/user001/PycharmProjects/skodaAuto/backend
   python scripts/ingest_skoda_datasets.py
   ```
   The orchestrator discovers files, infers schemas, enforces ingestion order (org hierarchy → skills → qualifications → training → employees), and logs normalized CSVs into `backend/data/normalized`.
3. `EmployeeIngestionService` updates or creates `EmployeeRecord`s, deduplicates learning history via `(content_id, end_date)` pairs, and persists linked `QualificationRecord` and `LearningHistory` rows.

### 4.5 Run the backend (dev mode)
```bash
cd /home/user001/PycharmProjects/skodaAuto/backend
uvicorn swx_api.core.main:app --reload --host 0.0.0.0 --port 8000
```
The FastAPI app performs environment validation, starts the TTL cache refresher, and mounts static directories. To run the same server without reload (production-style), drop the `--reload` flag or use the Docker service defined in `docker-compose.yml`.

### 4.6 Backend folder structure (highlights)
```
backend/
├── swx_api/
│   ├── app/
│   │   ├── services/        # TeamCapabilityService, RiskRadarService, ForecastService, etc.
│   │   ├── routes/          # hackathon_routes.py, analytics_route.py, dashboard_route.py…
│   │   ├── models/          # SQLModel definitions (EmployeeRecord, QualificationRecord…)
│   │   └── utils/           # TTL cache, dependency wiring, unified responses
│   ├── core/                # FastAPI app bootstrap, router loader, middleware
│   └── scripts/             # Verification helpers, Azure integration tests
├── scripts/ingest_skoda_datasets.py
├── migrations/              # Alembic env + versions
└── data/                    # raw / normalized / processed datasets and logs
```

## 5. Frontend Setup
1. Install dependencies:
   ```bash
   cd /home/user001/PycharmProjects/skodaAuto/frontend
   npm install
   ```
2. Configure the API base URL by creating `frontend/.env` (or exporting) with:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   ```
3. Run Vite:
   ```bash
   npm run dev -- --host 0.0.0.0 --port 5173
   ```

### Frontend architecture
- **Routing**: `App.tsx` wraps all routes in `MainLayout` and enumerates persona pages: `/` (Manager capability), `/risk-radar`, `/promotion-readiness`, `/hrbp/dashboard`, `/hrbp/forecast`, `/employee/career`, `/assistant`, etc.
- **Role switcher**: `components/layout/RoleSwitcher.tsx` uses a Zustand store (`state/store.ts`) to persist the active persona and automatically navigates to its landing route (Manager → `/`, HRBP → `/hrbp/dashboard`, Employee → `/employee/career`).
- **TanStack Query integration**: `hooks/useBackendEndpoints.ts` defines `useCapability`, `useRiskRadar`, `usePromotionReadiness`, `useCareerPath`, and `useForecast`. Each hook:
  - Reads from `api/services/api.ts` (Axios client pointed at `VITE_API_BASE_URL`).
  - Uses a deterministic query key (e.g., `['team-capability', teamId]`).
  - Defaults to demo IDs (`DEMO_TEAM_ID='SE'`, `DEMO_EMPLOYEE_ID=9186`).
  - Configures retries, stale times, and automatic caching (so pages re-use data when switching personas).
- **Progressive loading**: Pages such as `TeamCapabilityDashboard.tsx` render Chakra Skeletons while hooks fetch, fall back to zeroed data, and display friendly alerts on errors. Other routes load lazily when navigated (e.g., promotion readiness and risk radar only fetch when their route is open).
- **Folder structure (excerpt)**:
  ```
  frontend/src/
  ├── App.tsx
  ├── index.css
  ├── src/
      ├── pages/
      │   ├── manager/ (TeamCapabilityDashboard, SkillRiskRadarPage, PromotionReadinessPage)
      │   ├── hrbp/ (OrgWideDashboard, FutureSkillForecast)
      │   └── employee/ (MyCareerDashboard)
      ├── components/ (layout + reusable cards, charts, skeletons)
      ├── hooks/ (TanStack Query wrappers)
      ├── services/api.ts
      ├── state/store.ts
      └── theme/index.ts
  ```

## 6. Data Ingestion Process
1. **Discovery & schema inference** – `SkodaIngestionOrchestrator` scans multiple candidate paths for `.xlsx/.csv/.json`, samples up to 100 rows via pandas, and tags each file as `employee_data`, `qualifications`, `training_history`, etc.
2. **Dependency-aware ingestion** – Files are loaded in this order: org hierarchy → skill mapping → qualifications → training/learning → employee data. Each ingest stores a normalized CSV in `backend/data/normalized`.
3. **Normalisation rules (`SkodaDataAdapter`)**:
   - Department resolution tries `pers_organization_branch`, `organization_branch`, `department`, org hierarchy levels (S1/S2), lookup tables, and any column containing “department”.
   - Skills are merged from explicit skill columns, comma/semicolon-delimited lists, completed courses (`derive_skills_from_courses`), and qualification names passed through the `MultilingualNormalizationService`.
   - OB codes, education fields, org hierarchy metadata, and job families are preserved in the `meta_data` JSONB column.
   - Learning history merges Degreed exports and course participation feeds; duplicates are removed by `(course_id, end_date)` keys.
4. **Qualification & learning ingestion** – `EmployeeIngestionService` caches team qualifications and learning records to avoid N+1 queries, persists them into `QualificationRecord` and `LearningHistory`, and links them back to each employee.
5. **Duplicate handling** – Employees are upserted (`update_existing=True`), learning history is deduped per employee, and dataset ingestion keeps a per-file `results` map so reruns skip already-normalized files.
6. **Storage tables**:
   - `EmployeeRecord` – main profile, normalized skills, metadata.
   - `QualificationRecord` – derived from Škoda qualification exports (44,412 rows after the last ingest).
   - `LearningHistory` – Degreed and course participation entries (37,204 records).
   - `OrgHierarchyRecord`, `HistoricalEmployeeSnapshot`, and `DatasetRecord` store lineage and aggregates.
7. **Before vs after (latest re-ingestion)**:

| Metric | Before fixes | After running `scripts/ingest_skoda_datasets.py` |
| --- | --- | --- |
| Employees loaded | 218 raw records with inconsistent metadata | 215 deduplicated `EmployeeRecord`s |
| Departments populated | 1.4% (most rows were `"Unknown"`) | 100% (215/215 assigned, demo data fixed to `SE`) |
| Employees with normalized skills | 3 employees (1.4%) had skills arrays | 206 employees (95.8%) have 42–90 skills each |
| Linked qualifications | Qualification lookups failed because services expected `emp_record.qualifications` | 44,412 `QualificationRecord`s linked through the adapter (per `DATABASE_CONTENTS.md`) |

Logs, summaries, and validation artefacts live under `backend/docs/` (e.g., `FINAL_INGESTION_REPORT.md`, `RE_INGESTION_SUCCESS.md`).

## 7. Architecture Diagram
```
[HR XLSX/CSV Feeds]
        │
        ▼
[Skoda Ingestion Orchestrator]
    ├─ discovers files & infers schema
    ├─ SkodaDataAdapter normalizes rows (dept, skills, OB, education)
    └─ EmployeeIngestionService upserts Employee/Qualification/Learning tables
        │
        ▼
[PostgreSQL 15 ← SQLModel tables]
        │
        ├─ TTL cache (global_cache, 60 s) for analytics/ontology summaries
        ├─ Feature services (Capability, Risk, Promotion, Career Path, Forecast)
        │       │
        │       └─ Azure OpenAI (career paths & 5Y forecast) via AI orchestrator
        │
        ▼
[FastAPI /api routes]
    ├─ Summary endpoints (cached) for dashboards
    └─ Full endpoints (live queries + AI) for drill-down pages
        │
        ▼
[React 18 + Vite UI]
    ├─ Role-aware layout (Manager / HRBP / Employee)
    └─ TanStack Query hooks → Chakra components, skeleton loaders, and charts
```

## 8. API Documentation
All endpoints return a unified response:
```json
{
  "success": true,
  "message": "…",
  "data": { ...payload... }
}
```

### 8.1 Summary endpoints (cached views)
> These routes call the same handlers as the full endpoints but return only the `<feature>_summary` section. They are cached aggressively via `global_cache` and used for hero cards/skeleton loaders.

| Endpoint | Inputs | Output snippet |
| --- | --- | --- |
| `GET /api/team/{team_id}/capability/summary` | `team_id` path parameter (department, demo uses `SE`) | `{ "capability_score": 72.5, "capability_level": 3, "capability_level_name": "Advanced", "team_summary": { "total_employees": 20, "critical_gaps": ["Kubernetes …"] } }` |
| `GET /api/team/{team_id}/risk-radar/summary` | `team_id` path parameter | `{ "risk_summary": { "employees_with_risks": 8, "risk_level": "medium", "critical_alerts_count": 3 }, "risk_distribution": { "critical": 2, "high": 3, "medium": 3, "low": 12 } }` |
| `GET /api/team/{team_id}/promotion-readiness/summary` | `team_id` path parameter, optional `target_job_family_id` query param | `{ "pipeline_summary": { "ready_now": 3, "ready_soon": 5, "developing": 12, "total_candidates": 20 }, "narrative": "…" }` |

### 8.2 Full endpoints (detailed payloads)
| Endpoint | Inputs | Response outline |
| --- | --- | --- |
| `GET /api/team/{team_id}/capability` | Path `team_id` (with fallback to `"Unknown"` if no dept matches). | Returns capability score, level, six-dimensional `capability_vector`, `skill_coverage` dictionary, skill strength stats, and `team_summary` (total employees, unique skills, top skills, `critical_gaps`). |
| `GET /api/team/{team_id}/risk-radar` | Path `team_id`. | Returns `risk_summary`, `risk_distribution`, and `employee_risks[]` with per-employee risk scores, counts, and alert lists (expired certifications, expiring soon, missing training, skill gaps). |
| `GET /api/team/{team_id}/promotion-readiness` | Path `team_id`, optional `target_job_family_id`. | Streams `pipeline_summary` plus `candidates[]` detailing readiness score, level, timelines, skill/qualification gaps, and metadata extracted from job families. |
| `GET /api/employee/{employee_id}/career-path` | Path `employee_id` (demo uses 9186). | Uses Azure OpenAI to generate `career_paths[]` (role name, readiness %, skill gaps, required trainings, timelines), `career_insights`, and `ai_generated` flag. Fallback heuristics run if Azure is disabled. |
| `GET /api/forecast/skills-5y` | Query `top_n` (5 ≤ n ≤ 50, default 20). | Returns `forecast_period`, `emerging_skills[]`, `declining_skills[]`, `skill_shortages[]`, `hiring_predictions[]`, `training_recommendations[]`, and `forecast_insights`, along with `ai_generated` metadata. |

All routes live in `backend/swx_api/app/routes/hackathon_routes.py` and depend on async repositories plus the feature services described earlier. Summary endpoints share the same implementations but short-circuit after the `<feature>_summary` extraction, so clients can opt for cached or full payloads depending on the view.

## 9. Current Limitations
- No authentication or RBAC; routes are deliberately open for demo purposes (`DEMO_API_TOKEN` is unused).
- Several experience/tenure fields fall back to defaults because the source data lacks reliable tenure columns; promotion readiness treats `experience_years` as 2.5 when missing.
- Job family datasets are absent, so promotion targets rely on heuristics and the few test job families seeded for demos.
- Historical snapshot tables exist but are not tapped by the live dashboards yet.
- Five-year forecasts lean on sparse historical skill trends, so predictions can drift without richer data.
- Career path and forecast endpoints block on Azure OpenAI latency; fallbacks are heuristic but less insightful.
- API responses are calibrated around the curated demo IDs (`team_id="SE"`, `employee_id=9186`); other IDs may return less compelling data until ingestion covers them.
- UI components show simplified values for some metadata (e.g., employee names default to IDs) because the backend payload lacks richer labels.
- No SAP or SuccessFactors connectors; ingestion currently expects flat files.
- There is no enterprise-grade audit logging/error tracking beyond basic Sentry integration; no centralized log shipping.
- Caching is purely in-process TTL (no Redis cluster), so cache misses occur after container restarts.

## 10. Known Issues
- First calls to heavy endpoints (forecast, promotion readiness) can take several seconds if the TTL cache is cold.
- Some normalization rules depend on Škoda-specific prefixes; new datasets with different column conventions require adapter updates.
- Azure forecast responses occasionally vary their JSON structure, so the frontend relies on defensive parsing and may show placeholders if a key changes.
- Promotion readiness heuristics assume consistent skill coverage and may over/under-estimate readiness without richer job-family data.
- UI tables/charts assume certain shapes (e.g., `skill_coverage` numbers). Unexpected nulls can break a specific widget until the fallback path is triggered.

## 11. How to Run the Full System
1. **Start Postgres** – Either run `docker compose up db` or start a local Postgres 15 instance with the credentials in `.env`.
2. **Start the backend** – Run migrations, ingest data, then launch `uvicorn swx_api.core.main:app --reload --port 8000`.
3. **Start the frontend** – `npm run dev -- --host 0.0.0.0 --port 5173` from `/home/user001/PycharmProjects/skodaAuto/frontend`.
4. **Verify endpoints** – Hit `http://localhost:8000/healthz`, then test `GET /api/team/SE/capability` and `/api/forecast/skills-5y` (curl or browser).
5. **Open the UI** – Visit `http://localhost:5173`, confirm the Manager dashboard renders, and check browser dev tools for successful API calls.
6. **Switch roles** – Use the top-right role switcher to flip between Manager, HRBP, and Employee personas; TanStack Query keeps responses cached so navigation is instant.
7. **Navigate personas** – Manager: `/`, `/risk-radar`, `/promotion-readiness`; HRBP: `/hrbp/dashboard`, `/hrbp/forecast`; Employee: `/employee/career`; Shared AI assistant: `/assistant`.

## 12. Demo Mode
- Defaults to `team_id="SE"` and `employee_id=9186` to guarantee rich data; these IDs are wired into the React hooks.
- Summary endpoints (or the summary sections of each payload) are fetched first to populate hero cards/skeleton loaders; detailed risk/promotion views load once the user navigates to those routes.
- Azure responses (career path and forecast) are cached per combination of parameters for 60 seconds, so repeated demos avoid extra latency.
- Because only a subset of datasets is required for the demo flow, ingestion can run in “minimal” mode (team SE + employee 9186) to keep disk usage low and produce reliable video demos.

## 13. Roadmap (What Comes Next)
- **RBAC & Auth** – Add proper identity, persona-specific scopes, and audit trails.
- **Succession engine** – Extend promotion readiness into full succession planning with vacancy forecasting.
- **Org-level shortages** – Introduce org-wide shortage indices and heatmaps built on aggregated skill gaps.
- **Skill decay modelling** – Track learning half-life and decay curves so capability scores account for recency.
- **SAP / SuccessFactors integration** – Replace manual XLSX ingestion with live connectors.
- **Skill decay modelling** – Track time-based proficiency loss to adjust capability scores (planned).

---
