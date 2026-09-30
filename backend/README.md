# RECRUIT.AI — Backend

FastAPI-powered backend for the AI recruitment platform.

## Quick Start

### 1. Start MongoDB & Redis
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
│   ├── main.py                 # FastAPI app, CORS, lifespan, /health
│   ├── config.py               # Pydantic settings from .env
│   ├── db.py                   # Motor client + Beanie initialisation
│   ├── logging_config.py       # Structured (JSON) logging
│   ├── error_tracking.py       # Optional Sentry wiring
│   ├── models/
│   │   ├── documents.py        # Beanie documents (7 collections)
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py             # /api/auth/*
│   │   ├── team.py             # /api/team/*
│   │   ├── drives.py           # /api/drives/*
│   │   ├── applicants.py       # /api/apply/*, /api/submit/*, /api/status/*
│   │   ├── applicant_admin.py  # /api/applicants/*
│   │   ├── interviews.py       # /api/interview/*
│   │   ├── analytics.py        # /api/analytics/*
│   │   └── audit.py            # /api/audit
│   └── services/
│       ├── auth_service.py     # JWT, password + reset-token hashing
│       ├── cascade.py          # Deletion cascades (no FKs in MongoDB)
│       ├── audit.py            # Append-only audit writes
│       ├── email_service.py    # Resend transport
│       ├── email_templates.py  # Branded HTML + text templates
│       ├── email_outbox.py     # Durable queue + retry sweeper
│       ├── storage_service.py  # S3 uploads and presigned reads
│       └── rate_limit.py       # Redis or in-process limiting
├── tests/                      # 300 tests, real queries via mongomock-motor
├── requirements.txt
├── .env / .env.example
└── .gitignore
```

## Sessions

The session JWT lives in an `httpOnly`, `SameSite=Lax` cookie scoped to
`/api` (and `Secure` in production), so no script on the page can read it.
The browser reaches the API through the frontend's own origin, where
`next.config.mjs` rewrites `/api/*` to this service. That keeps the cookie
first-party; if the API set it on its own domain, the browser would treat it
as a third-party cookie and Safari would drop it.

A write that authenticates with the cookie must also send
`X-Requested-With`, which a cross-site form cannot add. Non-browser clients
can still send `Authorization: Bearer <token>` instead.

"JWT" in the table below means either of those.

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | — | Org registration |
| POST | `/api/auth/login` | — | Sets the session cookie, returns the profile |
| POST | `/api/auth/logout` | — | Clears the session cookie |
| POST | `/api/auth/switch` | JWT | Move the session to another organisation the caller belongs to |
| GET | `/api/auth/me` | JWT | Current org profile |
| PATCH | `/api/auth/me` | admin | Update org profile |
| POST | `/api/auth/change-password` | JWT | Change your password; signs out every other session and sets a fresh cookie |
| POST | `/api/auth/forgot-password` | — | Request a reset link (always 204) |
| POST | `/api/auth/reset-password` | — | Consume a reset token, set new password |
| GET | `/api/team` | JWT | List organisation members |
| POST | `/api/team` | owner | Invite a member |
| PATCH | `/api/team/{id}` | owner | Change a member's role |
| DELETE | `/api/team/{id}` | owner | Remove a member |
| POST | `/api/drives` | JWT | Create drive (returns its apply-link token) |
| GET | `/api/drives` | JWT | List org drives |
| GET | `/api/drives/{id}` | JWT | Drive detail + applicants |
| PATCH | `/api/drives/{id}/status` | JWT | Open / close drive |
| PATCH | `/api/drives/{id}` | JWT | Edit drive details |
| DELETE | `/api/drives/{id}` | JWT | Delete drive (`?confirm=true` if it has applicants) |
| GET | `/api/apply/{token}` | — | Fetch drive info for form |
| POST | `/api/apply/{token}` | — | Submit application |
| POST | `/api/submit/{submit_token}` | token | Task submission; the candidate then waits for a recruiter |
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
| POST | `/api/applicants/{id}/invite` | JWT | Invite a submitted candidate to interview |
| POST | `/api/applicants/{id}/decision` | JWT | Record hire / reject, email the result |
| GET | `/api/interview/{token}` | — | Get interview config |
| POST | `/api/interview/{token}/start` | — | Begin interview |
| POST | `/api/interview/{token}/answer` | — | Submit answer, get next Q |
| POST | `/api/interview/{token}/end` | — | End & score interview |
| POST | `/api/interview/{token}/recording` | token | Upload the interview recording |
| GET | `/api/interview/{token}/detail` | JWT | Full interview detail (org only) |

## Tests

```bash
pip install -r requirements-dev.txt
./venv/bin/python -m pytest tests/ -q
```

The suite needs no database server. `mongomock-motor` provides an in-process
MongoDB that Beanie initialises against normally, so tests run real queries,
including requests driven through the FastAPI app. The stand-in does not
enforce unique indexes, so the uniqueness tests check that each index is
declared rather than that it is enforced.

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

## Migrating existing PostgreSQL data

The code change moves where *new* data is written. Existing rows move with:

```bash
pip install psycopg2-binary   # not a runtime dependency

DATABASE_URL=postgresql://... MONGODB_URL=mongodb://... \
    python scripts/migrate_postgres_to_mongo.py --dry-run
```

Drop `--dry-run` to write. Safe to re-run: documents are upserted by their
existing id, so an interrupted run can simply be repeated. Ids are preserved,
which is what keeps links already emailed to candidates resolving afterwards.

Not a dump/restore — `submissions`, `interviews` and `email_logs` are joined
and nested into the applicant document on the way across.

## Schema and indexes

MongoDB is schemaless, so there are no migrations. Document shape is defined
in `app/models/documents.py` and validated by Pydantic on the way in and out.

The indexes declared on each model — including every uniqueness rule that used
to be a table constraint — are created by `init_beanie` on every startup. That
is the closest thing to a migration step here, and it is not optional: without
it, nothing stops two applications to the same drive from the same email.

Adding a field is a code change alone. **Removing or renaming one leaves the
old key on existing documents**, so a rename needs a one-off backfill script;
nothing will warn you.

## Database

7 MongoDB collections: `organisations`, `users`, `drives`, `applicants`,
`password_reset_tokens`, `audit_log`, `email_outbox`.

`submissions`, `interviews` and `email_logs` are no longer separate: each was
either 1:1 with an applicant or an append-only list only ever read through
one, so they are **embedded in the applicant document**. That removes three
collections, three joins and three cascade rules.

Each embedded email-log entry carries the `outbox_id` of the `email_outbox`
document that sends it. It reads `pending` until the outbox delivers the
message (`sent`, with the Resend message id) or gives up on it (`failed`), so
the log never shows a delivery that did not happen.

A `users` document is one person's membership of one organisation, unique on
`(email, org_id)`. The same person can therefore belong to several
organisations. The memberships they have accepted share one password, so
changing or resetting it on one changes it on all and signs out every session.
`app/db.py` drops the old deployment-wide unique `email_1` index on boot,
because `init_beanie` only ever creates indexes and never drops them.

`audit_log` is deliberately *not* embedded. It has to outlive the documents it
describes, or erasing a candidate would also erase the record that they were
erased.

### Referential integrity

There is none at the database level. Every cascade PostgreSQL used to enforce
now lives in `app/services/cascade.py`, deliberately in one file: a delete
added elsewhere that skips it leaves orphans, and MongoDB will not object.
`cascade.count_orphans()` is the diagnostic for exactly that.
