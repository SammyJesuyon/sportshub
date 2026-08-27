import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const ROOT = "/Users/samsonkitigo/Documents/Codex/sportshub";
const TMP = path.join(ROOT, "tmp/presentation-revision-jwytUc");
const STARTER = path.join(TMP, "template-starter.pptx");
const FINAL = path.join(ROOT, "docs/SportsHub_Project_Presentation_Revised.pptx");
const RENDERED = path.join(TMP, "final-rendered");

const C = {
  ink: "#10211B",
  forest: "#103D2F",
  green: "#176247",
  lime: "#D9F35B",
  white: "#FFFFFF",
  muted: "#5D6A64",
};

const deck = await PresentationFile.importPptx(await FileBlob.load(STARTER));

function rewrite(shape, value, options = {}) {
  const current = shape.text?.toString?.() ?? "";
  if (value.includes("\n")) shape.text = value;
  else if (current) shape.text.replace(current, value);
  else shape.text = value;
  if (options.color) shape.text.fill = options.color;
  if (options.style) shape.text.style = options.style;
}

function pageNumber(slide, number) {
  rewrite(slide.shapes.items[2], String(number).padStart(2, "0"));
}

function setNotes(slide, talkingPoints, sources) {
  slide.speakerNotes.textFrame.setText([
    ...talkingPoints,
    "",
    "[Sources]",
    ...sources.map((source) => `- ${source}`),
    "[/Sources]",
  ].join("\n"));
  slide.speakerNotes.setVisible(true);
}

function rewriteRows(slide, number, title, rows, footer) {
  rewrite(slide.shapes.items[1], title);
  pageNumber(slide, number);
  const textIndexes = [
    [4, 5, 6],
    [8, 9, 10],
    [12, 13, 14],
    [16, 17, 18],
  ];
  rows.forEach((row, index) => {
    rewrite(slide.shapes.items[textIndexes[index][0]], row[0]);
    rewrite(slide.shapes.items[textIndexes[index][1]], row[1]);
    rewrite(slide.shapes.items[textIndexes[index][2]], row[2]);
  });
  rewrite(slide.shapes.items[19], footer);
}

function rewriteFourCards(slide, number, title, cards, boundaryLabel, boundaryText) {
  rewrite(slide.shapes.items[1], title);
  pageNumber(slide, number);
  const slots = [
    [5, 6, 7],
    [10, 11, 12],
    [15, 16, 17],
    [20, 21, 22],
  ];
  cards.forEach((card, index) => {
    rewrite(slide.shapes.items[slots[index][0]], String(index + 1).padStart(2, "0"));
    rewrite(slide.shapes.items[slots[index][1]], card[0]);
    rewrite(slide.shapes.items[slots[index][2]], card[1]);
  });
  rewrite(slide.shapes.items[24], boundaryLabel);
  rewrite(slide.shapes.items[25], boundaryText);
}

function rewriteThreeColumns(slide, number, title, columns, footer) {
  rewrite(slide.shapes.items[1], title);
  pageNumber(slide, number);
  const slots = [
    [5, 6, 7],
    [10, 11, 12],
    [15, 16, 17],
  ];
  columns.forEach((column, index) => {
    rewrite(slide.shapes.items[slots[index][0]], column[0]);
    rewrite(slide.shapes.items[slots[index][1]], column[1]);
    rewrite(slide.shapes.items[slots[index][2]], column[2].map((item) => `•  ${item}`).join("\n"));
  });
  rewrite(slide.shapes.items[18], footer);
}

// 1. Cover
{
  const slide = deck.slides.items[0];
  rewrite(slide.shapes.items[1], "A focused football\nmatchday experience");
  rewrite(slide.shapes.items[2], "CS425 project demonstration");
  rewrite(slide.shapes.items[10], "A working, tested web release—followed by a clearly separated plan for realtime updates, official tickets, administration, and broader sports coverage.");
  setNotes(slide, [
    "Introduce SportsHub as a football-first product with a working browser release.",
    "Set the expectation that the presentation will clearly separate what is executable today from what the documents place in the next release or later horizon.",
  ], [`${ROOT}/README.md`, `${ROOT}/docs/WEB_PLAN.md`]);
}

// 2. Problem and purpose
{
  const slide = deck.slides.items[1];
  rewrite(slide.shapes.items[1], "SportsHub connects the pieces of a fan’s matchday");
  pageNumber(slide, 2);
  rewrite(slide.shapes.items[5], "Scores, team context, and fan tools often live in separate places.");
  rewrite(slide.shapes.items[6], "SportsHub brings the essential football journey into one responsive web experience: browse the day, understand a fixture, explore a club, personalize a hub, and review alerts.");
  rewrite(slide.shapes.items[13], "Browse matchdays, inspect fixtures, explore teams, personalize My Hub, and review alerts.");
  rewrite(slide.shapes.items[18], "Planned role-protected workflows manage competitions, integrations, and operational configuration.");
  rewrite(slide.shapes.items[23], "iSportsAPI remains authoritative for sports data; future ticket and delivery providers stay outside the system boundary.");
  rewrite(slide.shapes.items[28], "Demonstrate requirements traceability, layered design, persistence, security, testing, and a working application.");
  setNotes(slide, [
    "Explain the product problem in fan terms before discussing implementation.",
    "The current course release is football-first and browser-based; provider-owned data and ticket fulfillment remain outside SportsHub.",
  ], [`${ROOT}/docs/sportshub_usecase.pdf`, `/Users/samsonkitigo/Documents/cs425/CS425.pdf`]);
}

// 3. Technology rationale — Docker intentionally removed.
{
  const slide = deck.slides.items[2];
  rewriteThreeColumns(slide, 3, "The core stack makes responsibilities visible and testable", [
    ["React + TypeScript", "Responsive fan journeys with explicit client contracts", [
      "Route-level pages keep public and protected journeys clear",
      "Typed API models catch response-shape mistakes early",
      "Reusable components support desktop and mobile layouts",
      "Vite keeps development, tests, and production builds fast",
    ]],
    ["FastAPI + Pydantic", "A small modular API with built-in validation", [
      "Versioned REST endpoints and generated OpenAPI documentation",
      "Pydantic schemas validate requests and normalize responses",
      "Dependency injection provides auth and repository boundaries",
      "A modular monolith fits the course scope without microservice overhead",
    ]],
    ["PostgreSQL", "Durable relational storage for user-scoped records", [
      "Constraints protect users, teams, preferences, and alerts",
      "Transactions fit follow operations and inbox creation",
      "Indexes support predictable user and team lookups",
      "Alembic provides repeatable, reviewable schema changes",
    ]],
  ], "Selection principle: choose mature tools that strengthen correctness, clarity, and demonstration value.");
  setNotes(slide, [
    "Explain why each technology was chosen, not only its name.",
    "Docker is intentionally omitted here because it is a local development and integration-test convenience, not a product architecture decision.",
  ], [`${ROOT}/sportshub-frontend/package.json`, `${ROOT}/sportshub-backend/requirements.txt`, `${ROOT}/sportshub-backend/app/db/models.py`]);
}

// 4. Engineering foundation
{
  const slide = deck.slides.items[3];
  rewriteRows(slide, 4, "The implementation follows explicit application-layer boundaries", [
    ["Endpoint layer", "Own HTTP validation, status codes, and authentication dependencies", "Controllers translate requests and responses without embedding database queries or provider rules."],
    ["Service layer", "Coordinate business rules and transaction boundaries", "Following teams, creating alerts, and updating global preferences remain deliberate, testable operations."],
    ["Repository layer", "Isolate SQLAlchemy queries and persistence operations", "Repositories keep database code out of endpoints and make PostgreSQL behavior independently testable."],
    ["Provider adapter", "Normalize iSportsAPI behind SportsHub contracts", "Caching, host fallback, and vendor-field mapping can change without rewriting client-facing endpoints."],
  ], "These boundaries keep persistence details, provider formats, and privileged diagnostics out of the fan interface.");
  setNotes(slide, [
    "Walk the instructor through controller, service, repository, model, and database responsibilities.",
    "Call out that the explicit repository layer was added to match the implementation rubric and improve testability.",
  ], [`${ROOT}/sportshub-backend/app/api`, `${ROOT}/sportshub-backend/app/services`, `${ROOT}/sportshub-backend/app/repositories`, `${ROOT}/sportshub-backend/app/integrations/isports.py`]);
}

// 5. Current release map
{
  const slide = deck.slides.items[4];
  rewrite(slide.shapes.items[1], "Six implemented capabilities form one connected fan experience");
  pageNumber(slide, 5);
  const cards = [
    ["Account access", "Register, sign in, restore the current user, and reach protected routes with a bearer token."],
    ["Matchday center", "Browse one selected local date with status groups, local kickoff times, ordering, and pagination."],
    ["Fixture details", "Review overview, statistics, lineups, timeline, and an explicit Chat coming-soon boundary."],
    ["Explore Teams", "Search publicly, open a useful team profile, view match outlook, and return through recent searches."],
    ["My Hub", "Follow, list, and remove teams through authenticated user-scoped operations."],
    ["Alert inbox", "Review persisted summaries, unread counts, read state, mark-all-read, and stored global preferences."],
  ];
  const slots = [
    [6, 7, 8, 9], [13, 14, 15, 16], [19, 20, 21, 22, 23],
    [26, 27, 28, 29, 30], [33, 34, 35, 36, 37], [40, 41, 42, 43, 44],
  ];
  cards.forEach((card, index) => {
    const slot = slots[index];
    const titleIndex = slot.length === 4 ? slot[0] : slot[1];
    const pillIndex = slot.length === 4 ? slot[1] : slot[2];
    const statusIndex = slot.length === 4 ? slot[2] : slot[3];
    const bodyIndex = slot.length === 4 ? slot[3] : slot[4];
    rewrite(slide.shapes.items[titleIndex], card[0]);
    slide.shapes.items[pillIndex].fill = C.lime;
    rewrite(slide.shapes.items[statusIndex], "IMPLEMENTED", { color: C.ink });
    rewrite(slide.shapes.items[bodyIndex], card[1]);
  });
  rewrite(slide.shapes.items[46], "Every capability on this page is executable in the current release; later features begin in the dedicated roadmap section.");
  setNotes(slide, [
    "Use this as the scope checkpoint: every card can be demonstrated in the current application.",
    "The following slides explain the behavior and implementation value of each capability in more detail.",
  ], [`${ROOT}/README.md`, `${ROOT}/sportshub-frontend/README.md`, `${ROOT}/sportshub-backend/README.md`]);
}

// 6. Accounts
{
  const slide = deck.slides.items[5];
  rewriteRows(slide, 6, "Accounts create a secure, user-scoped experience", [
    ["Create account", "Registration validates required fields and unique email", "A successful registration persists the fan and immediately issues an authenticated session."],
    ["Sign in & restore", "Login verifies credentials; /auth/me restores the current user", "AuthContext owns token lifecycle so route pages do not duplicate session logic."],
    ["Authenticated identity", "Protected endpoints derive the user from the validated token", "Self-service preference operations never trust a browser-supplied userId."],
    ["Protected journeys", "My Hub and Alerts require authentication", "Anonymous visitors are redirected to sign in while matchday and team exploration remain public."],
  ], "Documented next step: add full profile editing and account deletion with the same user-scoped security rules.");
  setNotes(slide, [
    "Demonstrate registration or login, then explain that route guards improve UX while the API provides the actual security boundary.",
  ], [`${ROOT}/sportshub-backend/app/api/auth.py`, `${ROOT}/sportshub-backend/app/services/auth.py`, `${ROOT}/sportshub-frontend/src/auth/AuthContext.tsx`]);
}

// 7. Matchday center
{
  const slide = deck.slides.items[6];
  rewriteRows(slide, 7, "The matchday center keeps every fixture on the right day", [
    ["Selected date", "Users can move through past, current, and upcoming matchdays", "The API returns only fixtures whose kickoff belongs to the selected local calendar date."],
    ["Local kickoff", "Browser timezone is sent to the API and rendered with locale rules", "Fans see the match at the time and date that apply where they are, including UTC day-boundary cases."],
    ["Status & ordering", "Live, half-time, full-time, and scheduled fixtures stay distinct", "Live and in-progress matches appear first, with the latest active fixtures ordered ahead of older results."],
    ["Pagination & states", "Large matchdays are paginated and filterable", "Loading, no-results, unavailable-provider, and retry states keep the page usable without exposing provider telemetry."],
  ], "Next release adds independent polling and SSE; the current page refreshes from date-scoped provider snapshots.");
  setNotes(slide, [
    "Show a date change, local kickoff time, status tab, and pagination control.",
    "Explain the prior bug that mixed other-day completed fixtures and how local-date filtering now prevents it.",
  ], [`${ROOT}/sportshub-backend/app/api/fixtures.py`, `${ROOT}/sportshub-frontend/src/pages/HomePage.tsx`]);
}

// 8. Fixture details
{
  const slide = deck.slides.items[7];
  rewriteRows(slide, 8, "Fixture details turn a score into match context", [
    ["Overview", "Score, status, venue, referee, kickoff, and period totals", "A fan can understand the match state without leaving the selected fixture."],
    ["Statistics", "Provider-backed team metrics are normalized into a stable response", "Available possession, shots, and other measures render by team while missing data degrades cleanly."],
    ["Lineups", "Formation, coach, starting XI, and substitutes appear by team", "The detail contract keeps provider-specific fields out of the React page."],
    ["Timeline & tabs", "Goals, cards, substitutions, and match events share an accessible tab set", "Tabs keep dense information readable and retain one clear route back to the matchday center."],
  ], "Chat is intentionally labeled “Coming soon”; no messaging or community behavior is claimed in this release.");
  setNotes(slide, [
    "Open each detail tab during the demo and emphasize graceful handling when a provider omits optional data.",
  ], [`${ROOT}/sportshub-backend/app/api/fixtures.py`, `${ROOT}/sportshub-frontend/src/pages/FixtureDetailPage.tsx`]);
}

// 9. Explore Teams
{
  const slide = deck.slides.items[8];
  rewriteRows(slide, 9, "Explore Teams answers who a club is—and what comes next", [
    ["Public search", "Search provider-backed teams without signing in", "Discovery is deliberately separate from the authenticated action of following a team."],
    ["Useful profile", "Crest, country, type, founded year, venue, capacity, and location", "The selected search result expands into a stable SportsHub team record rather than stalling on a button state."],
    ["Match outlook", "Show a live/current fixture, next match, and latest result when available", "Each match card links directly to the fixture detail route in the fan’s local time."],
    ["Recent searches", "The browser keeps the five most recently opened team profiles", "Fans can resume exploration quickly without changing account data or the teams in My Hub."],
  ], "Exploring a team is public and read-only; it never adds or removes a followed-team association.");
  setNotes(slide, [
    "Demonstrate a team search, the profile facts, the match outlook, and a recent-search revisit.",
  ], [`${ROOT}/sportshub-backend/app/api/teams.py`, `${ROOT}/sportshub-backend/app/services/teams.py`, `${ROOT}/sportshub-frontend/src/pages/TeamsPage.tsx`]);
}

// 10. My Hub
{
  const slide = deck.slides.items[9];
  rewriteRows(slide, 10, "My Hub makes personalization reversible and user-scoped", [
    ["Follow a team", "Authenticated fans add a resolved team to their personal hub", "The current user comes from the bearer token, so one fan cannot write another fan’s preferences."],
    ["Stable resolution", "Repository logic resolves internal UUIDs and provider identifiers", "Shared team records remain reusable even when a provider uses a different external ID format."],
    ["Duplicate safe", "The service appends only missing user-team associations", "Repeated follow requests report duplicates instead of creating a second association."],
    ["Confirmed removal", "Fans confirm before removing a followed team", "Only that user-team association is deleted; the shared team and other users’ follows remain intact."],
  ], "Team following and global notification preferences are separate transactions with separate API requests.");
  setNotes(slide, [
    "Follow a team, show it in My Hub, then remove it to prove that personalization is reversible.",
  ], [`${ROOT}/sportshub-backend/app/api/users.py`, `${ROOT}/sportshub-backend/app/repositories/team_preferences.py`, `${ROOT}/sportshub-frontend/src/pages/TeamsPage.tsx`]);
}

// 11. Alerts
{
  const slide = deck.slides.items[10];
  rewriteRows(slide, 11, "The alert inbox makes account activity visible", [
    ["Persistent inbox", "Alerts are stored per user and ordered newest first", "Refreshing the page preserves summaries, links, timestamps, and read state in PostgreSQL."],
    ["Current sources", "Registration creates a welcome alert; a new follow creates a team alert", "These concrete account events prove the inbox flow without pretending scheduled match alerts already run."],
    ["Unread workflow", "Navigation badge, unread dot, single-read, and mark-all-read stay synchronized", "Every read operation is scoped to the authenticated user and updates the visible unread count."],
    ["Preference foundation", "Global pre-match, kickoff, end, chat, and promotion toggles are stored", "The API can also store a device token, but the web release does not expose push setup or delivery."],
  ], "Next release generates pre-match, match-start, score, and full-time alerts from fixture events; today’s delivery is in-app only.");
  setNotes(slide, [
    "Explain the difference between the implemented inbox/preferences foundation and the not-yet-implemented match-event scheduler.",
  ], [`${ROOT}/sportshub-backend/app/services/notifications.py`, `${ROOT}/sportshub-backend/app/services/auth.py`, `${ROOT}/sportshub-backend/app/services/teams.py`, `${ROOT}/sportshub-frontend/src/pages/AlertsPage.tsx`]);
}

// 12. Provider and caching
{
  const slide = deck.slides.items[11];
  rewriteRows(slide, 12, "Provider integration stays quota-conscious and replaceable", [
    ["Adapter boundary", "iSportsAPI calls stay behind one SportsHub provider contract", "Endpoints and React pages consume normalized fixtures, teams, statistics, lineups, and schedules."],
    ["Normalization", "Vendor fields map into stable internal response models", "A provider replacement changes the adapter and contract tests—not every controller and component."],
    ["Cache discipline", "Matchdays, fixture details, teams, searches, and schedules are cached", "Persistent snapshots reduce repeat requests, support local pagination, and protect a limited API allowance."],
    ["Graceful fallback", "Secondary-host retry, sample data, and clear unavailable states protect the demo", "The UI never exposes API keys, quota counters, cache-hit telemetry, or raw provider diagnostics to fans."],
  ], "Provider diagnostics remain administrator-only; credentials and signing secrets stay in ignored runtime configuration.");
  setNotes(slide, [
    "Connect caching to the provider suspension and free-tier constraint: the goal is resilient product behavior, not a quota dashboard for users.",
  ], [`${ROOT}/sportshub-backend/app/integrations/isports.py`, `${ROOT}/sportshub-backend/app/api/admin.py`, `${ROOT}/docs/WEB_PLAN.md`]);
}

// 13. Security and data design
{
  const slide = deck.slides.items[12];
  rewrite(slide.shapes.items[1], "Security and persistence are enforced behind the UI");
  pageNumber(slide, 13);
  rewrite(slide.shapes.items[7], "BCrypt hashes are stored instead of plaintext credentials.");
  rewrite(slide.shapes.items[10], "Signed, expiring JWTs are validated for protected requests.");
  rewrite(slide.shapes.items[13], "The API derives identity from the token; the browser never supplies userId.");
  rewrite(slide.shapes.items[16], "Repository classes keep SQLAlchemy queries outside endpoint and service code.");
  rewrite(slide.shapes.items[19], "Alembic creates repeatable, reviewable PostgreSQL schema changes.");
  rewrite(slide.shapes.items[22], "Provider keys and signing secrets remain in ignored runtime configuration.");
  rewrite(slide.shapes.items[25], "Security is enforced by the API—not by hiding links.");
  setNotes(slide, [
    "Tie the user interface to backend enforcement: protected routes improve navigation, but authorization, validation, and record scoping happen in the API.",
  ], [`${ROOT}/sportshub-backend/app/core/security.py`, `${ROOT}/sportshub-backend/app/api/dependencies.py`, `${ROOT}/sportshub-backend/alembic`]);
}

// 14. Test evidence
{
  const slide = deck.slides.items[13];
  rewrite(slide.shapes.items[1], "Automated evidence covers behavior at every layer");
  pageNumber(slide, 14);
  rewrite(slide.shapes.items[4], "48");
  rewrite(slide.shapes.items[8], "8");
  rewrite(slide.shapes.items[12], "2");
  rewrite(slide.shapes.items[16], "48");
  rewrite(slide.shapes.items[18], "Integration profile");
  rewrite(slide.shapes.items[21], "Authentication, validation, status codes, local-date filtering, pagination, and fixture details");
  rewrite(slide.shapes.items[24], "Preference rules, user scoping, alert state, repository queries, transactions, and error cases");
  rewrite(slide.shapes.items[27], "iSportsAPI normalization, caching, secondary-host fallback, optional detail data, and failures");
  rewrite(slide.shapes.items[30], "Desktop and mobile matchday, fixture-tab, and team-detail browser journeys");
  rewrite(slide.shapes.items[31], "Current suite · 48 backend tests · 8 frontend tests · 2 browser projects");
  setNotes(slide, [
    "Explain what each layer proves rather than treating the counts as the entire testing story.",
    "The integration profile reruns the backend suite against PostgreSQL so repository behavior matches the production database type.",
  ], [`${ROOT}/docs/TEST_PLAN.md`, `${ROOT}/sportshub-backend/tests`, `${ROOT}/sportshub-frontend/src/test/App.test.tsx`, `${ROOT}/sportshub-frontend/e2e/smoke.spec.ts`]);
}

// 15. Demo route
{
  const slide = deck.slides.items[14];
  rewrite(slide.shapes.items[1], "The demo follows one fan from discovery to personalization");
  pageNumber(slide, 15);
  const steps = [
    [6, 7, "Browse the matchday", "Change the date, show local time, select a status, and open a fixture."],
    [10, 11, "Inspect the fixture", "Move through overview, statistics, lineups, timeline, and the Chat boundary."],
    [14, 15, "Explore a team", "Search, open a profile, inspect the match outlook, and revisit a recent search."],
    [18, 19, "Build My Hub", "Register or sign in, follow the team, then remove it with confirmation."],
    [22, 23, "Review the inbox", "Open Alerts, read one item, and clear the remaining unread count."],
  ];
  steps.forEach(([titleIndex, bodyIndex, title, body]) => {
    rewrite(slide.shapes.items[titleIndex], title);
    rewrite(slide.shapes.items[bodyIndex], body);
  });
  rewrite(slide.shapes.items[25], "If live provider data is unavailable, continue with the sample provider and the local account, hub, and alert flows.");
  setNotes(slide, [
    "Use this as the browser demonstration checklist so the presentation proves the major current-release use cases in one story.",
  ], [`${ROOT}/README.md`, `${ROOT}/sportshub-frontend/README.md`]);
}

// 16. Next release — realtime and alerts
{
  const slide = deck.slides.items[15];
  rewriteFourCards(slide, 16, "Next release: realtime updates and match-event alerts", [
    ["Independent poller", "Poll live fixtures in background work, compare snapshots, and broadcast only when a match is live or its state changes."],
    ["Browser SSE", "Subscribe before the initial detail lookup, then deliver connected, fixture_detail, fixture_update, and heartbeat events."],
    ["Fresh reconnect", "A reconnect opens a new subscription and restores current state from a fresh snapshot—without Last-Event-ID or replay."],
    ["Generated alerts", "Evaluate followed teams and global toggles to create pre-match, kickoff, score, and full-time inbox events."],
  ], "Built now", "Stored global toggles and inbox records exist now; next release adds event generation and scheduling.");
  setNotes(slide, [
    "Present realtime behavior and automated alerts as one coherent next-release slice built on the current fixture and inbox foundations.",
  ], [`${ROOT}/docs/WEB_PLAN.md`, `${ROOT}/docs/lab4_sequence_diagram.pdf`, `${ROOT}/docs/SportsHub_Lab5.pdf`]);
}

// 17. Next release — product scope
{
  const slide = deck.slides.items[16];
  rewriteFourCards(slide, 17, "Next release: tickets, standings, and administration", [
    ["Standings & competitions", "Add normalized competition and standings views so fans can move from a fixture to broader league context."],
    ["Official ticket discovery", "Resolve fixture teams, competition, date, and attraction mappings into Ticketmaster search parameters."],
    ["Safe buy redirect", "Route /api/v1/tickets/events/{eventId}/buy through eligible Impact links with direct Ticketmaster fallback."],
    ["Admin workflows", "Add role-protected featured-tournament ordering, integration status, and limited user/content operations with audit evidence."],
  ], "Boundary", "SportsHub does not own inventory or process payment, fulfillment, refunds, or ticket-provider support.");
  setNotes(slide, [
    "Keep ticketing precise: SportsHub supports discovery and safe handoff only.",
    "Featured-tournament administration comes from the documented use case and does not delete the underlying tournament or fixtures.",
  ], [`${ROOT}/docs/sportshub_usecase.pdf`, `${ROOT}/docs/WEB_PLAN.md`, `${ROOT}/docs/lab4_sequence_diagram.pdf`]);
}

// 18. Next release — engineering
{
  const slide = deck.slides.items[17];
  rewriteThreeColumns(slide, 18, "Next-release engineering makes the product production-ready", [
    ["Shared realtime state", "Introduce infrastructure only when the live path requires it", [
      "Add Redis when multiple API processes must share cache or subscription state",
      "Define ownership, TTLs, versioned keys, and invalidation rules",
      "Keep process-local cache disposable and provider snapshots recoverable",
      "Prove concurrency and fixture-isolation behavior with automated tests",
    ]],
    ["Background work", "Separate scheduled work from browser requests", [
      "Run fixture polling and alert generation outside request handlers",
      "Make jobs idempotent and retry provider failures with bounds",
      "Record alert outcomes without inventing user-visible queue semantics",
      "Measure worker health and live-update delay",
    ]],
    ["Cloud-ready operations", "Harden delivery, recovery, and observability", [
      "Add secure edge routing, TLS, scaling, and environment configuration",
      "Centralize logs, metrics, health checks, and secret redaction",
      "Rehearse migrations, backup, restore, rollback, and provider outage paths",
      "Complete accessibility, performance, and responsive regression gates",
    ]],
  ], "This work turns the same modular boundaries into a dependable release without prematurely splitting the application into microservices.");
  setNotes(slide, [
    "Describe these as release-enabling engineering tasks rather than end-user features.",
  ], [`${ROOT}/docs/WEB_PLAN.md`, `${ROOT}/docs/TEST_PLAN.md`, `${ROOT}/docs/SportsHub Lab 3 Architecture - Scope Aligned.pdf`]);
}

// 19. Later horizon
{
  const slide = deck.slides.items[18];
  rewriteThreeColumns(slide, 19, "Later expansion stays separate from the next release", [
    ["More sports", "Extend the football-first product through stable contracts", [
      "Add sports only after provider coverage and response models are defined",
      "Reuse authentication, preferences, alerts, and navigation foundations",
      "Keep sport-specific rules behind adapters and services",
      "Preserve the current “more sports coming soon” expectation",
    ]],
    ["Native mobile", "Deliver a dedicated Android and iOS experience", [
      "Push notifications tied to the same global preference model",
      "Offline access to selected content and home-screen widgets",
      "Biometric authentication and improved mobile performance",
      "Share API contracts without duplicating backend business rules",
    ]],
    ["Optional engagement", "Ideas documented beyond the initial platform", [
      "AI predictions and personalized recommendations",
      "Social communities, match discussion, and in-app messaging",
      "Official merchandise discovery or marketplace features",
      "Premium subscriptions and advanced statistics",
    ]],
  ], "These are long-term possibilities—not commitments for the next release and not completed functionality in the current submission.");
  setNotes(slide, [
    "Use this slide to protect scope: the documents name these ideas, but the next release remains focused on finishing the web platform.",
  ], [`/Users/samsonkitigo/Documents/cs425/CS425.pdf`, `${ROOT}/docs/SportsHub Lab 3 Architecture - Scope Aligned.pdf`, `${ROOT}/docs/WEB_PLAN.md`]);
}

// 20. Closing
{
  const slide = deck.slides.items[19];
  rewrite(slide.shapes.items[1], "A working foundation for a broader sports platform");
  rewrite(slide.shapes.items[2], "Working now");
  rewrite(slide.shapes.items[3], "A tested football workflow for local-time matchdays, fixture detail, team exploration, My Hub, authentication, and an in-app alert inbox.");
  rewrite(slide.shapes.items[4], "Next release");
  rewrite(slide.shapes.items[5], "Realtime updates, generated match alerts, standings, official ticket discovery, administration, and release hardening.");
  rewrite(slide.shapes.items[6], "The constant");
  rewrite(slide.shapes.items[7], "Stable application boundaries keep the product understandable as it grows.");
  setNotes(slide, [
    "Close by returning to the opening promise: a coherent current experience and a disciplined, evidence-backed next release.",
    "Invite technical questions about layering, authentication, user scoping, provider normalization, caching, migrations, or tests.",
  ], [`${ROOT}/README.md`, `${ROOT}/docs/WEB_PLAN.md`]);
}

await fs.rm(RENDERED, { recursive: true, force: true });
await fs.mkdir(RENDERED, { recursive: true });

for (const [index, slide] of deck.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await deck.export({ slide, format: "png", scale: 1.5 });
  await fs.writeFile(path.join(RENDERED, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(RENDERED, `${stem}.layout.json`), await layout.text());
}

const montage = await deck.export({ format: "png", montage: true, scale: 1 });
await fs.writeFile(path.join(RENDERED, "deck-montage.png"), new Uint8Array(await montage.arrayBuffer()));

const inspection = await deck.inspect({
  kind: "slide,textbox,shape,image,notes,layout",
  maxChars: 100000,
});
await fs.writeFile(path.join(RENDERED, "final-inspect.ndjson"), inspection.ndjson);

const output = await PresentationFile.exportPptx(deck);
await output.save(FINAL);
console.log(FINAL);
