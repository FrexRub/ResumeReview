# AGENTS.md

## Project

ResumeReview is a full-stack application with:

- a FastAPI backend in `src/`;
- an async SQLAlchemy/Alembic data layer backed by Supabase PostgreSQL;
- Redis-backed refresh-token sessions;
- a React + Vite + TypeScript frontend in `frontend/`;
- a backend-only proxy to ParserDoc for vacancy document parsing.

Keep the existing direction: API routers call small services/CRUD helpers, which use
SQLAlchemy models and injected infrastructure. Do not bypass these layers with
database or external-service calls from the frontend.

## Repository map

- `src/main.py` — FastAPI application, CORS, global router registration.
- `src/api_v1/` — versioned API features.
  - `auth/` — login, refresh, logout and refresh-session handling.
  - `users/` — current-user profile and password change.
  - `vacancies/` — protected ParserDoc proxy.
- `src/core/` — settings, database session, shared dependencies, JWT helpers.
- `src/models/` — SQLAlchemy ORM models.
- `alembic/` — migration environment and revision history.
- `tests/` — backend tests.
- `frontend/src/api/` — typed backend client and API contracts.
- `frontend/src/auth/` — in-memory authentication state and session restoration.
- `frontend/src/pages/` — route-level UI.
- `frontend/src/components/` — reusable UI.
- `frontend/src/**/*.test.tsx` — frontend tests.

Before changing a subsystem, inspect its neighboring modules and tests. Extend the
existing structure instead of creating parallel authentication, configuration, or
HTTP-client implementations.

## Supported API

The current public contracts are:

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/users/me`
- `POST /api/users/me/change-password`
- `POST /api/vacancies/parse`

Preserve response and error shapes unless the task explicitly requests an API
change. If a contract changes, update backend schemas, frontend types/client,
tests, and README examples together.

## Local setup and commands

Python 3.12+ and Node.js 20+ are expected. Commands below are PowerShell-friendly.

Backend:

```powershell
poetry install --with dev
poetry run alembic upgrade head
poetry run uvicorn src.main:app --reload
```

Backend checks:

```powershell
poetry run pytest -q
poetry run python -m compileall -q src tests
poetry check
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Frontend checks:

```powershell
cd frontend
npm test -- --run
npm run build
```

Prefer repository-local executables when Poetry is unavailable:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\uvicorn.exe src.main:app --reload
```

Do not claim a check passed unless it was actually run. If a service dependency
(PostgreSQL, Redis, or ParserDoc) prevents an integration check, report that
separately from unit-test results.

## Configuration

Configuration is environment-driven through `src/core/config.py`. Use `.env` only
for local secrets and never commit it.

Relevant settings include:

- Supabase/PostgreSQL connection fields;
- `SECRET_KEY`;
- access- and refresh-token lifetimes;
- `REDIS_URL`;
- `FRONTEND_URL`;
- refresh-cookie security settings;
- `PARSERDOC_URL`;
- ParserDoc timeout and maximum upload size.

Use a long, random `SECRET_KEY`. Production must use HTTPS and secure cookies.
`FRONTEND_URL` is an explicit allow-list; never replace it with wildcard CORS when
credentials are enabled.

When adding settings:

1. add a typed field with validation in `src/core/config.py`;
2. document it in `.env.example` and `README.md`;
3. inject the setting rather than reading environment variables throughout the
   application;
4. avoid real hosts, credentials, and tokens in tests.

## Authentication and security invariants

These rules are part of the product contract:

- Use `PyJWT`, not the unrelated `jwt` package.
- Passwords are bcrypt hashes; never store or log plaintext passwords.
- Access JWTs contain `sub`, `type`, `jti`, `auth_version`, `iat`, and `exp`.
- Access tokens are sent as Bearer tokens and kept only in frontend memory.
- Never put access or refresh tokens in `localStorage` or `sessionStorage`.
- Refresh JWTs live in an `HttpOnly` cookie and have a Redis session with matching
  TTL.
- Refresh rotation must be atomic: a refresh token is single-use.
- Logout revokes the current refresh session and clears the cookie.
- Password change increments `auth_version` and revokes every refresh session for
  the user, immediately invalidating older access tokens as well.
- Every authenticated request verifies token type, signature, expiry, active user,
  and `auth_version`.
- Authentication failures should not disclose whether a username exists.
- Redis failures at authentication boundaries must become controlled `503`
  responses, not raw connection errors.
- Do not add server-side cookie sessions or `SessionMiddleware`; JWT and Redis are
  the session model.

Changes to token claims, cookie paths, TTLs, Redis keys, or password policy require
tests for login, refresh rotation, logout, invalid/expired tokens, inactive users,
and revocation after password change.

## Database and migrations

The application uses async SQLAlchemy and Alembic. The user model is based on:

- `id`
- `name`
- `hashed_password`
- `is_active`
- `is_superuser`
- `registered_at`
- `auth_version`

Do not reintroduce unused `email`, `full_name`, or `is_verified` assumptions.

For schema changes:

1. update the ORM model;
2. create a new Alembic revision;
3. make upgrades safe for existing rows;
4. include a meaningful downgrade when practical;
5. verify the chain with `alembic upgrade head --sql`;
6. add or update tests.

Never edit a migration that may already have been applied. Never apply migrations
to Supabase or another shared database unless the user explicitly authorizes that
environment-changing action.

There is no public registration flow. Users are created manually with a unique
`name`, a bcrypt password hash, and `is_active=true`. Do not add seeded default
credentials.

## Backend conventions

- Keep route handlers thin: validation and HTTP mapping belong in views; reusable
  behavior belongs in services/CRUD helpers.
- Use Pydantic request/response schemas for public contracts.
- Use async database and network operations end to end.
- Inject database sessions, Redis, current users, and HTTP clients through FastAPI
  dependencies so tests can override them.
- Prefer explicit domain exceptions and controlled HTTP mappings over broad
  `except Exception`.
- Do not expose ORM objects without a response schema.
- Use timezone-aware UTC timestamps.
- Keep imports and package boundaries consistent with neighboring modules.

## ParserDoc proxy

The frontend must upload documents only to the backend. The backend proxies
multipart field `file` to `${PARSERDOC_URL}/parse`.

Current constraints:

- maximum size: 20 MB;
- allowed extensions: PDF, DOCX, DOC, RTF, XLS, TXT, CSV, HTML, JSON, XML;
- timeout: 120 seconds by default;
- parsed files and extracted text are not persisted.

Preserve the normalized result fields:

- `status`
- `filename`
- `mime_type`
- `source_type`
- `characters`
- `text`
- `warnings`

Map failures deliberately:

- oversized upload → `413`;
- unsupported or invalid document / ParserDoc validation → `422`;
- upstream unavailable or malformed response → `502`;
- upstream timeout → `504`.

Use the injectable ParserDoc HTTP-client dependency in tests. Do not make live
network calls in the automated test suite.

## Frontend conventions

- Use React, TypeScript, React Router, and CSS Modules already configured in
  `frontend/`.
- Keep API calls and refresh retry logic centralized in `frontend/src/api/client.ts`.
- Keep authentication state centralized in the auth provider/context.
- On application start, restore a session through the refresh cookie; do not
  persist JWTs in browser storage.
- Protected routes must wait for session restoration before redirecting.
- After a successful password change, clear local auth state and return to login.
- Never call ParserDoc directly from the browser.
- Keep user-facing copy in Russian unless the task requests localization.
- Reuse the existing editorial visual direction: light paper background, dark
  typography, and one contrasting accent.
- Support widths from 375 px through 1440 px.
- Every form control needs a visible label, keyboard focus state, and useful error
  text. Announce asynchronous errors/status where appropriate.
- Respect `prefers-reduced-motion`.
- Avoid `any`; keep API payloads and component props typed.

When adding dependencies, update `package.json` and `package-lock.json` together.
This application uses client-side React Router, not React Server Components.

## Tests

Behavior changes require focused tests close to the changed layer.

Backend tests should use dependency overrides and fakes/mocks for PostgreSQL,
Redis, and ParserDoc where possible. Cover both the successful path and meaningful
HTTP/error mappings.

Frontend tests use Vitest and Testing Library. Cover user-visible behavior rather
than internal component state, including:

- form validation;
- pending and error states;
- session restoration;
- protected-route redirects;
- upload validation and result rendering;
- logout after password change.

Before handing off a normal full-stack change, run at least:

```powershell
poetry run pytest -q
cd frontend
npm test -- --run
npm run build
```

Run live smoke checks against Supabase, Redis, or ParserDoc only when the required
configuration is present and the user has authorized changes to shared services.

## Scope boundaries

Unless a task explicitly expands scope, this iteration does not include:

- registration or password recovery;
- resume-to-vacancy matching;
- document or extracted-text persistence;
- analysis history;
- Docker Compose orchestration.

Avoid speculative infrastructure or abstractions for these future features.

## Working-tree and delivery rules

- Preserve unrelated user changes in a dirty working tree.
- Do not reset, delete, or rewrite user work to make checks pass.
- Do not commit, push, deploy, or modify shared external services unless asked.
- Do not commit `.env`, secrets, `node_modules/`, build output, coverage output, or
  browser-test artifacts.
- Keep generated lockfiles when dependencies legitimately change.
- Update README when setup, environment variables, commands, or public behavior
  changes.

A change is done when implementation, migrations (if any), frontend integration,
tests, and documentation agree; relevant checks pass; and any unverified
environment-dependent behavior is stated clearly in the handoff.
