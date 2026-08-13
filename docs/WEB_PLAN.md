# SportsHub Web Plan

The web application is a responsive fan experience inside the SportsHub monorepo. It consumes the backend through `/api/v1`; provider credentials and provider-specific logic stay on the server.

## Product shape

- React and TypeScript client with route-level pages and a typed API boundary.
- FastAPI modular monolith with PostgreSQL as the system of record and Alembic migrations.
- Docker Compose development stack: `web`, `api`, `migrate`, and `db`.
- Bearer authentication initially; the client stores only the session token and derives the current user from `/auth/me`.
- Mobile-first layouts with explicit loading, empty, degraded, and retry states.

## Delivery sequence

### 1. Foundation — implemented

- Responsive shell, registration, sign-in/sign-out, protected routes.
- Team search and authenticated team following.
- Global notification preferences with failed-update rollback.
- Dockerized web/API/PostgreSQL workflow and automated migration gate.

Definition of done: component tests, PostgreSQL integration suite, web production build, responsive browser inspection, and health checks all pass.

### 2. Sports browsing — in progress

- Show provider-backed matchday fixtures on the home page, grouped into live, half-time, full-time, and scheduled sections — implemented.
- Monitor the 100-request free-tier allowance from response headers, persist provider snapshots across restarts, paginate locally, and cache fixture detail responses — implemented.
- Keep public team exploration separate from authenticated team selection and following — implemented.
- Add team and standings pages from normalized backend contracts; fixture statistics, lineups, and timeline are implemented.
- Keep cache and provider-status telemetry on an authenticated administrator endpoint, never in fan-facing pages or public fixture responses.

Definition of done: contract tests cover normalization and degraded states; browser tests cover search-to-fixture navigation on desktop and mobile.

### 3. Live match

- Add the independent background fixture poller and per-fixture SSE broker.
- Build a live fixture view for connected, fixture-detail, fixture-update, heartbeat, disconnect, and reconnect states.
- On reconnect, restore a fresh snapshot only—no event IDs or missed-event replay.

Definition of done: ordering/concurrency tests prove subscribe-before-detail and poller independence; a browser journey survives a forced reconnect.

### 4. Official ticket discovery

- Resolve a fixture to Ticketmaster search parameters and show official event results.
- Route purchases through `/api/v1/tickets/events/{eventId}/buy` with Impact eligibility and direct Ticketmaster fallback.
- Label the handoff clearly: SportsHub does not handle inventory, payment, fulfillment, refunds, or provider support.

Definition of done: resolver, fallback, and external-redirect tests pass; no `TicketOffer` persistence exists.

### 5. Small administration surface

- Add role-protected integration status and the limited content/user operations required by the course scope.
- Record auditable administrative changes without importing LeagueBook community or commerce administration.

Definition of done: every route has positive and negative role tests, and secrets never reach client responses or logs.

### 6. Release hardening

- Accessibility audit, performance budgets, responsive visual regression, and full browser journeys.
- Production images/configuration, migration upgrade rehearsal, backup/restore drill, observability, and deployment runbook.

## Deliberate deferrals

Redis waits until the live-update design has a concrete multi-process shared-state need. Chat, communities, gamification, predictions, wallets, merchandise, subscriptions, native apps, AI recommendations, payment processing, and fulfillment remain outside the SportsHub school-project scope.
