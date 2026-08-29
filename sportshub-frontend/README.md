# SportsHub Web

SportsHub Web is the React client for the football matchday experience. It is designed for a short live demo: the main journeys are easy to find, protected pages behave predictably, and provider failures are shown as product states rather than raw technical diagnostics.

## Start the web application

The preferred setup runs the frontend, API, migrations, and PostgreSQL together:

```bash
cd ..
docker compose up --build
```

Open <http://localhost:5173>.

To run only the frontend locally:

```bash
npm install
VITE_API_BASE_URL=http://localhost:8010/api/v1 npm run dev
```

## Routes and demo purpose

| Route | What to show |
| --- | --- |
| `/` | Date selection, locale-aware matchday groups, status filters, and pagination |
| `/fixtures/:fixtureId` | Overview, statistics, lineups, timeline, and the chat placeholder |
| `/explore/teams` | Team search, recent searches, and a selected team profile |
| `/register` | Account creation and automatic sign-in |
| `/login` | Existing-user sign-in |
| `/verify-email` | Consume a signed registration or email-change verification link |
| `/profile` | Update the signed-in email or username and securely delete the account |
| `/my/teams` | Followed teams and the remove-from-hub action |
| `/alerts` | Alert summaries, unread count, individual read state, and mark all read |

The old `/teams` route redirects to `/explore/teams` so team discovery has one clear destination.

## Frontend structure

```text
src/api/          Typed HTTP client and API contracts
src/components/   Shared shell, navigation, route guards, and UI pieces
src/context/      Authentication state and token lifecycle
src/pages/        Route-level matchday, fixture, team, account, and alert views
src/test/         Vitest and Testing Library setup
e2e/              Playwright browser journeys
```

`AppShell` owns the navigation and alert badge. `AuthContext` restores the signed-in user and keeps bearer-token handling out of individual pages. Protected routes send anonymous visitors to sign in before they can reach My Hub or Alerts.

## Suggested browser demo

1. On Home, choose a date and open a fixture.
2. Move through the detail tabs and call out the explicit Chat “coming soon” state.
3. Search for a team in Explore Teams and revisit it from recent searches.
4. Register or sign in, then add and remove the team in My Hub.
5. Select the username in the header, request an email update, and open the verification message in Mailpit at <http://localhost:8025>.
6. Change the password and show the security notice in Mailpit; show that deletion also requires the current password.
7. Open Alerts, read one item, and clear the remaining unread count.
8. Resize to a narrow viewport to show that the same flow remains usable on mobile.

## Quality checks

```bash
npm test -- --run
npm run lint
npm run build
npm run test:e2e
```

The component suite covers route rendering, date handling, fixture detail states, team discovery, authenticated navigation, profile updates, verification links, password changes, and account deletion. Playwright runs the main journey in desktop and mobile projects.

## UX boundaries

- Kickoff times are rendered in the browser's locale.
- Only the selected matchday is displayed; completed fixtures from other dates are not mixed into the list.
- Live and in-progress fixtures are ordered ahead of older completed fixtures.
- Provider quota data and API credentials are never shown to fans.
- Match-event alert preferences exist, but scheduled pre-match, kickoff, score, and full-time alert generation remains future work.
- Chat, additional sports, live SSE updates, tickets, and push-delivery UX are future work and are labeled accordingly.
