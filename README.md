# Cinema backend

Backend for an online cinema: a Django admin panel for the film catalogue, an async FastAPI
content API backed by Elasticsearch and Redis, an ETL pipeline that keeps the search index in
sync with PostgreSQL, and a FastAPI auth service with JWT tokens and roles — all behind nginx
and running in Docker Compose.

**Stack:** Python · FastAPI · Django · PostgreSQL · Elasticsearch · Redis · nginx · Docker Compose · pytest · Alembic

---

## Quick start

Everything below runs the final, fully integrated system in [`07-full-system/`](07-full-system).

Requirements: Docker and Docker Compose.

```bash
git clone https://github.com/pickling-21/cinema-backend.git
cd cinema-backend/07-full-system
docker compose up -d
```

That starts PostgreSQL (seeded from `database_dump.sql`), Elasticsearch, Redis, the auth service,
the Django admin panel, the film API, the ETL worker and nginx on port 80. The ETL fills the
search index on its own within a few seconds of the first run.

Once the containers are healthy:

| What | URL |
| --- | --- |
| Film API docs | http://localhost/api/openapi |
| Films | http://localhost/api/v1/films/ |
| Auth (register / login / refresh / logout) | http://localhost/api/v1/auth/ |
| Roles | http://localhost/api/v1/roles/ |
| Django admin | http://localhost/admin/ |

Defaults for every secret are set in `docker-compose.yml`, so the stack comes up without any
configuration. To change them, export `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` and
`DJANGO_SECRET_KEY` before starting.

Create an admin user for the Django panel:

```bash
docker compose exec django python manage.py createsuperuser
```

Create a superuser for the auth service:

```bash
docker compose exec auth uv run python -m src.cli --login admin --password secret
```

Stop everything (add `-v` to drop the data volumes too):

```bash
docker compose down
```

### Tests

```bash
cd 07-full-system/auth && docker compose -f docker-compose.tests.yaml up --abort-on-container-exit
cd ../film_service && docker compose -f docker-compose.test.yaml up --abort-on-container-exit
```

---

## Repository structure

| Folder | What was built |
| --- | --- |
| [`01-admin-panel`](01-admin-panel) | PostgreSQL schema for the film catalogue, a Django admin panel, and a migration script moving the data from SQLite to PostgreSQL |
| [`02-docker-compose`](02-docker-compose) | The admin panel packaged into Docker Compose behind nginx and uWSGI, plus a read-only Django REST API and its OpenAPI spec |
| [`03-etl-elasticsearch`](03-etl-elasticsearch) | ETL pipeline PostgreSQL → Elasticsearch with state persistence, backoff on failures, and tests |
| [`04-async-api`](04-async-api) | First version of the async FastAPI content API — film, genre and person endpoints with Redis caching |
| [`05-async-api-final`](05-async-api-final) | The content API after a refactoring sprint towards SOLID, with the ETL and a functional test suite |
| [`06-auth-service`](06-auth-service) | Standalone auth service: FastAPI, JWT access/refresh tokens, a Redis token blacklist, roles, Alembic migrations and a CLI |
| [`07-full-system`](07-full-system) | Everything integrated: auth + admin panel + film service + ETL behind one nginx gateway. **Start here.** |

