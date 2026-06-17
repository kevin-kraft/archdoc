# Dockerized Docs Site

## Context

The Archdoc review site needs to be runnable outside the local development
environment and deployable behind a server reverse proxy at
`teamprojekt.docs.kevinkraft.de`.

## Change

The docs-site package now includes a Docker Compose deployment with two
containers:

- `docs-site`: Docusaurus static build served by Nginx
- `docs-backend`: FastAPI review backend for catalog tables, overlays, user
  stories, and trace APIs

Nginx serves the static frontend and proxies:

- `/api/*` to the backend
- `/health` to the backend

The frontend API client now defaults to same-origin API calls in production,
while keeping `http://localhost:8010` as the local development fallback for
`localhost` and `127.0.0.1`.

Follow-up: table and graph API URLs now resolve relative same-origin paths
against `window.location.origin` before adding query parameters, so production
calls such as `/api/table/interfaces` work behind the Apache reverse proxy.

Persistent review state is stored in the named Docker volume
`archdoc-review-data`.

## Files Added

- `Dockerfile.frontend`
- `Dockerfile.backend`
- `docker-compose.yml`
- `docker/nginx.conf`
- `docker/Caddyfile.example`
- `.dockerignore`
- `DEPLOYMENT.md`

## Verification

- TypeScript compile for the Docusaurus site
- Python compile for the UI backend
- Docker Compose config/build could not be executed in this WSL environment
  because Docker is not installed or integrated with the distro
- Docusaurus production build could not be executed locally because the WSL
  Node.js version is `18.19.1`, while the site requires Node.js `>=20`; the
  Docker frontend build uses `node:22-alpine`
