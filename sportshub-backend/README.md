# SportsHub API

The SportsHub API is a FastAPI service for football fixtures, team discovery, authentication, account management, user team preferences, and the in-app alert inbox. PostgreSQL is the system of record, SQLAlchemy handles persistence, and Alembic owns schema changes.

## Start the API

The recommended path is to start the complete stack from the repository root:

```bash
docker compose up --build
```

The API is then available at <http://localhost:8010>, with interactive documentation at <http://localhost:8010/docs>.

For live provider data, create `sportshub-backend/.env` and add the configuration described in the root README. The file is intentionally local and must not be committed.

The live adapter uses iSportsAPI behind the same internal provider contract as the sample data source. Current UTC matchdays come from the livescore feed; other dates use the schedule feed; fixture details combine the event, statistics, and lineup feeds when those resources are available. Responses are normalized before they reach the API layer and cached by matchday, fixture, team, and search query. The adapter also retries the documented secondary iSportsAPI host after a network or gateway failure.

### Run without Docker

Use Python 3.12 or newer and a running PostgreSQL database:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8010
```

Set `DATABASE_URL` and any provider settings in your shell or in a local `.env` before starting the process.

## API surface

All application routes are versioned under `/api/v1`.

| Area | Method and path | Purpose |
| --- | --- | --- |
| Authentication | `POST /auth/register` | Create an account and issue a bearer token |
| Authentication | `POST /auth/login` | Authenticate and issue a bearer token |
| Authentication | `GET /auth/me` | Return the authenticated user |
| Authentication | `POST /auth/verify-email` | Verify a registration email or promote a pending email change |
| Account | `PATCH /users/me` | Update the authenticated user's email or username |
| Account | `POST /users/me/email-verification` | Resend the required verification message |
| Account | `PUT /users/me/password` | Change the password after confirming the current password |
| Account | `DELETE /users/me` | Permanently delete the authenticated account after password confirmation |
| Fixtures | `GET /fixtures/matchday` | Return a paginated date-scoped matchday |
| Fixtures | `GET /fixtures/{fixture_id}` | Return fixture overview, statistics, lineups, and timeline |
| Teams | `GET /teams/?search={query}` | Search cached or provider-backed teams |
| Teams | `GET /teams/{team_id}` | Return a team profile |
| My Hub | `GET /users/me/team-preferences` | List the current user's followed teams |
| My Hub | `PUT /users/me/team-preferences` | Add resolvable teams to the current user's hub |
| My Hub | `DELETE /users/me/team-preferences/{team_id}` | Remove a followed team |
| Alerts | `GET /notifications/inbox` | Return alerts and unread count |
| Alerts | `PUT /notifications/inbox/{alert_id}/read` | Mark one alert as read |
| Alerts | `PUT /notifications/inbox/read-all` | Mark all alerts as read |
| Alerts | `GET /notifications/preferences` | Return global user alert preferences |
| Alerts | `PUT /notifications/preferences` | Update supplied global alert toggles |
| Alerts | `POST /notifications/devices` | Register or reactivate an Expo device record |
| Operations | `GET /admin/provider-status` | Return protected provider diagnostics |

Health endpoints are available at `/health` and `/health/ready`.

## Application layers

```text
app/api/           HTTP validation, response mapping, auth dependencies
app/services/      Business rules and transaction coordination
app/repositories/  SQLAlchemy queries and persistence operations
app/db/            Models, sessions, and database setup
app/integrations/  External sports-provider adapters and cache behavior
app/schemas/       Request and response contracts
```

Keeping these responsibilities separate makes the main flows easy to test: endpoints do not contain database queries, services do not know about HTTP responses, and repositories do not make product decisions.

## Database and migrations

Create a new migration after changing a model:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

With Docker, migrations run automatically before the API starts. The current model includes users and email-verification state, teams, user-team associations, global notification preferences, push-device records, alert records, and provider-backed team detail fields.

## Local email

Docker Compose starts Mailpit as the development SMTP server. The API sends mail
to `mailpit:1025`, and the captured inbox is available at
<http://localhost:8025>. Registration and pending-email verification links are
signed with `SECRET_KEY` and expire after 60 minutes. Password changes produce a
security notice but never include a password or token in the message.

## Tests

```bash
python3 -m pytest
```

Run the PostgreSQL-backed suite from the repository root:

```bash
make test-integration
```

The suite covers authentication, endpoint behavior, service rules, repositories, migrations, provider caching, locale-aware matchdays, fixture details, team preferences, and alerts.

## Implementation decisions worth explaining in a demo

- Authenticated preference endpoints derive the user from the bearer token; the client never supplies a `userId`.
- Team following and notification preferences are separate transactions.
- Notification toggles are global per user, not event rules stored per team.
- Repositories are explicit dependencies, so persistence can be tested without mixing it into controllers.
- iSportsAPI access sits behind an adapter and cache, which protects the rest of the code from third-party response details and limits repeat requests.
- Provider status information is administrative and is not displayed as quota telemetry to ordinary users.

## Not in the current release

The API does not yet provide live SSE streams, a background fixture poller, scheduled match-event alert generation, chat, ticket discovery, payment or fulfillment, Redis caching, or cloud deployment.
