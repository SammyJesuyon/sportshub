# SportsHub Backend

FastAPI modular monolith for the SportsHub CS425 miniature. The backend lives as a sibling of `sportshub-frontend` in the root monorepo.

## Implemented API slice

- account registration, login, current-user bearer authentication;
- team search through a stable sports-provider adapter;
- public matchday fixtures grouped as live, half-time, full-time, or scheduled;
- authenticated team following with stable internal IDs;
- global notification preferences and idempotent Expo device registration;
- liveness and database-readiness endpoints.

The client never submits `userId` for self-service preference operations. Team following and notification settings remain separate transactions.

## Football provider

Set the backend-specific `sportshub-backend/.env` from `.env.example`:

```bash
SPORTS_PROVIDER=api-sports
API_SPORTS_KEY=your-key
API_SPORTS_BASE_URL=https://v3.football.api-sports.io
```

The [API-Football dashboard](https://dashboard.api-football.com/) manages the subscription and key; it is not used as the runtime API URL. Docker Compose reads this backend `.env` without exposing the key to the frontend.

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
