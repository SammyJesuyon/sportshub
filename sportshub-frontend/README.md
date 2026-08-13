# SportsHub Frontend

Responsive React and TypeScript client for the SportsHub CS425 miniature.

## Current web slice

- responsive application shell and home dashboard;
- account registration, login, session restoration, and protected routes;
- provider-backed team search and authenticated adding/removal of followed teams;
- persisted in-app alert summaries with unread/read state and a red navigation badge;
- desktop and mobile browser smoke-test configuration.

## Commands

```bash
npm install
npm run dev
npm test -- --run
npm run build
```

Set `VITE_API_BASE_URL` to the FastAPI `/api/v1` URL. The root Compose stack provides this automatically.
