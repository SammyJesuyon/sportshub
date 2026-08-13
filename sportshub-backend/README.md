# SportsHub Backend

FastAPI modular monolith for the SportsHub CS425 miniature. The backend lives as a sibling of `sportshub-frontend` in the root monorepo.

## Implemented API slice

- account registration, login, current-user bearer authentication;
- team search through a stable sports-provider adapter;
- authenticated team following with stable internal IDs;
- global notification preferences and idempotent Expo device registration;
- liveness and database-readiness endpoints.

The client never submits `userId` for self-service preference operations. Team following and notification settings remain separate transactions.

## Database

PostgreSQL is the development and production system of record. Alembic owns the schema:

```bash
alembic upgrade head
```

SQLite is used only by fast isolated tests. The root Docker Compose integration profile runs the backend test suite against PostgreSQL.

## Run and test

The preferred workflow is from the repository root:

```bash
docker compose up --build
make test
make test-integration
```

For direct backend tests:

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest
```
