# SportsHub Monorepo Engineering Rules

SportsHub is a self-contained miniature CS425 project with its own product identity, scope, and implementation.

## Sources of truth

1. `/Users/samsonkitigo/Documents/cs425/CS425.pdf` controls school-project scope and terminology.
2. SportsHub Lab 3-5 artifacts under `/Users/samsonkitigo/Documents/Codex/2026-07-18/google-drive-plugin-google-drive-openai/outputs/` guide architecture and analyzed use cases.

## Repository structure

- `sportshub-backend/`: FastAPI modular monolith.
- `sportshub-frontend/`: responsive React and TypeScript web application.
- `compose.yaml`: PostgreSQL, schema migration, API, web, and integration-test orchestration.

Do not introduce an `apps/` wrapper. Keep backend and frontend as sibling folders.

## Scope boundary

Initial scope includes accounts, roles, favorites/preferences, football content, live SSE, notifications, official ticket discovery, and a small admin surface. Do not add chat, communities, gamification, predictions, wallets, merchandise, subscriptions, native applications, AI recommendations, payment processing, or fulfillment without an explicit scope change.

## Architecture invariants

- PostgreSQL is the development and production system of record; Alembic owns schema changes.
- SQLite is allowed only for fast isolated backend tests.
- Derive the current user from bearer authentication; self-service payloads must reject `userId`.
- Team following and notification preferences are separate transactions.
- Notification preferences are global per user, not per team.
- Do not invent durable queues, SSE replay, `Last-Event-ID`, per-team notification rules, or `TicketOffer` persistence.
- Keep provider-specific behavior behind adapters and secrets in environment configuration.
- Add Redis only when the live-update implementation has a concrete shared-state requirement.

## Verification

- Backend: `cd sportshub-backend && python3 -m pytest`.
- Frontend: `cd sportshub-frontend && npm test -- --run && npm run build`.
- Full PostgreSQL integration: `docker compose --profile test run --rm api-test`.
- Compose validation: `docker compose config --quiet`.
