# Deployment preparation (not deployed)

Target: one Docker application on AWS EC2 with a persistent SQLite Docker volume, behind Caddy HTTPS. The image serves React and FastAPI on one origin. This avoids putting a SQLite file on Vercel's ephemeral function filesystem. No cloud resources have been provisioned and no deployment credentials are needed by CI.

## Local container rehearsal

Install Docker, then run `docker compose up --build -d app`. Visit http://localhost:8000. SQLite lives in the named `draftwise-data` volume. `docker compose down` preserves it; **do not use `down -v`** unless intentionally discarding data. The Windows Python/Vite preview uses its separate `.data/draftwise.sqlite3` file.

Import reviewed observations inside the running container:

```sh
docker compose exec app python backend/scripts/import_onetricks.py backend/app/data/onetricks_reviewed.json
```

## EC2 steps for a later deployment

1. Provision an Ubuntu EC2 instance with enough memory to build the frontend (start with 2 GB), install Docker Engine and the Compose plugin. Attach persistent EBS storage and keep its delete-on-termination setting appropriate for your backup policy.
2. Clone the private GitHub repository using your account access. Do not bake GitHub credentials into the image.
3. Point a domain's DNS at the instance. Allow inbound HTTPS/HTTP on 443/80 and restrict SSH to your IP. Port 8000 is bound to loopback only.
4. Set `DOMAIN=your-domain.example` and `COOKIE_SECURE=true` in the server's root `.env`; run `docker compose --profile cloud up --build -d`. Caddy obtains the HTTPS certificate. Keep the app and proxy on the same Docker network.
5. Import reviewed observations, then verify health, save/load across a container restart, and all source labels through HTTPS.
6. Back up SQLite with its backup API to a separate durable destination. Copying only the main database file while WAL writes are active can lose data. Restore-test a backup before relying on it.

SQLite supports this single-instance course MVP. Multiple app instances require a shared database such as PostgreSQL and a proper migration plan. Anonymous saved drafts are scoped to an unguessable HttpOnly browser cookie; clearing it loses access. This is not account authentication or cross-device sync. Before public traffic, add abuse controls/rate limits and decide whether account login is needed.

## Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests: isolated backend tests, frontend formatting/build, deterministic Playwright flows, Docker build, and save/restart/load persistence smoke test. Tests disable external stats and paid AI. No auto-deploy workflow exists. A green CI run is evidence for the tested commit, not proof that a cloud deployment occurred.
