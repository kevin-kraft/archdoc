# Docker API Base URL Resolution

Date: 2026-07-06

## Context

The Docker deployment serves the Docusaurus site through nginx on port `8088` and proxies backend calls through the same origin:

- `/api/*` -> `docs-backend:8010/api/*`
- `/health` -> `docs-backend:8010/health`

The frontend API resolver previously treated every `localhost` host as local development and returned `http://localhost:8010`. In Docker this made the browser bypass nginx and try to reach a host port that is not published by `docker-compose.yml`, producing browser-side `NetworkError when attempting to fetch resource`.

## Change

The frontend now uses `http://localhost:8010` only for the Docusaurus development server on `localhost:3000`. Docker and production-like deployments use relative URLs, allowing nginx to proxy `/api` and `/health` to the backend on the internal Docker network.

## Architectural Decision

Same-origin relative API calls are the default for deployed frontend builds. Cross-origin `localhost:8010` remains a development convenience only for `npm run start` on port `3000`, or when explicitly overridden through `window.ARCHDOC_API_BASE_URL`.

## Verification

Run:

```bash
npm run typecheck
npm run build
```

Expected Docker behavior after rebuilding images:

- `http://localhost:8088/health` returns backend health through nginx
- frontend table/API calls use `/api/...` on port `8088`
- no direct browser fetch to `http://localhost:8010` is required