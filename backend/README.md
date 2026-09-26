# RECRUIT.AI — Backend

FastAPI-powered backend for the AI recruitment platform.

## Quick Start

### 1. Start PostgreSQL & Redis
```bash
# From the project root
docker-compose up -d
```

### 2. Create Python virtual environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Open API docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # Pydantic settings from .env
│   ├── db.py                 # SQLAlchemy session management
│   ├── models/
│   │   ├── database.py       # ORM models (6 tables)
│   │   └── schemas.py        # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py           # /api/auth/*
│   │   ├── drives.py         # /api/drives/*
│   │   ├── applicants.py     # /api/apply/*, /api/submit/*
│   │   └── interviews.py     # /api/interview/*
│   └── services/
│       ├── auth_service.py   # JWT + password hashing
│       ├── email_service.py  # EmailJS integration
│       └── qr_service.py     # QR code generation
├── alembic/                  # Database migrations
├── alembic.ini
├── requirements.txt
├── .env / .env.example
└── .gitignore
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | — | Org registration |
| POST | `/api/auth/login` | — | Returns JWT |
| GET | `/api/auth/me` | JWT | Current org profile |
| PATCH | `/api/auth/me` | JWT | Update org profile |
| POST | `/api/auth/change-password` | JWT | Change org password |
| POST | `/api/auth/forgot-password` | — | Request a reset link (always 204) |
| POST | `/api/auth/reset-password` | — | Consume a reset token, set new password |
| POST | `/api/drives` | JWT | Create drive (returns link + QR) |
| GET | `/api/drives` | JWT | List org drives |
| GET | `/api/drives/{id}` | JWT | Drive detail + applicants |
| PATCH | `/api/drives/{id}/status` | JWT | Open / close drive |
| PATCH | `/api/drives/{id}` | JWT | Edit drive details |
| DELETE | `/api/drives/{id}` | JWT | Delete drive (`?confirm=true` if it has applicants) |
| GET | `/api/apply/{token}` | — | Fetch drive info for form |
| POST | `/api/apply/{token}` | — | Submit application |
| POST | `/api/submit/{submit_token}` | token | Task/GitHub submission |
| POST | `/api/submit/{submit_token}/upload` | token | Upload a submission file (max 10MB) |
| GET | `/api/applicants` | JWT | List applicants (filter / search; `X-Total-Count` header) |
| GET | `/api/applicants/export` | JWT | CSV export (same filters as list) |
| GET | `/api/applicants/{id}` | JWT | Applicant profile + submission + interview |
| GET | `/api/applicants/{id}/submission-file` | JWT | Short-lived download link |
| POST | `/api/applicants/{id}/resend-email` | JWT | Re-send applied / task / interview / result |
| POST | `/api/applicants/bulk-decision` | JWT | Decide up to 100 applicants at once |
| DELETE | `/api/applicants/{id}` | JWT | Erase a candidate and their stored files |
| GET | `/api/audit` | JWT | This organisation's audit trail |
| GET | `/api/status/{submit_token}` | token | Candidate's own application status |
| POST | `/api/applicants/{id}/decision` | JWT | Record hire / reject, email the result |
| GET | `/api/interview/{token}` | — | Get interview config |
| POST | `/api/interview/{token}/start` | — | Begin interview |
| POST | `/api/interview/{token}/answer` | — | Submit answer, get next Q |
| POST | `/api/interview/{token}/end` | — | End & score interview |
| POST | `/api/interview/{token}/recording` | token | Upload the interview recording |
| GET | `/api/interview/{token}/detail` | JWT | Full interview detail (org only) |

## Tests

```bash
./venv/bin/python -m pytest tests/ -q
```

The suite runs without a database. It covers the authentication boundary, the
organisation-scoping filter (asserted against the compiled SQL) and request
validation. End-to-end behaviour against PostgreSQL is not yet covered.

## File uploads

Submission files go to S3 (or any S3-compatible endpoint, e.g. MinIO via
`S3_ENDPOINT_URL`). Uploads need `S3_BUCKET_NAME` plus either AWS credentials
or an endpoint URL; without them the upload endpoint returns a clear `503`
rather than failing obscurely.

Objects are stored **private**. Recruiters read them through short-lived
presigned URLs from `/api/applicants/{id}/submission-file`, so the bucket never
needs public access. Allowed types: pdf, zip, doc, docx, png, jpg, txt, md.
## Email

Transactional email goes through [Resend](https://resend.com). Templates live
in `app/services/email_templates.py` and ship with the code, so message content
is versioned and reviewable rather than living in a third-party dashboard.

Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL`; the sender domain must be
verified in Resend. Without them, sends are skipped and logged rather than
failing the request that queued them.

Five templates: application received, task assigned, interview invitation,
decision result (selected / rejected), password reset. Each is sent as HTML
plus a plain-text alternative, with the logo and a footer carrying support and
policy links.

## Migrations

Alembic owns the schema.

```bash
alembic upgrade head          # apply
alembic revision --autogenerate -m "describe change"
alembic upgrade head --sql    # preview SQL without touching a database
```

**On a database that already has these tables** (they were created by
`create_all` on startup before Alembic was wired up), do not run the baseline
— mark it as already applied:

```bash
alembic stamp baseline_0001
```

`AUTO_CREATE_TABLES` is off by default. `create_all()` only ever creates
*missing* tables — it never alters an existing one — so relying on it where
data matters means a changed column is silently skipped and the app runs
against a schema it does not have. Turn it on only for a throwaway local
database.

## Security notes

- Public candidate routes are reached by **unguessable token**, never by a
  database id. `submit_token` guards submission; `link_token` guards apply;
  interview links carry their own token and expire after
  `INTERVIEW_TOKEN_TTL_DAYS` (default 14).
- `/api/interview/{token}/detail` requires a signed-in organisation and is
  scoped to that organisation's drives.
- `CORS_ALLOWED_ORIGINS` must list exact origins. `*` is rejected at startup:
  a wildcard is invalid on credentialed requests and browsers reject it.
- Sign-in, registration, password reset and public application are rate
  limited. Counters use Redis when `REDIS_URL` is reachable, which makes the
  limit exact and shared across workers; otherwise they fall back to process
  memory, which is approximate. If Redis is configured but unreachable the
  limiter degrades to memory rather than failing closed.
- Set `SENTRY_DSN` to enable error tracking. It is off by default, sends no
  PII, drops request bodies and redacts credential headers before anything
  leaves the process.

## Logging and health

Logs are structured: readable text when `ENVIRONMENT=development`, one JSON
object per line otherwise, so hosted log viewers can index the fields.
Level via `LOG_LEVEL`.

`GET /health` runs `SELECT 1` and returns **503** when the database is
unreachable. It previously returned healthy unconditionally, so it stayed
green through an outage.

## Background work

Outbound email is written to the `email_outbox` table before delivery is
attempted, so the intent to send survives a restart. A sweeper retries
anything left pending every `OUTBOX_SWEEP_INTERVAL_SECONDS`, giving up after
five attempts and leaving the row as `failed` for inspection.

This is not a distributed queue — one sweeper per process, no lock — but it
closes the failure that mattered: an email vanishing with no record it was
ever attempted. `celery` remains out of requirements; it was declared and
never imported, advertising a guarantee the code did not provide.

`redis` stays in requirements for moving rate-limit counters out of process
memory, which is the next step for exact, shared limits.

## Audit and data rights

Consequential actions — hiring decisions, candidate deletion, drive
create/delete, password change — are appended to `audit_log`, scoped to the
organisation and readable at `GET /api/audit`. There is no endpoint to edit or
delete an entry: a trail that can be rewritten answers nothing.

The table has **no foreign key to applicants** on purpose. It must outlive the
rows it describes, so erasing a candidate cannot also erase the record that
they were erased; the subject is stored as an id plus a label captured at the
time.

`DELETE /api/applicants/{id}` erases a candidate, their submission, interview,
transcript and email log, and removes their stored files from object storage.
This is what makes a deletion request answerable — the service stores names,
email addresses, transcripts, scores and recordings of identifiable people.

## Database

7 PostgreSQL tables: `organisations`, `drives`, `applicants`, `submissions`, `interviews`, `email_logs`, `password_reset_tokens`

See `../database/init.sql` for the raw SQL schema.
