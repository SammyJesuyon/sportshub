# SportsHub Backend

SportsHub is the CS425-sized miniature derived from LeagueBook. It is an independent FastAPI modular monolith: the SportsHub Vision and architecture documents control product scope, while LeagueBook contributes implementation patterns only.

## Scope boundary

Initial SportsHub scope:

- responsive web client and a later small admin portal;
- secure accounts and bearer-token authentication;
- favorite teams and global notification preferences;
- football teams, fixtures, live scores, standings, and statistics;
- browser live updates through SSE;
- official ticket discovery with external purchase redirects.

Explicitly excluded from this miniature are LeagueBook chat/social features, gamification, predictions, points and wallets, merchandise, premium subscriptions, native mobile applications, AI recommendations, payment processing, and ticket fulfillment.

## Implemented first slice

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/teams/?search={query}`
- `PUT /api/v1/users/me/team-preferences`
- `GET /api/v1/users/me/team-preferences`
- `GET /api/v1/notifications/preferences`
- `PUT /api/v1/notifications/preferences`
- `POST /api/v1/notifications/devices`
- `GET /health`

The endpoint derives the current user from the bearer token. The client never submits a `userId` for preference mutations. Team-following and notification-preference changes are separate transactions, and notification toggles are global per user. SportsHub currently stores only in-scope match toggles (`enabled`, `pre_match_reminder`, `match_start`, and `match_end`); LeagueBook's chat and commerce toggles are deliberately not copied.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

The local default uses SQLite and a deterministic sample sports adapter, so the project works without external credentials. To search API-Sports, set `SPORTS_PROVIDER=api-sports` and provide `API_SPORTS_KEY`. PostgreSQL can be selected later through `DATABASE_URL` without changing endpoint contracts.

## Test

```bash
pytest
```

## Next vertical slices

1. Fixtures, standings, and team/player statistics behind the same provider-adapter boundary.
2. Independent fixture polling, current snapshots, and SSE live updates without event replay.
3. Ticketmaster search and safe `/events/{eventId}/buy` redirects, with Impact fallback behavior.
4. A small role-protected admin surface for users, competitions, integrations, and notification operations.
