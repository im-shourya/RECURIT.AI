"""
Production FastAPI Application - Final Hardened Version
Features:
- Proper async status flow
- Split table architecture
- Guaranteed persistence
- Single Gemini call per repo
- Zero Gemini calls in /api/ask
- Rate limiting
- Structured logging
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded

from db.database import init_db
from db.migration import add_diagram_column
from routes.api import router
from utils.rate_limiter import get_limiter
from utils.logger import get_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager with proper database initialization."""
    # Startup
    print("=" * 80)
    print("🚀 GitHub Repository Analyzer - Production")
    print("=" * 80)
    
    print("\n📊 Initializing database...")
    await init_db()
    await add_diagram_column()   # safe no-op if column already exists
    print("✅ Database initialized successfully")
    
    # Print configuration
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "flash")
    
    print("\n🤖 AI Configuration:")
    if api_key:
        model_name = "Gemini 3 Pro" if model.lower() == "pro" else "Gemini 3 Flash"
        print(f"  ✅ {model_name} configured")
        print(f"  ✅ API Key: {'*' * 20}{api_key[-8:]}")
    else:
        print("  ⚠️  No GEMINI_API_KEY - using mock mode")
        print("  💡 Set GEMINI_API_KEY in .env for AI analysis")
    
    print("\n⚡ Architecture:")
    print("  ✅ Status-based async flow (Option A)")
    print("  ✅ Split table storage (normalized)")
    print("  ✅ Single Gemini call per repository")
    print("  ✅ Zero Gemini calls in /api/ask")
    print("  ✅ Proper SQLite persistence")
    print("  ✅ Idempotent Q&A operations")
    
    print("\n🌐 Endpoints:")
    print("  POST   /api/analyze-repo     - Start analysis")
    print("  GET    /api/status/{id}      - Check status")
    print("  GET    /api/analysis/{id}    - Get results")
    print("  POST   /api/ask              - Ask questions")
    print("  GET    /api/health           - Health check")
    
    print("\n" + "=" * 80)
    print("✅ Application started successfully")
    print("=" * 80 + "\n")
    
    yield
    
    # Shutdown
    print("\n👋 Application shutting down...")


# Create FastAPI app
app = FastAPI(
    title="GitHub Repository Analyzer - Production",
    description="Hardened system with proper async flow and guaranteed persistence",
    version="3.0.0-final",
    lifespan=lifespan
)

# Add rate limiter
limiter = get_limiter()
app.state.limiter = limiter

# Add rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["analysis"])

# Include WebSocket routes
from routes.websocket import router as ws_router
app.include_router(ws_router, tags=["websocket"])

# Serve index.html at root and for SPA routing (all non-API routes)
@app.get("/")
async def serve_root():
    """Serve index.html at root."""
    import os
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"error": "index.html not found"}


@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve index.html for SPA routing (catch-all for non-API, non-static routes)."""
    # Skip if it looks like an API call or static asset with extension
    if path.startswith("api") or "." in path.split("/")[-1]:
        return JSONResponse({"error": "Not found"}, status_code=404)
    
    import os
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return JSONResponse({"error": "index.html not found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn
    
    # Use PORT from environment (Railway/Heroku) or default to 8000 for local dev
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["routes", "services", "models", "utils", "db"],
        log_level="info"
    )
