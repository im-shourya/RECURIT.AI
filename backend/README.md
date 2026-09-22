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
│       ├── rate_limit.py       # Redis or in-process limiting
│       └── qr_service.py       # QR code generation
├── tests/                      # 300 tests, real queries via mongomock-motor
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
| GET | `/api/team` | JWT | List organisation members |
| POST | `/api/team` | owner | Invite a member |
| PATCH | `/api/team/{id}` | owner | Change a member's role |
| DELETE | `/api/team/{id}` | owner | Remove a member |
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

`audit_log` is deliberately *not* embedded. It has to outlive the documents it
describes, or erasing a candidate would also erase the record that they were
erased.

### Referential integrity

There is none at the database level. Every cascade PostgreSQL used to enforce
now lives in `app/services/cascade.py`, deliberately in one file: a delete
added elsewhere that skips it leaves orphans, and MongoDB will not object.
`cascade.count_orphans()` is the diagnostic for exactly that.
