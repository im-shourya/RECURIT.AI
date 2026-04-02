"""
Production V2 Database Models - Split Table Architecture
Stores data in normalized tables for better queries and flexibility.
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Float, Integer
from sqlalchemy.sql import func
from db.database import Base


# ============================================================================
# CORE TABLES (always used)
# ============================================================================

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Text, primary_key=True)
    repo_url = Column(Text, unique=True, nullable=False, index=True)
    owner = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    primary_language = Column(Text)
    created_at = Column(DateTime)
    analyzed_at = Column(DateTime)


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    status = Column(Text, nullable=False, index=True)  # processing|completed|failed
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    gemini_call_count = Column(Integer, default=0)  # Track API calls made
    

# ============================================================================
# ANALYSIS DATA TABLES (split architecture for normalized storage)
# ============================================================================

class AnalysisSummary(Base):
    """Core summary and metadata for quick access."""
    __tablename__ = "analysis_summary"
    
    repo_id = Column(Text, ForeignKey("repositories.id"), primary_key=True)
    
    # Core fields
    summary = Column(Text, nullable=False)
    purpose = Column(Text, nullable=False)
    architecture_pattern = Column(Text, nullable=False)
    data_flow = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.8)
    
    # Architecture diagram (Mermaid syntax, generated client-side — no API call)
    architecture_diagram_mermaid = Column(Text)  # nullable; stores Mermaid syntax text

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    analysis_version = Column(Text, default="2.0")


class TechStack(Base):
    """Individual technology items (many per repository)."""
    __tablename__ = "tech_stack"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    version = Column(Text)
    reasoning = Column(Text)


class ArchitectureComponent(Base):
    """Individual architectural components."""
    __tablename__ = "architecture_components"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    purpose = Column(Text, nullable=False)
    key_files = Column(Text)  # JSON array as text


class KeyFile(Base):
    """Key files identified in the repository."""
    __tablename__ = "key_files"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    role = Column(Text, nullable=False)  # entry_point|config|core|utility
    purpose = Column(Text, nullable=False)


class SetupStep(Base):
    """Setup instructions in order."""
    __tablename__ = "setup_steps"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False)
    instruction = Column(Text, nullable=False)


class ContributionArea(Base):
    """Safe areas for new contributors."""
    __tablename__ = "contribution_areas"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    area = Column(Text, nullable=False)


class RiskyArea(Base):
    """Areas requiring caution."""
    __tablename__ = "risky_areas"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    area = Column(Text, nullable=False)


class KnownIssue(Base):
    """Known issues from GitHub analysis."""
    __tablename__ = "known_issues"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    issue = Column(Text, nullable=False)


# ============================================================================
# Q&A LOGS (unchanged)
# ============================================================================

class QALog(Base):
    __tablename__ = "qa_logs"
    
    id = Column(Text, primary_key=True)
    repo_id = Column(Text, ForeignKey("repositories.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


# ============================================================================
# RAW RESPONSE STORAGE (for debugging and versioning)
# ============================================================================

class RawAnalysisResponse(Base):
    """Store raw Gemini response for debugging/auditing."""
    __tablename__ = "raw_analysis_responses"
    
    repo_id = Column(Text, ForeignKey("repositories.id"), primary_key=True)
    raw_json = Column(Text, nullable=False)  # Complete Pydantic model as JSON
    prompt_used = Column(Text)  # Store prompt for reproducibility
    model_version = Column(Text)  # gemini-3-flash-preview or pro
    created_at = Column(DateTime, server_default=func.now())