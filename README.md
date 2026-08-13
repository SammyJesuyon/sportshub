# SportsHub Monorepo

SportsHub is the CS425-sized sports engagement platform derived from LeagueBook. The school project controls scope; LeagueBook contributes proven implementation patterns without bringing its full feature set into this repository.

## Structure

```text
sportshub/
├── sportshub-backend/    FastAPI, SQLAlchemy and Alembic
├── sportshub-frontend/   React, TypeScript and Vite
├── docs/                 Test strategy and phased web roadmap
├── compose.yaml          Full development and integration stack
└── Makefile              Common workflows
```

## Start the full project

```bash
cp .env.example .env
cp sportshub-backend/.env.example sportshub-backend/.env
# Add API_SPORTS_KEY to sportshub-backend/.env
docker compose up --build
```

- Web: http://localhost:5173
- API: http://localhost:8010
- Swagger: http://localhost:8010/docs
- PostgreSQL: localhost:5432

The `migrate` service applies Alembic migrations before the API starts. Development data is stored in a named Docker volume.

## Tests

```bash
make test              # Fast backend and frontend tests
make test-integration  # Backend tests against PostgreSQL in Docker
docker compose config --quiet
docker compose build
```

Test layers:

1. Backend unit/API tests cover security, validation, stable team IDs, adding and removing team follows, the user-scoped in-app alert inbox, notification records, provider failure, readiness, and migrations.
2. Frontend component tests cover public rendering, route protection, account creation, authenticated team follow management, API authorization headers, alert summaries, and unread-count behavior.
3. Docker/PostgreSQL integration tests apply migrations to the isolated `sportshub_test` database and run the API suite against the real database engine.
4. Playwright is configured for desktop and mobile smoke tests. These expand as fixtures, SSE, tickets, and administration land.

The detailed acceptance matrix is in [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md).

## Web delivery plan

1. **Foundation:** responsive shell, authentication, team following, and a persisted in-app alert inbox with unread counts.
2. **Sports browsing (current):** locale-aware past and upcoming matchday browsing with shared UTC cache snapshots, local pagination and kickoff display, plus tabbed fixture overview, statistics, lineups, timeline, and a clearly inactive chat placeholder. Missing detail datasets use guarded provider-resource fallbacks above the quota safety floor. Public team exploration and authenticated team selection are separate journeys. Provider quota and cache telemetry are restricted to administrators. Standings and team pages follow next.
3. **Live match:** fixture detail, independent poller status, SSE connected/detail/update events, heartbeat, disconnect cleanup, and fresh-snapshot reconnect.
4. **Tickets:** Ticketmaster event results and backend `/events/{eventId}/buy` redirects with Impact/direct fallback.
5. **Administration:** role-protected user, competition, integration, and notification operations.
6. **Hardening:** accessibility audit, performance budgets, responsive visual regression, complete Playwright journeys, backup/restore drill, and production deployment configuration.

The milestone-level roadmap and definition of done are in [`docs/WEB_PLAN.md`](docs/WEB_PLAN.md).

Football is the first supported sport; the fan-facing home page clearly identifies more sports as coming soon without presenting them as available. Redis is intentionally deferred until live shared state needs it. The fixture Chat tab is a non-functional future-feature placeholder; chat implementation, gamification, predictions, wallets, commerce, subscriptions, payments, and fulfillment remain outside the current SportsHub release scope.
