"""
Pydantic models for API request and response validation.
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime


class AnalyzeRepoRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")


class AnalyzeRepoResponse(BaseModel):
    repo_id: str
    status: str
    message: str


class AskQuestionRequest(BaseModel):
    repo_id: str
    question: str


class AskQuestionResponse(BaseModel):
    repo_id: str
    question: str
    answer: str
    created_at: datetime


class TechStackItem(BaseModel):
    name: str
    category: str
    reasoning: str


class RepositoryInfo(BaseModel):
    id: str
    repo_url: str
    owner: Optional[str]
    name: Optional[str]
    primary_language: Optional[str]
    analyzed_at: Optional[datetime]


class AnalysisResult(BaseModel):
    repository: RepositoryInfo
    overview: Optional[str]
    tech_stack: List[TechStackItem]
    architecture_overview: Optional[str]
    getting_started: Optional[str]
    safe_areas: Optional[str]
    caution_areas: Optional[str]