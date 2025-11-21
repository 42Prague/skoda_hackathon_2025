This is a Vite + React single-page app configured for containerised development with hot reloading.

## Local development

```bash
docker compose up frontend
```

The container mounts the `frontend` directory, installs dependencies on boot, and exposes the dev server at http://localhost:5173.

Environment variables that need to be shipped to the browser must use the `VITE_` prefix. For example, the docker-compose file provides `VITE_API_BASE_URL` pointing at the backend.
