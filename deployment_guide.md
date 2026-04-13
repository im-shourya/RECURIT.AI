# 🚀 RECRUIT.AI Deployment Guide

This guide will walk you through deploying the **RECRUIT.AI** platform using **Vercel** for the frontend and **Render** for the backend.

---

## 1. Prerequisites
- A **GitHub** account with your code pushed to a repository.
- A **Vercel** account (Free tier is fine).
- A **Render** account (Free tier is fine).
- (Recommended) A **Neon.tech** account for a free PostgreSQL database.
- (Recommended) An **Upstash.com** account for a free Redis instance.

---

## 2. Backend Deployment (Render)

### Using the Blueprint (Fastest)
I've already created a `render.yaml` file in your root directory.
1. Log in to [Render](https://dashboard.render.com/).
2. Click **New +** > **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect the `render.yaml` and set up:
   - **FastAPI Web Service** (the API)
   - **Celery Worker** (for background tasks)
   - **Postgres Database** (90-day free trial)
   - **Redis Instance**

### Environment Variables to Set on Render
After the initial deployment starts, go to the **recruit-ai-api** service > **Environment** and add/update these:
- `SECRET_KEY`: (Generate a long random string)
- `FRONTEND_URL`: `https://your-app.vercel.app` (Your Vercel URL)
- `AI_SERVICE_URL`: (Your AI service URL if deployed, otherwise leave default)
- `DATABASE_URL`: (If using Neon, paste your connection string here)
- `REDIS_URL`: (If using Upstash, paste your connection string here)

---

## 3. Frontend Deployment (Vercel)

1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New** > **Project**.
3. Connect your GitHub repository.
4. **Configure Project**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend` (I've renamed it from `fronted` to `frontend`)
5. **Environment Variables**:
   Add the following:
   - `NEXT_PUBLIC_API_URL`: `https://recruit-ai-api.onrender.com` (Your Render API URL)
6. Click **Deploy**.

---

## 4. Connecting the Two

> [!IMPORTANT]
> Once your Vercel app is deployed, copy its URL (e.g., `https://recruit-ai.vercel.app`) and update the `FRONTEND_URL` environment variable in your **Render API service**. This ensures that generated links (like interview tokens) point to the correct live site.

---

## 5. Database Migrations

The backend is configured to automatically create tables on startup (`create_tables()` in `main.py`). However, for production:
1. Use **Alembic** if you have existing migrations.
2. Run migrations by connecting to the Render Shell:
   ```bash
   alembic upgrade head
   ```

---

## 6. Recommended Free Tier Services

| Service | Recommended Provider | Why? |
| :--- | :--- | :--- |
| **Database** | [Neon](https://neon.tech) | Permanent free tier, better than Render's 90-day trial. |
| **Redis** | [Upstash](https://upstash.com) | Serverless Redis with a very generous free tier. |
| **Storage** | [Cloudinary](https://cloudinary.com) or S3 | For profile pictures and logo uploads. |

---

### Troubleshooting
- **CORS Issues**: Ensure `FRONTEND_URL` in the backend matches your Vercel URL exactly (no trailing slash).
- **Build Errors**: Check the Render logs to ensure `pip install` succeeded. Ensure the `rootDir` is set to `backend` in the Blueprint.
