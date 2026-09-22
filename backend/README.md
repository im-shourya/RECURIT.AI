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
| POST | `/api/submit/{applicant_id}` | — | Task/GitHub submission |
| POST | `/api/submit/{applicant_id}/upload` | — | Upload a submission file (max 10MB) |
| GET | `/api/applicants` | JWT | List applicants (filter by drive / status / search) |
| GET | `/api/applicants/export` | JWT | CSV export (same filters as list) |
| GET | `/api/applicants/{id}` | JWT | Applicant profile + submission + interview |
| GET | `/api/applicants/{id}/submission-file` | JWT | Short-lived download link |
| POST | `/api/applicants/{id}/resend-email` | JWT | Re-send applied / task / interview / result |
| POST | `/api/applicants/bulk-decision` | JWT | Decide up to 100 applicants at once |
| POST | `/api/applicants/{id}/decision` | JWT | Record hire / reject, email the result |
| GET | `/api/interview/{token}` | — | Get interview config |
| POST | `/api/interview/{token}/start` | — | Begin interview |
| POST | `/api/interview/{token}/answer` | — | Submit answer, get next Q |
| POST | `/api/interview/{token}/end` | — | End & score interview |
| GET | `/api/interview/{token}/detail` | — | Full interview detail |

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

## Database

7 PostgreSQL tables: `organisations`, `drives`, `applicants`, `submissions`, `interviews`, `email_logs`, `password_reset_tokens`

See `../database/init.sql` for the raw SQL schema.
