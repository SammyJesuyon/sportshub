# SportsHub Backend Engineering Rules

## Product identity

SportsHub is a self-contained miniature CS425 project with its own product identity, scope, and implementation.

## Sources of truth

Use these sources in this order:

1. The root `../AGENTS.md` and `/Users/samsonkitigo/Documents/cs425/CS425.pdf` control SportsHub structure, scope, and terminology.
2. SportsHub Lab 3-5 documents under `/Users/samsonkitigo/Documents/Codex/2026-07-18/google-drive-plugin-google-drive-openai/outputs/` guide the planned architecture and analyzed use cases.
## Initial SportsHub scope

- Responsive web API and a small admin surface.
- Registration, login, roles, and profile basics.
- Favorite teams or competitions and global notification preferences.
- Football teams, fixtures, live scores, standings, and team/player statistics.
- Independent fixture polling and browser SSE updates.
- Official ticket discovery and safe external purchase redirects.

## Excluded capabilities

Do not add chat, communities, social moderation, gamification, predictions, points, credits, wallets, cosmetics, boosts, referrals, leaderboards, merchandise, subscriptions, native applications, AI recommendations, payment processing, or ticket fulfillment unless the user explicitly changes SportsHub scope.

## Architecture

- Keep a FastAPI modular monolith with endpoint, service, repository/persistence, and external-adapter boundaries.
- PostgreSQL is the development and production system of record; Alembic owns schema creation and changes.
- SQLite is permitted only for fast isolated tests. Docker integration tests must use PostgreSQL.
- Derive the authenticated user from bearer tokens. Never accept a browser-provided `userId` for self-service preference mutations.
- Keep team following and notification configuration as separate transactions.
- Notification preferences are global per user, not per team.
- Do not invent durable queues, SSE replay, `Last-Event-ID`, per-team notification rules, `TicketOffer` persistence, payments, or fulfillment.
- Keep secrets in environment configuration and validate production configuration.

## Verification

- Run `PYTHONPYCACHEPREFIX=/tmp/sportshub-pycache python3 -m compileall -q app tests`.
- Run `PYTHONPYCACHEPREFIX=/tmp/sportshub-pycache python3 -m pytest`.
- Run migrations against an isolated database with `alembic upgrade head`; never use runtime `create_all()` for the application schema.
- Add tests for authentication, invalid input, duplicate/retry behavior, transaction boundaries, and provider failures as each slice grows.
