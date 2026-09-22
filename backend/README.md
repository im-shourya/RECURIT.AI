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
| GET | `/api/apply/{token}` | — | Fetch drive info for form |
| POST | `/api/apply/{token}` | — | Submit application |
| POST | `/api/submit/{applicant_id}` | — | Task/GitHub submission |
| GET | `/api/applicants` | JWT | List applicants (filter by drive / status / search) |
| GET | `/api/applicants/{id}` | JWT | Applicant profile + submission + interview |
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

## Database

7 PostgreSQL tables: `organisations`, `drives`, `applicants`, `submissions`, `interviews`, `email_logs`, `password_reset_tokens`

See `../database/init.sql` for the raw SQL schema.
