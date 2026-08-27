# SportsHub

SportsHub is a football matchday application built for CS425. It gives fans one place to browse fixtures in their local time, inspect match details, explore teams, build a personal team hub, and receive in-app alerts.

The repository is a Docker-ready monorepo with a React frontend, a FastAPI backend, and PostgreSQL persistence.

## What the demo shows

- Browse fixtures for today or another selected date, with pagination and local kickoff times.
- Open a fixture and move through overview, statistics, lineups, timeline, and chat tabs.
- Search for a team, review its profile and recent searches, then follow or remove it from My Hub.
- Register, sign in, and use protected team and alert pages.
- Review welcome and team-follow confirmations in a persistent inbox, including unread state and mark-all-read behavior.
- See a clear “more sports coming soon” boundary around the football-first release.

## Run the complete application

### Prerequisites

- Docker Desktop with Docker Compose
- Ports `5173`, `8010`, and `5432` available

From the repository root:

```bash
docker compose up --build
```

Once the health checks pass, open:

- Web application: <http://localhost:5173>
- API documentation: <http://localhost:8010/docs>
- API readiness check: <http://localhost:8010/health/ready>

The default configuration uses the built-in sample provider. To use live iSportsAPI data, create `sportshub-backend/.env` with your own values:

```dotenv
ENVIRONMENT=development
SECRET_KEY=replace-with-a-random-string-of-at-least-32-characters
SPORTS_PROVIDER=isports
ISPORTS_API_KEY=your-isports-api-key
ISPORTS_BASE_URL=https://api.isportsapi.com
ISPORTS_FALLBACK_BASE_URL=https://api2.isportsapi.com
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Do not commit that file. Docker Compose supplies the database connection and keeps provider cache data in named volumes.

Stop the stack with:

```bash
docker compose down
```

## Suggested demo route

1. Start on Home and change the matchday date to show date-scoped, locale-aware fixtures.
2. Open a fixture and walk through the detail tabs. Point out that Chat is deliberately marked as coming soon.
3. Search for a club in Explore Teams and open its profile.
4. Register or sign in, follow the club, view it in My Hub, and remove it again.
5. Open Alerts to show the unread badge, alert summary, individual read state, and mark-all-read action.

If the live provider is unavailable, the application keeps its shell usable and displays a provider status message instead of exposing credentials or quota details.

## Architecture

```text
React + Vite
    │  JSON over HTTP
    ▼
FastAPI endpoints
    ▼
Application services ───── iSportsAPI adapter + file cache
    ▼
Repository layer
    ▼
SQLAlchemy models + PostgreSQL
```

The API follows a controller-service-repository structure. Endpoints handle HTTP and authentication concerns, services own business rules, repositories isolate persistence, and Alembic manages the schema. Docker Compose starts the database, runs migrations, then starts the API and web application.

## Repository layout

```text
sportshub/
├── sportshub-backend/   FastAPI, SQLAlchemy, Alembic, and pytest
├── sportshub-frontend/  React, TypeScript, Vite, Vitest, and Playwright
├── docker/              PostgreSQL initialization support
├── docs/                Course artifacts and test plans
├── compose.yaml         Development and integration-test services
└── Makefile             Common run, build, and test commands
```

## Test the project

```bash
make test              # backend unit/API tests and frontend component tests
make test-web-quality  # lint and production frontend build
make test-e2e          # Playwright desktop and mobile browser journeys
make test-integration  # migrations and backend tests against PostgreSQL
docker compose config --quiet
```

Current local verification covers 46 backend tests, 8 frontend tests, two browser projects, and the same 46 backend tests against containerized PostgreSQL.

Detailed coverage and browser scenarios are recorded in [TEST_PLAN.md](docs/TEST_PLAN.md) and [WEB_PLAN.md](docs/WEB_PLAN.md).

## Course documentation

- [Use-case descriptions](docs/sportshub_usecase.pdf)
- [System architecture](docs/sportshub_architecture.pdf)
- [Sequence diagrams](docs/lab4_sequence_diagram.pdf)
- [Collaboration and VOPC diagrams](docs/SportsHub_Lab5.pdf)
- [Project presentation](docs/SportsHub_Project_Presentation.pptx)

The diagrams describe both the implemented foundation and the intended product direction. Features that are not part of the current executable release are listed below rather than presented as finished work.

## Current release boundaries

- Football is the only implemented sport.
- The chat tab is a placeholder; messaging is not implemented.
- Alerts are stored and displayed in the application. Push delivery is not part of the web demo.
- Pre-match, match-start, score, and full-time preferences are stored, but scheduled match-event alert generation is not implemented yet.
- Live SSE streaming and the independent fixture poller shown in the design artifacts are planned work.
- Official ticket discovery and affiliate redirects are planned work.
- Redis and cloud deployment are not included in the current development stack.
- Live match data requires an active iSportsAPI plan and API key with access to the requested endpoints.

## Security notes

- Passwords are hashed before storage.
- Protected endpoints derive the current user from an expiring bearer token.
- Administrative provider diagnostics require an administrator account.
- API keys, passwords, tokens, and local `.env` files are excluded from source control.
