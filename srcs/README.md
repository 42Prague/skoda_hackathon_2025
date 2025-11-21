# Talent Matching (FastAPI + React)

## Overview

- **frontend**: React + Vite dev server exposed on `http://localhost:5173`.
- **backend**: FastAPI service exposed on `http://localhost:3000`, serving the talent matching API.
- **data**: CSV datasets are mounted read-only; the SQLite database persists under `volumes/talent-db/`.
- **docker compose**: Builds both services and wires the shared volumes so the backend can initialise and update the talent database.

## Quick start

1. Build and start everything:

   ```bash
   docker compose up --build
   ```

2. Wait for the backend to download the sentence-transformer model during the first run.

3. Open the React app at `http://localhost:5173`. The UI will call the API directly (CORS enabled).

4. The API root is at `http://localhost:3000/api`. A quick health check is available at `http://localhost:3000/api/health`.

## Verifying the API from the frontend project

The frontend ships with a helper script that exercises the backend endpoints without needing a browser. Run it after the containers are up:

```bash
docker compose exec frontend npm run check-api
```

It calls `/api/health`, `/api/job-matches`, and `/api/training-plans`, printing a short summary of the returned data.

## Data persistence

- CSV seeds live under `data/` and are mounted into the backend container read-only.
- SQLite data is stored on the host inside `volumes/talent-db/` so runs are persistent between restarts.
