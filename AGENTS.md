# SportsHub Engineering Rules

## Product identity

SportsHub is the miniature CS425 project derived from LeagueBook. It is an independent project, not a rename or fork of the full LeagueBook product.

## Sources of truth

Use these sources in this order:

1. `/Users/samsonkitigo/Documents/cs425/CS425.pdf` controls SportsHub product scope and terminology.
2. SportsHub Lab 3-5 documents under `/Users/samsonkitigo/Documents/Codex/2026-07-18/google-drive-plugin-google-drive-openai/outputs/` guide the planned architecture and analyzed use cases.
3. `/Users/samsonkitigo/Documents/leaguebook-backend` supplies implementation patterns and provider behavior only. Its extra features do not expand SportsHub scope.

Do not modify LeagueBook while implementing SportsHub unless the user explicitly requests a LeagueBook change.

## Initial SportsHub scope

- Responsive web API and a small admin surface.
- Registration, login, roles, and profile basics.
- Favorite teams or competitions and global notification preferences.
- Football teams, fixtures, live scores, standings, and team/player statistics.
- Independent fixture polling and browser SSE updates.
- Official ticket discovery and safe external purchase redirects.

## Excluded LeagueBook capabilities

Do not add chat, communities, social moderation, gamification, predictions, points, credits, wallets, cosmetics, boosts, referrals, leaderboards, merchandise, subscriptions, native applications, AI recommendations, payment processing, or ticket fulfillment unless the user explicitly changes SportsHub scope.

## Architecture

- Keep a FastAPI modular monolith with endpoint, service, repository/persistence, and external-adapter boundaries.
- Start locally with SQLite and deterministic adapters; preserve PostgreSQL-ready SQLAlchemy models and API-Sports-ready adapters.
- Derive the authenticated user from bearer tokens. Never accept a browser-provided `userId` for self-service preference mutations.
- Keep team following and notification configuration as separate transactions.
- Notification preferences are global per user, not per team.
- Do not invent durable queues, SSE replay, `Last-Event-ID`, per-team notification rules, `TicketOffer` persistence, payments, or fulfillment.
- Keep secrets in environment configuration and validate production configuration.

## Verification

- Run `PYTHONPYCACHEPREFIX=/tmp/sportshub-pycache python3 -m compileall -q app tests`.
- Run `PYTHONPYCACHEPREFIX=/tmp/sportshub-pycache python3 -m pytest`.
- Add tests for authentication, invalid input, duplicate/retry behavior, transaction boundaries, and provider failures as each slice grows.

