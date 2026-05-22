# Atlas Analytics

A production-style analytics SaaS MVP built for the Senior Full Stack Engineer assessment. It uses React.js on the frontend and FastAPI/Python on the backend, with PostgreSQL, Redis, and Celery for async processing.

## What is included

- JWT auth with refresh-token cookie.
- Organization-scoped multi-tenancy and role-based guards.
- API key generation, rotation, and revocation.
- Event ingestion through single event, batch event, and CSV upload endpoints.
- Webhook ingestion endpoint, API-key rate limiting, and live event stream over WebSockets.
- Dashboard CRUD with chart widgets, templates, presentation mode, and auto-refreshing chart data.
- Team invitations and member role updates.
- Alert-rule CRUD, manual evaluation, mute/snooze, alert history, in-app notifications, webhook delivery, and SMTP-ready email notification records.
- Scheduled report creation, on-demand report runs, and PDF download archive endpoint.
- Alembic scaffold for migration generation.
- Docker Compose for Postgres, Redis, API, Celery worker, and Celery Beat.

## Tech stack

- Frontend: React + Vite + TypeScript + Tailwind CSS + TanStack Query + Recharts.
- Backend: FastAPI + SQLAlchemy async + Pydantic v2.
- Infrastructure: PostgreSQL + Redis + Celery.

## Local setup

### Backend without Docker

Use this path if Docker Desktop is not installed.

```bash
cd backend
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

This uses a local SQLite database file at `backend/analytics.db`. Celery/Redis tasks fall back to inline execution for local demo ingestion.

### Backend and infrastructure with Docker

```bash
docker compose up --build
```

API runs at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Demo flow

1. Sign up from the frontend. This creates an organization and makes the user an Owner.
2. Open Ingestion, generate an API key, and copy the full key.
3. Paste the key into the ingestion form and submit a few events such as `signup` or `checkout`.
4. Create a dashboard and add a widget whose metric name matches the event name.
5. Watch the chart populate from organization-scoped event data.
6. Open Alerts to create and evaluate threshold rules.
7. Open Reports to schedule and download a generated PDF report.

## API overview

- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /organizations/current`
- `POST /organizations/invites`
- `POST /organizations/invites/accept`
- `PATCH /organizations/members/{member_id}`
- `GET /api-keys`
- `POST /api-keys`
- `POST /api-keys/{id}/rotate`
- `DELETE /api-keys/{id}`
- `POST /ingest/events`
- `POST /ingest/events/batch`
- `POST /ingest/csv`
- `POST /ingest/webhook/{source}`
- `GET /dashboards`
- `POST /dashboards`
- `GET /dashboards/{id}`
- `PATCH /dashboards/{id}`
- `DELETE /dashboards/{id}`
- `POST /dashboards/{id}/widgets`
- `PATCH /widgets/{id}`
- `DELETE /widgets/{id}`
- `GET /alerts`
- `POST /alerts`
- `GET /alerts/history`
- `POST /alerts/evaluate`
- `POST /alerts/{alert_id}/mute`
- `GET /notifications`
- `GET /reports`
- `POST /reports`
- `POST /reports/{report_id}/run`
- `GET /reports/runs/{report_id}/download`
- `WS /ws/events/{organization_id}`

## Deployment

Deployment templates are included:

- `railway.json` for Railway backend deploy.
- `render.yaml` for Render backend + Postgres.
- `frontend/vercel.json` for Vercel frontend deploy.

Actual hosting requires connecting your Railway/Render/Vercel account and setting production env vars such as `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `FRONTEND_ORIGIN`, `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, and `VITE_API_URL`.

## Notifications

The notification stack is:

- In-app: persisted in the `notifications` table and shown in the Alerts page.
- Slack/webhook: alert rules can store a Slack-compatible webhook URL; triggered alerts POST a payload to that URL.
- Email: SendGrid is used when `SENDGRID_API_KEY` is configured. Without a key, email notifications are still recorded with a configured status for local demos.

## Architecture notes

The backend is organized as routers, services, schemas, models, and worker tasks. Tenant isolation is enforced by attaching every business record to an `organization_id` and filtering queries through the current membership or API key organization.

The frontend is plain React.js with Vite rather than Next.js, matching the requested React implementation. If strict compliance with a Next.js-only assessment is required later, the page structure and API client can be migrated to Next.js App Router without changing the backend contract.

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

The included tests cover core auth service behavior, CSV ingestion parsing, rate limiting, and PDF report generation. The next useful test expansion would be API-level tests for tenant isolation, API key revocation, dashboard CRUD, and ingestion validation.
