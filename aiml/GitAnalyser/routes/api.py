"""
Production API Routes - Hardened with proper async flow and persistence.
Implements Option A: Status-based async flow.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from db.database import get_db, async_session_maker
from models.pydantic_models import (
    AnalyzeRepoRequest, AnalyzeRepoResponse,
    AskQuestionRequest, AskQuestionResponse
)
from services.analysis_service import AnalysisServiceFinal
from services.comparative_service import ComparativeAnalysisService
from services.code_quality_service import CodeQualityAnalyzer
from utils.rate_limiter import get_limiter

router = APIRouter()
analysis_service = AnalysisServiceFinal()
comparative_service = ComparativeAnalysisService()
code_quality_analyzer = CodeQualityAnalyzer()
limiter = get_limiter()


@router.post("/analyze-repo", response_model=AnalyzeRepoResponse)
async def analyze_repo(
    request: AnalyzeRepoRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start repository analysis (returns immediately with status='processing').
    
    Flow:
    1. Validate URL
    2. Create repo + analysis_session with status='processing'
    3. Commit to database
    4. Return immediately with repo_id and status
    5. Background task does actual analysis
    """
    try:
        # Validate URL
        if not request.repo_url or 'github.com' not in request.repo_url:
            raise HTTPException(
                status_code=400,
                detail="Invalid GitHub repository URL"
            )
        
        # Start analysis (synchronous setup)
        result = await analysis_service.start_analysis(request.repo_url, db)
        
        repo_id = result['repo_id']
        
        # Background task for actual analysis (with NEW session)
        async def background_analysis():
            """
            Runs in background with its OWN database session.
            This is critical for SQLite persistence.
            """
            async with async_session_maker() as bg_db:
                try:
                    await analysis_service.execute_analysis(repo_id, bg_db)
                except Exception as e:
                    print(f"Background analysis error: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        background_tasks.add_task(background_analysis)
        
        return AnalyzeRepoResponse(
            repo_id=repo_id,
            status="processing",
            message="Analysis started. Use GET /api/status/{repo_id} to check progress."
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/status/{repo_id}")
async def get_analysis_status(
    repo_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get analysis status for a repository.
    
    Returns:
        {
            "repo_id": "...",
            "status": "processing|completed|failed|not_found",
            "started_at": "...",
            "completed_at": "...",
            "error_message": "..."
        }
    """
    try:
        status = await analysis_service.get_status(repo_id, db)
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/analysis/{repo_id}")
async def get_analysis(
    repo_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete analysis for a repository.
    
    Requirements:
    - Analysis must be completed (status='completed')
    - Returns frontend-ready structured JSON
    - ZERO Gemini calls (reads from database only)
    """
    try:
        analysis = await analysis_service.get_analysis(repo_id, db)
        return analysis
    except ValueError as e:
        # Analysis not completed or not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analysis: {str(e)}"
        )


@router.post("/ask", response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Answer question about analyzed repository.
    
    Requirements:
    - Analysis MUST be completed first
    - Returns 400 if analysis not completed
    - ZERO Gemini calls (uses stored data only)
    - Idempotent and deterministic
    """
    try:
        # Check status first
        status = await analysis_service.get_status(request.repo_id, db)
        
        if status['status'] == 'not_found':
            raise HTTPException(
                status_code=404,
                detail=f"Repository not found: {request.repo_id}"
            )
        
        if status['status'] == 'processing':
            raise HTTPException(
                status_code=400,
                detail="Analysis still in progress. Please wait for completion."
            )
        
        if status['status'] == 'failed':
            raise HTTPException(
                status_code=400,
                detail=f"Analysis failed: {status.get('error_message', 'Unknown error')}"
            )
        
        # Status is 'completed' - safe to answer
        result = await analysis_service.answer_question(
            request.repo_id,
            request.question,
            db
        )
        
        return AskQuestionResponse(
            repo_id=result['repo_id'],
            question=result['question'],
            answer=result['answer'],
            created_at=result['created_at']
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint with system info."""
    return {
        "status": "healthy",
        "service": "repo-analyzer-final",
        "architecture": "production",
        "features": {
            "single_gemini_call": True,
            "split_table_storage": True,
            "status_based_async": True,
            "proper_persistence": True,
            "idempotent_qa": True,
            "websocket_support": True,
            "code_quality_analysis": True,
            "comparative_analysis": True,
            "rate_limiting": True,
            "caching": True
        }
    }


# Pydantic models for new endpoints
class CompareRequest(BaseModel):
    """Request model for repository comparison."""
    repo_ids: List[str]
    comparison_type: str = "tech_stack"  # tech_stack, architecture, complexity


@router.post("/compare")
@limiter.limit("5/minute")
async def compare_repositories(
    request: Request,
    compare_request: CompareRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare multiple repositories.
    
    Supports comparison types:
    - tech_stack: Compare technologies used
    - architecture: Compare architectural patterns
    - complexity: Compare complexity metrics
    """
    try:
        result = await comparative_service.compare_repositories(
            compare_request.repo_ids,
            db,
            compare_request.comparison_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


@router.get("/code-quality/{repo_id}")
async def get_code_quality(
    repo_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get code quality metrics for a repository.
    
    Returns scores for:
    - Documentation quality
    - Test coverage estimate
    - Code organization
    - Dependency health
    """
    try:
        # Get repository data
        from sqlalchemy import select
        from models.schemas import Repository, TechStack
        
        repo_result = await db.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        repo = repo_result.scalar_one_or_none()
        
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Get tech stack
        tech_result = await db.execute(
            select(TechStack).where(TechStack.repo_id == repo_id)
        )
        tech_stack = [
            {"name": t.name, "category": t.category}
            for t in tech_result.scalars()
        ]
        
        # Analyze code quality
        # Note: This is a simplified version. In production, you'd fetch actual file data
        quality_metrics = await code_quality_analyzer.analyze(
            files=[],  # Would need to fetch from analysis
            readme=None,  # Would fetch from GitHub
            tech_stack=tech_stack
        )
        
        return {
            "repo_id": repo_id,
            "repo_name": f"{repo.owner}/{repo.name}",
            "metrics": quality_metrics
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze code quality: {str(e)}"
        )