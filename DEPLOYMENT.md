# Archdoc Docker Deployment

This package runs the Archdoc Docusaurus site and the review UI backend as two
containers:

- `docs-site`: static Docusaurus build served by Nginx
- `docs-backend`: FastAPI review backend on port `8010`

Nginx serves the frontend and proxies:

- `/api/*` to the backend
- `/health` to the backend

## Local Run

From `docs-site-docasaurus`:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8088
```

## Server Deployment

Build and run the same compose stack on the Linux server:

```bash
docker compose up -d --build
```

Expose `docs-site` through the server reverse proxy at:

```text
https://teamprojekt.docs.kevinkraft.de
```

The container listens on host port `8088` by default. Point Caddy/Nginx/Traefik
on the host to:

```text
http://127.0.0.1:8088
```

Example Caddy config:

```caddyfile
teamprojekt.docs.kevinkraft.de {
    encode zstd gzip
    reverse_proxy 127.0.0.1:8088
}
```

The same example is stored in:

```text
docker/Caddyfile.example
```

## Persistent Review State

The compose stack stores review UI state in the named volume:

```text
archdoc-review-data
```

This contains:

- `archdoc-review.sqlite3`
- `review-overlay.json`

Generated JSON files are intentionally not committed to the standalone docs
repository because they are large. Before building production images, CI/CD must
either regenerate or restore the generated Archdoc artifacts into:

```text
site/static/archdoc
```

The UI backend imports generated data from that directory. If it contains no
generated JSON files, the site still starts but catalog/review tables will be
empty.

When building from a checkout that also has access to the Utilis backend source,
regenerate Archdoc data before rebuilding the images:

```bash
archdoc scan -c archdoc.yml
archdoc map -c archdoc.yml
docker compose up -d --build
```

When building from a docs-only GitHub repository, restore the generated JSON
directory from a CI artifact, release asset, or server-side sync step before
running Docker build.
