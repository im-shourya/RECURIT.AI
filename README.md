<div align="center">

# RECRUIT.AI

### **AI-Powered Recruitment & Interview Platform**

*Hire smarter. Interview less. Five minutes per candidate, not five hours.*

[![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis_7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Gemini](https://img.shields.io/badge/Gemini_AI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)

<br/>

[Live Demo](https://recuritai.shouryaparashar.in) · [API Docs](https://recuritai.shouryaparashar.in/docs) · [Report Bug](https://github.com/im-shourya/RECURIT.AI/issues) · [Request Feature](https://github.com/im-shourya/RECURIT.AI/issues)

</div>

---

## Table of Contents

- [About](#about)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## About

**RECRUIT.AI** is a full-stack, AI-powered recruitment platform designed for college clubs, startups, and organizations to streamline their entire hiring pipeline. From creating a recruitment drive to conducting automated AI interviews — everything is handled in one place.

### The Problem
Traditional recruitment at scale involves:
- Manually screening hundreds of applications
- Scheduling and conducting repetitive first-round interviews
- Evaluating code submissions without standardized metrics
- Coordinating emails across multiple stages

### The Solution
RECRUIT.AI automates the entire funnel:

> **Create a drive → Share a link → AI screens, interviews & scores → You pick the best**

Organizations save **80% of interview time** while candidates get a fair, consistent evaluation through structured AI interviews with real-time integrity monitoring.

---

## Key Features

<table>
<tr>
<td width="50%">

### AI-Powered Interviews
Structured 3-round interviews that adapt to each candidate's profile, projects, and experience. Powered by **Gemini AI** with BERT-based answer evaluation.

</td>
<td width="50%">

### GitHub Integration
Automated repository analysis using **RepoLens** — evaluates code quality, tech stack, commit patterns, and project complexity via the GitAnalyser microservice.

</td>
</tr>
<tr>
<td width="50%">

### Video Proctoring
Real-time integrity checks using computer vision. Face detection and gaze tracking catch malpractice during AI interviews automatically.

</td>
<td width="50%">

### Smart Scoring
Multi-dimensional scoring across **communication**, **technical depth**, and **domain knowledge** with detailed breakdowns per interview round.

</td>
</tr>
<tr>
<td width="50%">

### QR Code Drives
Generate shareable links and QR codes for recruitment drives. Candidates can apply in under **30 seconds** — no sign-up required.

</td>
<td width="50%">

### Automated Emails
End-to-end email automation — application confirmations, task assignments, interview invitations, and selection results via **EmailJS**.

</td>
</tr>
<tr>
<td width="50%">

### Analytics Dashboard
Real-time analytics with charts showing applicant flow, score distributions, drive performance, and conversion funnels via **Recharts**.

</td>
<td width="50%">

### Dark Mode
Premium design with full dark/light theme support, glassmorphism effects, smooth Framer Motion animations, and responsive layouts.

</td>
</tr>
</table>

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         RECRUIT.AI                               │
├──────────────┬──────────────────┬───────────────┬────────────────┤
│   Frontend   │    Backend API   │  AI / ML      │  Infrastructure│
│  (Next.js)   │   (FastAPI)      │ (GitAnalyser) │                │
├──────────────┼──────────────────┼───────────────┼────────────────┤
│              │                  │               │                │
│  Landing     │  Auth (JWT)      │  Repo Clone   │  PostgreSQL    │
│  Dashboard   │  Drives CRUD     │  File Filter  │  Redis         │
│  Apply Form  │  Applications    │  Gemini LLM   │  Celery        │
│  Task Submit │  Interviews      │  Tech Stack   │  Docker        │
│  AI Interview│  Analytics       │  Architecture │  S3 (Uploads)  │
│  Settings    │  Email (EmailJS) │  Code Quality │  Render / Vercel│
│              │  QR Generation   │  Q&A Engine   │                │
│              │  Celery Workers  │  WebSocket    │                │
│              │                  │               │                │
└──────┬───────┴────────┬─────────┴───────┬───────┴────────────────┘
       │                │                 │
       │    REST API    │   Internal API  │
       │  (Port 3000)   │  (Port 8000)    │  (Port 8001)
       ▼                ▼                 ▼
   ┌────────┐     ┌──────────┐     ┌──────────────┐
   │ Vercel │     │  Render  │     │   Railway    │
   │ (CDN)  │     │ (API+DB) │     │  (AI Svc)   │
   └────────┘     └──────────┘     └──────────────┘
```

### How the AI Interview Works

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Start  │────▶│  Round 1    │────▶│   Round 2    │────▶│   Round 3   │
│Interview│     │ Introduction│     │ Project Deep │     │   Domain    │
│         │     │   (60s)     │     │  Dive (90s)  │     │ Knowledge   │
└─────────┘     │             │     │              │     │   (90s)     │
                │ "Tell us    │     │ Questions on │     │ Technical   │
                │  about      │     │ your GitHub  │     │ questions   │
                │  yourself"  │     │ projects or  │     │ at org-set  │
                │             │     │ task work    │     │ difficulty  │
                └─────────────┘     └──────────────┘     └──────┬──────┘
                                                                │
                                                                ▼
                                                        ┌──────────────┐
                                                        │  AI Scoring  │
                                                        │ ────────────── │
                                                        │ Communication│
                                                        │ Technical    │
                                                        │ Domain       │
                                                        │ Total /100   │
                                                        └──────────────┘
```

---

## Tech Stack

### Frontend
| Technology | Purpose |
|:-----------|:--------|
| **Next.js 16** | React framework with App Router & SSR |
| **TypeScript** | Type-safe development |
| **Tailwind CSS 4** | Utility-first styling |
| **Framer Motion** | Animations & transitions |
| **Radix UI** | Accessible headless components |
| **shadcn/ui** | Polished component library |
| **Recharts** | Data visualization & charts |
| **React Hook Form + Zod** | Form handling & validation |
| **next-themes** | Dark/light theme management |

### Backend
| Technology | Purpose |
|:-----------|:--------|
| **FastAPI** | High-performance async Python API |
| **SQLAlchemy 2.0** | ORM with async support |
| **Alembic** | Database migration management |
| **Celery + Redis** | Background task processing |
| **python-jose** | JWT authentication |
| **bcrypt** | Password hashing |
| **boto3** | AWS S3 file uploads |
| **qrcode** | QR code generation |
| **Pydantic v2** | Request/response validation |

### AI / ML — GitAnalyser
| Technology | Purpose |
|:-----------|:--------|
| **Gemini 3 (Flash/Pro)** | LLM for repo analysis & interviews |
| **FastAPI** | Microservice API |
| **SQLite + async SQLAlchemy** | Lightweight analysis storage |
| **httpx** | Async GitHub API client |
| **WebSocket** | Real-time analysis progress |
| **slowapi** | Rate limiting |

### Infrastructure
| Technology | Purpose |
|:-----------|:--------|
| **PostgreSQL 16** | Primary relational database |
| **Redis 7** | Caching & Celery message broker |
| **Docker Compose** | Local development orchestration |
| **Render** | Backend & worker deployment |
| **Vercel** | Frontend hosting & CDN |
| **Railway** | AI microservice deployment |

---

## Getting Started

### Prerequisites

- **Node.js** >= 18.x
- **Python** >= 3.9
- **Docker & Docker Compose** (for PostgreSQL + Redis)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/im-shourya/RECURIT.AI.git
cd RECURIT.AI
```

### 2. Start Infrastructure Services

```bash
docker-compose up -d
```

This spins up:
- **PostgreSQL 16** on `localhost:5432` (auto-runs `database/init.sql`)
- **Redis 7** on `localhost:6379`

### 3. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section)

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

> API documentation available at [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variable
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

> Frontend available at [http://localhost:3000](http://localhost:3000)

### 5. AI Service Setup (Optional)

```bash
cd aiml/GitAnalyser

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GEMINI_API_KEY and GITHUB_TOKEN

# Start the AI service
python main.py
```

> GitAnalyser API at [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Project Structure

```
RECRUIT.AI/
│
├── frontend/                    # Next.js 16 application
│   ├── app/
│   │   ├── (dashboard)/         # Protected dashboard routes
│   │   │   └── dashboard/
│   │   │       ├── page.tsx     # Main dashboard (drives, stats)
│   │   │       ├── drives/      # Drive management pages
│   │   │       ├── analytics/   # Analytics & charts
│   │   │       └── settings/    # Organization settings
│   │   ├── auth/                # Login & registration
│   │   ├── apply/[token]/       # Public application form
│   │   ├── submit/[applicantId]/ # Task/GitHub submission
│   │   ├── interview/[token]/   # AI interview interface
│   │   ├── privacy/             # Privacy policy
│   │   ├── terms/               # Terms of service
│   │   ├── layout.tsx           # Root layout (fonts, SEO, theme)
│   │   ├── page.tsx             # Landing page
│   │   ├── globals.css          # Global styles & design tokens
│   │   ├── sitemap.ts           # Dynamic sitemap generation
│   │   └── robots.ts            # Robots.txt configuration
│   ├── components/
│   │   ├── landing/             # Landing page sections
│   │   │   ├── hero-section.tsx
│   │   │   ├── features-section.tsx
│   │   │   ├── how-it-works-section.tsx
│   │   │   ├── trusted-by-section.tsx
│   │   │   └── cta-section.tsx
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── navbar.tsx
│   │   ├── footer.tsx
│   │   └── animated-background.tsx
│   ├── hooks/                   # Custom React hooks
│   ├── lib/                     # Utility functions
│   └── public/                  # Static assets (favicon, OG image)
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py              # App entry point & CORS config
│   │   ├── config.py            # Pydantic settings from .env
│   │   ├── db.py                # SQLAlchemy session management
│   │   ├── models/
│   │   │   ├── database.py      # ORM models (6 tables)
│   │   │   └── schemas.py       # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py          # /api/auth/* — JWT auth
│   │   │   ├── drives.py        # /api/drives/* — CRUD + QR
│   │   │   ├── applicants.py    # /api/apply/*, /api/submit/*
│   │   │   ├── interviews.py    # /api/interview/* — AI interview
│   │   │   └── analytics.py     # /api/analytics/* — stats
│   │   └── services/
│   │       ├── auth_service.py  # JWT + password hashing
│   │       ├── email_service.py # EmailJS integration
│   │       └── qr_service.py    # QR code generation
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   └── .env.example
│
├── aiml/                        # AI/ML microservices
│   └── GitAnalyser/             # GitHub repository analyzer
│       ├── main.py              # FastAPI app (Gemini + WebSocket)
│       ├── routes/              # API & WebSocket routes
│       ├── services/            # Analysis, Gemini, comparison
│       ├── models/              # Pydantic schemas
│       ├── db/                  # SQLite database layer
│       ├── utils/               # Rate limiting, logging
│       └── tests/               # pytest test suite
│
├── database/
│   └── init.sql                 # PostgreSQL schema (6 tables, enums, indexes)
│
├── docker-compose.yml           # PostgreSQL + Redis for local dev
└── render.yaml                  # Render deployment blueprint
```

---

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|:------:|:---------|:----:|:------------|
| `POST` | `/api/auth/register` | — | Register new organization |
| `POST` | `/api/auth/login` | — | Login, returns JWT token |
| `GET`  | `/api/auth/me` | JWT | Get current org profile |

### Recruitment Drives

| Method | Endpoint | Auth | Description |
|:------:|:---------|:----:|:------------|
| `POST` | `/api/drives` | JWT | Create drive (generates link + QR) |
| `GET`  | `/api/drives` | JWT | List all org drives |
| `GET`  | `/api/drives/{id}` | JWT | Drive details + applicants |
| `PATCH`| `/api/drives/{id}/status` | JWT | Open / close drive |

### Applications

| Method | Endpoint | Auth | Description |
|:------:|:---------|:----:|:------------|
| `GET`  | `/api/apply/{token}` | — | Fetch drive info for form |
| `POST` | `/api/apply/{token}` | — | Submit application |
| `POST` | `/api/submit/{applicant_id}` | — | Upload task / GitHub submission |

### AI Interviews

| Method | Endpoint | Auth | Description |
|:------:|:---------|:----:|:------------|
| `GET`  | `/api/interview/{token}` | — | Get interview config |
| `POST` | `/api/interview/{token}/start` | — | Begin AI interview |
| `POST` | `/api/interview/{token}/answer` | — | Submit answer, get next question |
| `POST` | `/api/interview/{token}/end` | — | End & score interview |
| `GET`  | `/api/interview/{token}/detail` | — | Full interview detail + scores |

### GitAnalyser (AI Microservice)

| Method | Endpoint | Description |
|:------:|:---------|:------------|
| `POST` | `/api/analyze-repo` | Start async repository analysis |
| `GET`  | `/api/status/{repo_id}` | Check analysis progress |
| `GET`  | `/api/analysis/{repo_id}` | Get analysis results |
| `POST` | `/api/ask` | Ask questions about a repo |
| `GET`  | `/api/code-quality/{repo_id}` | Code quality metrics |
| `POST` | `/api/compare` | Compare multiple repositories |
| `WS`   | `/ws/analysis/{repo_id}` | Real-time progress updates |

---

## Database Schema

PostgreSQL with **6 core tables** and **5 custom enum types**:

```sql
┌──────────────────┐       ┌──────────────────┐
│  organisations   │───1:N─│     drives       │
│──────────────────│       │──────────────────│
│ id (UUID, PK)    │       │ id (UUID, PK)    │
│ name             │       │ org_id (FK)      │
│ email (UNIQUE)   │       │ name, domain     │
│ password_hash    │       │ task_type (ENUM) │
│ description      │       │ question_level   │
│ domain_tags[]    │       │ apply_deadline   │
│ logo_url         │       │ link_token       │
│ created_at       │       │ qr_code_url      │
└──────────────────┘       │ status (ENUM)    │
                           └────────┬─────────┘
                                    │ 1:N
                           ┌────────▼─────────┐
                           │   applicants     │
                           │──────────────────│
                           │ id (UUID, PK)    │
                           │ drive_id (FK)    │
                           │ name, email      │
                           │ skills[]         │
                           │ github_url       │
                           │ status (ENUM)    │
                           └──┬──────────┬────┘
                              │ 1:1      │ 1:1
                    ┌─────────▼──┐  ┌────▼──────────┐
                    │ submissions │  │  interviews   │
                    │────────────│  │───────────────│
                    │ file_url   │  │ token         │
                    │ github_url │  │ transcript[]  │
                    │ description│  │ score_intro   │
                    │ repolens   │  │ score_project │
                    │ _analysis  │  │ score_domain  │
                    │ (JSONB)    │  │ total_score   │
                    └────────────┘  │ malpractice[] │
                                   └───────────────┘

                    ┌──────────────┐
                    │  email_logs  │
                    │──────────────│
                    │ applicant_id │
                    │ type (ENUM)  │
                    │ sent_at      │
                    │ emailjs_id   │
                    └──────────────┘
```

**Enum Types:** `task_type_enum`, `question_level_enum`, `drive_status_enum`, `applicant_status_enum`, `email_type_enum`

---

## Deployment

### Render (Backend + Workers)

The project includes a [`render.yaml`](render.yaml) blueprint for one-click deploy:

```bash
# Deploy to Render
# 1. Push to GitHub
# 2. Connect repo on Render Dashboard
# 3. Use "Blueprint" and point to render.yaml
```

Services deployed:
- **recruit-ai-api** — FastAPI web service (Uvicorn)
- **recruit-ai-worker** — Celery background worker
- **recruit-ai-redis** — Managed Redis instance
- **recruit-ai-db** — Managed PostgreSQL database

### Vercel (Frontend)

```bash
cd frontend
npx vercel --prod
```

> Set `NEXT_PUBLIC_API_URL` to your Render backend URL in Vercel environment variables.

### Docker (Local Development)

```bash
# Start all infrastructure
docker-compose up -d

# Verify services are healthy
docker-compose ps
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|:---------|:--------:|:------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing secret |
| `ALGORITHM` | — | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | Token TTL (default: `1440`) |
| `REDIS_URL` | Yes | Redis connection string |
| `FRONTEND_URL` | Yes | Frontend URL for link generation |
| `AI_SERVICE_URL` | — | GitAnalyser URL (default: `http://localhost:8001`) |
| `S3_BUCKET_NAME` | — | AWS S3 bucket for uploads |
| `AWS_ACCESS_KEY_ID` | — | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | — | AWS credentials |
| `EMAILJS_SERVICE_ID` | — | EmailJS service identifier |
| `EMAILJS_PUBLIC_KEY` | — | EmailJS public key |
| `EMAILJS_PRIVATE_KEY` | — | EmailJS private key |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|:---------|:--------:|:------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API base URL |

### GitAnalyser (`aiml/GitAnalyser/.env`)

| Variable | Required | Description |
|:---------|:--------:|:------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `GEMINI_MODEL` | — | `flash` (default) or `pro` |
| `GITHUB_TOKEN` | — | GitHub PAT for higher rate limits |

---

## Contributing

Contributions are welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Tips

- Backend API docs auto-reload at `/docs` during development
- Frontend uses hot reload with `next dev`
- Run `alembic revision --autogenerate -m "description"` for DB migrations
- GitAnalyser falls back to mock responses if `GEMINI_API_KEY` is missing

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ by [Shourya Parashar](https://shouryaparashar.in)**

Star this repo if you found it helpful!

</div>
