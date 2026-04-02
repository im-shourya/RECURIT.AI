"""
Production Analysis Service - Hardened with proper async flow and persistence.
Guarantees:
- Exactly ONE Gemini call per repository
- Proper SQLite transaction management
- Status-based async flow
- Data persists across restarts
"""
import uuid
import json
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas import (
    Repository, AnalysisSession, AnalysisSummary,
    TechStack, ArchitectureComponent, KeyFile,
    SetupStep, ContributionArea, RiskyArea, KnownIssue,
    QALog, RawAnalysisResponse
)
from services.github_service import GitHubService
from services.gemini_service import GeminiServiceV2, RepositoryAnalysis
from services.dependency_analyzer import DependencyAnalyzer
from services.diagram_generator import DiagramGenerator
from utils.file_filter import FileFilter


class AnalysisServiceFinal:
    """
    Production-ready analysis service with proper persistence.
    """
    
    def __init__(self):
        self.github = GitHubService()
        self.gemini = GeminiServiceV2()
        self.file_filter = FileFilter()
        self.dependency_analyzer = DependencyAnalyzer()
        self.diagram_generator = DiagramGenerator()
    
    async def start_analysis(self, repo_url: str, db: AsyncSession) -> Dict:
        """
        Start repository analysis (synchronous setup + background work).
        
        Returns immediately with repo_id and status='processing'.
        Actual analysis happens in background.
        """
        # Parse URL
        try:
            owner, repo_name = self.github.parse_repo_url(repo_url)
        except ValueError as e:
            raise ValueError(f"Invalid repository URL: {str(e)}")
        
        # Check if repository exists
        result = await db.execute(
            select(Repository).where(Repository.repo_url == repo_url)
        )
        existing_repo = result.scalar_one_or_none()
        
        if existing_repo:
            repo_id = existing_repo.id
        else:
            repo_id = str(uuid.uuid4())
            
            # Create minimal repository record
            repository = Repository(
                id=repo_id,
                repo_url=repo_url,
                owner=owner,
                name=repo_name,
                analyzed_at=datetime.utcnow()
            )
            db.add(repository)
            
            # CRITICAL: Flush to ensure repository exists before creating session
            # This prevents FOREIGN KEY constraint errors
            await db.flush()
        
        # Create analysis session with 'processing' status
        session_id = str(uuid.uuid4())
        session = AnalysisSession(
            id=session_id,
            repo_id=repo_id,
            status="processing",
            started_at=datetime.utcnow(),
            gemini_call_count=0
        )
        db.add(session)
        
        # CRITICAL: Commit synchronously so status is persisted
        try:
            await db.commit()
            print(f"✓ Created analysis session {session_id} for {repo_url}")
        except Exception as e:
            await db.rollback()
            print(f"✗ Failed to create analysis session: {str(e)}")
            raise
        
        return {
            "repo_id": repo_id,
            "session_id": session_id,
            "status": "processing"
        }
    
    async def execute_analysis(self, repo_id: str, db: AsyncSession) -> None:
        """
        Execute the actual analysis (called in background).
        Uses a SEPARATE database session from the request.
        
        This is the ONLY method that calls Gemini.
        """
        print(f"\n{'='*70}")
        print(f"BACKGROUND ANALYSIS START: {repo_id}")
        print(f"{'='*70}")
        
        # Get repository info
        result = await db.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        repo = result.scalar_one_or_none()
        
        if not repo:
            print(f"✗ Repository not found: {repo_id}")
            return
        
        # Get analysis session
        result = await db.execute(
            select(AnalysisSession)
            .where(AnalysisSession.repo_id == repo_id)
            .order_by(AnalysisSession.started_at.desc())
        )
        session = result.scalars().first()
        
        if not session:
            print(f"✗ Analysis session not found for: {repo_id}")
            return
        
        try:
            # ================================================================
            # STEP 1: Fetch GitHub data (no LLM calls)
            # ================================================================
            
            owner = repo.owner
            repo_name = repo.name
            
            print(f"📥 Fetching GitHub data for {owner}/{repo_name}...")
            
            metadata = await self.github.get_repo_metadata(owner, repo_name)
            readme = await self.github.get_readme(owner, repo_name)
            tree = await self.github.get_repository_tree(owner, repo_name)
            important_files = self.file_filter.filter_important_files(tree, max_files=30)
            
            # Fetch limited file contents
            file_contents = {}
            prioritized_files = self._prioritize_files_for_content(important_files)
            for file_info in prioritized_files[:20]:
                content = await self.github.get_file_content(owner, repo_name, file_info['path'])
                if content:
                    file_contents[file_info['path']] = content[:10000]
            
            # Fetch issues
            open_issues = await self.github.get_issues(owner, repo_name, state="open", max_issues=30)
            closed_issues = await self.github.get_issues(owner, repo_name, state="closed", max_issues=20)
            
            print(f"✓ GitHub data fetched: {len(important_files)} files, {len(open_issues)} open issues")
            
            # Update repository metadata
            repo.primary_language = metadata.get('language')
            if metadata.get('created_at'):
                repo.created_at = datetime.fromisoformat(metadata['created_at'].replace('Z', '+00:00'))
            repo.analyzed_at = datetime.utcnow()
            
            # ================================================================
            # STEP 2: Build context for Gemini
            # ================================================================
            
            context = {
                'repo_name': f"{owner}/{repo_name}",
                'primary_language': metadata.get('language'),
                'readme': readme,
                'files': important_files,
                'config_files': [f for f in important_files if f['role'] == 'configuration'],
                'source_files': [f for f in important_files if f['role'] in ['source_code', 'entry_point']],
                'file_contents': file_contents,
                'open_issues': open_issues,
                'closed_issues': closed_issues,
                'dependencies': self.dependency_analyzer.analyze_dependencies(file_contents),
                'architecture_hints': self._infer_architecture_from_structure(important_files)
            }
            
            # ================================================================
            # STEP 3: SINGLE GEMINI API CALL
            # ================================================================
            
            print(f"🤖 Making SINGLE Gemini API call for {owner}/{repo_name}...")
            session.gemini_call_count += 1
            
            analysis: RepositoryAnalysis = await self.gemini.analyze_repository(context)
            
            print(f"✓ Received structured analysis (confidence: {analysis.confidence_score})")

            # ================================================================
            # STEP 3.5: Generate Mermaid diagram (pure Python — ZERO API calls)
            # ================================================================

            print("🎨 Generating architecture diagram (Mermaid)...")
            diagram_syntax = self.diagram_generator.generate_mermaid_diagram({
                'components': analysis.components,
                'tech_stack':  analysis.tech_stack,
                'data_flow':   analysis.data_flow,
            })
            print("✓ Mermaid diagram generated")
            
            # ================================================================
            # STEP 4: Store in database (split tables)
            # ================================================================
            
            print(f"💾 Storing analysis in database...")
            
            # 1. Summary
            result = await db.execute(
                select(AnalysisSummary).where(AnalysisSummary.repo_id == repo_id)
            )
            existing_summary = result.scalar_one_or_none()
            
            if existing_summary:
                # Update existing
                existing_summary.summary = analysis.summary
                existing_summary.purpose = analysis.purpose
                existing_summary.architecture_pattern = analysis.architecture_pattern
                existing_summary.data_flow = analysis.data_flow
                existing_summary.confidence_score = analysis.confidence_score
                existing_summary.architecture_diagram_mermaid = diagram_syntax
                existing_summary.updated_at = datetime.utcnow()
            else:
                # Create new
                summary = AnalysisSummary(
                    repo_id=repo_id,
                    summary=analysis.summary,
                    purpose=analysis.purpose,
                    architecture_pattern=analysis.architecture_pattern,
                    data_flow=analysis.data_flow,
                    confidence_score=analysis.confidence_score,
                    architecture_diagram_mermaid=diagram_syntax,
                )
                db.add(summary)
            
            # 2. Tech Stack (delete old, insert new)
            await db.execute(
                select(TechStack).where(TechStack.repo_id == repo_id)
            )
            # Delete existing
            result = await db.execute(
                select(TechStack).where(TechStack.repo_id == repo_id)
            )
            for old_tech in result.scalars():
                await db.delete(old_tech)
            
            # Insert new
            for tech_item in analysis.tech_stack:
                tech = TechStack(
                    id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    name=tech_item.name,
                    category=tech_item.category,
                    version=tech_item.version
                )
                db.add(tech)
            
            # 3. Components
            result = await db.execute(
                select(ArchitectureComponent).where(ArchitectureComponent.repo_id == repo_id)
            )
            for old_comp in result.scalars():
                await db.delete(old_comp)
            
            for comp in analysis.components:
                component = ArchitectureComponent(
                    id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    name=comp.name,
                    purpose=comp.purpose,
                    key_files=json.dumps(comp.files)
                )
                db.add(component)
            
            # 4. Key Files
            result = await db.execute(
                select(KeyFile).where(KeyFile.repo_id == repo_id)
            )
            for old_file in result.scalars():
                await db.delete(old_file)
            
            for file_item in analysis.key_files:
                key_file = KeyFile(
                    id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    file_path=file_item.path,
                    role=file_item.role,
                    purpose=file_item.purpose
                )
                db.add(key_file)
            
            # 5. Setup Steps
            result = await db.execute(
                select(SetupStep).where(SetupStep.repo_id == repo_id)
            )
            for old_step in result.scalars():
                await db.delete(old_step)
            
            for i, step in enumerate(analysis.setup_steps):
                setup_step = SetupStep(
                    id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    step_order=i + 1,
                    instruction=step
                )
                db.add(setup_step)
            
            # 6. Contribution Areas
            result = await db.execute(
                select(ContributionArea).where(ContributionArea.repo_id == repo_id)
            )
            for old_area in result.scalars():
                await db.delete(old_area)
            
            for area in analysis.contribution_areas:
                contrib_area = ContributionArea(
                    id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    area=area
                )
                db.add(contrib_area)
            
            # 7. Risky Areas
            result = await db.execute(
                select(RiskyArea).where(RiskyArea.repo_id == repo_id)
            )
            for old_risky in result.scalars():
                await db.delete(old_risky)
            
            for risky in analysis.risky_areas:
                risky_area = RiskyArea(
                    id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    area=risky
                )
                db.add(risky_area)
            
            # 8. Known Issues
            result = await db.execute(
                select(KnownIssue).where(KnownIssue.repo_id == repo_id)
            )
            for old_issue in result.scalars():
                await db.delete(old_issue)
            
            for issue in analysis.known_issues:
                known_issue = KnownIssue(
                    id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    issue=issue
                )
                db.add(known_issue)
            
            # 9. Raw Response (for debugging)
            result = await db.execute(
                select(RawAnalysisResponse).where(RawAnalysisResponse.repo_id == repo_id)
            )
            existing_raw = result.scalar_one_or_none()
            
            if existing_raw:
                existing_raw.raw_json = analysis.json()
                existing_raw.model_version = self.gemini.model_name or "mock"
                existing_raw.created_at = datetime.utcnow()
            else:
                raw_response = RawAnalysisResponse(
                    repo_id=repo_id,
                    raw_json=analysis.json(),
                    model_version=self.gemini.model_name or "mock"
                )
                db.add(raw_response)
            
            # ================================================================
            # STEP 5: Mark session as completed
            # ================================================================
            
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            
            # CRITICAL: Commit everything
            try:
                await db.commit()
                print(f"✓ Analysis committed to database successfully")
                print(f"✓ Gemini calls made: {session.gemini_call_count}")
            except Exception as commit_error:
                await db.rollback()
                print(f"✗ Database commit failed: {str(commit_error)}")
                raise
            
            print(f"{'='*70}")
            print(f"BACKGROUND ANALYSIS COMPLETE: {owner}/{repo_name}")
            print(f"{'='*70}\n")
            
        except Exception as e:
            # Mark session as failed
            session.status = "failed"
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            
            try:
                await db.commit()
                print(f"✗ Analysis failed and marked in database: {str(e)}")
            except:
                await db.rollback()
                print(f"✗ Failed to mark error in database")
            
            print(f"✗ Background analysis error: {str(e)}")
            import traceback
            traceback.print_exc()

    def _prioritize_files_for_content(self, files: List[Dict]) -> List[Dict]:
        """Prioritize entry points and config files before other sources."""
        entry_points = [f for f in files if f.get('role') == 'entry_point']
        config_files = [f for f in files if f.get('role') == 'configuration']
        others = [f for f in files if f.get('role') not in ['entry_point', 'configuration']]
        return entry_points + config_files + others

    def _infer_architecture_from_structure(self, files: List[Dict]) -> Dict:
        """Infer architecture pattern from folder structure only."""
        paths = [f.get('path', '') for f in files]
        dir_names = set()
        top_level = set()

        for path in paths:
            parts = [p for p in path.split('/') if p]
            if len(parts) > 1:
                top_level.add(parts[0].lower())
                dir_names.update([p.lower() for p in parts[:-1]])

        indicators = []
        pattern = "Unknown"
        confidence = 0.5

        mvc_hits = [n for n in ["models", "views", "controllers"] if n in dir_names]
        if len(mvc_hits) >= 2:
            pattern = "MVC"
            confidence = 0.7 if len(mvc_hits) == 2 else 0.85
            indicators.append(f"folders: {', '.join(sorted(mvc_hits))}")

        service_like = [d for d in top_level if "service" in d or d in ["services", "gateway"]]
        if len(service_like) >= 2:
            pattern = "Microservices"
            confidence = max(confidence, 0.8)
            indicators.append(f"top-level services: {', '.join(sorted(service_like))}")

        layered_hits = [n for n in ["controllers", "services", "repositories", "domain", "infrastructure"] if n in dir_names]
        if len(layered_hits) >= 3 and pattern == "Unknown":
            pattern = "Layered"
            confidence = 0.75
            indicators.append(f"layers: {', '.join(sorted(layered_hits))}")

        if pattern == "Unknown":
            indicators.append("no strong structural pattern detected")

        return {
            "pattern": pattern,
            "confidence": round(confidence, 2),
            "indicators": indicators
        }
    
    async def get_status(self, repo_id: str, db: AsyncSession) -> Dict:
        """Get analysis status for a repository."""
        result = await db.execute(
            select(AnalysisSession)
            .where(AnalysisSession.repo_id == repo_id)
            .order_by(AnalysisSession.started_at.desc())
        )
        session = result.scalars().first()
        
        if not session:
            return {"repo_id": repo_id, "status": "not_found"}
        
        return {
            "repo_id": repo_id,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "error_message": session.error_message
        }
    
    async def get_analysis(self, repo_id: str, db: AsyncSession) -> Dict:
        """
        Retrieve complete analysis from database.
        ZERO Gemini calls - reads only from stored data.
        """
        # Check status first
        status_result = await self.get_status(repo_id, db)
        
        if status_result['status'] != 'completed':
            raise ValueError(f"Analysis not completed (status: {status_result['status']})")
        
        # Fetch all data from split tables
        summary_result = await db.execute(
            select(AnalysisSummary).where(AnalysisSummary.repo_id == repo_id)
        )
        summary = summary_result.scalar_one_or_none()
        
        if not summary:
            raise ValueError("Analysis data not found")
        
        # Tech stack
        tech_result = await db.execute(
            select(TechStack).where(TechStack.repo_id == repo_id)
        )
        tech_stack = [
            {"name": t.name, "category": t.category, "version": t.version}
            for t in tech_result.scalars()
        ]
        
        # Components
        comp_result = await db.execute(
            select(ArchitectureComponent).where(ArchitectureComponent.repo_id == repo_id)
        )
        components = [
            {"name": c.name, "purpose": c.purpose, "files": json.loads(c.key_files) if c.key_files else []}
            for c in comp_result.scalars()
        ]
        
        # Key files
        files_result = await db.execute(
            select(KeyFile).where(KeyFile.repo_id == repo_id)
        )
        key_files = [
            {"path": f.file_path, "role": f.role, "purpose": f.purpose}
            for f in files_result.scalars()
        ]
        
        # Setup steps
        steps_result = await db.execute(
            select(SetupStep)
            .where(SetupStep.repo_id == repo_id)
            .order_by(SetupStep.step_order)
        )
        setup_steps = [s.instruction for s in steps_result.scalars()]
        
        # Contribution areas
        contrib_result = await db.execute(
            select(ContributionArea).where(ContributionArea.repo_id == repo_id)
        )
        contribution_areas = [c.area for c in contrib_result.scalars()]
        
        # Risky areas
        risky_result = await db.execute(
            select(RiskyArea).where(RiskyArea.repo_id == repo_id)
        )
        risky_areas = [r.area for r in risky_result.scalars()]
        
        # Known issues
        issues_result = await db.execute(
            select(KnownIssue).where(KnownIssue.repo_id == repo_id)
        )
        known_issues = [i.issue for i in issues_result.scalars()]
        
        return {
            "repo_id": repo_id,
            "summary": summary.summary,
            "purpose": summary.purpose,
            "architecture_pattern": summary.architecture_pattern,
            "data_flow": summary.data_flow,
            "confidence_score": summary.confidence_score,
            "architecture_diagram": summary.architecture_diagram_mermaid,
            "tech_stack": tech_stack,
            "components": components,
            "key_files": key_files,
            "setup_steps": setup_steps,
            "contribution_areas": contribution_areas,
            "risky_areas": risky_areas,
            "known_issues": known_issues,
            "analyzed_at": summary.created_at.isoformat() if summary.created_at else None,
            "version": summary.analysis_version
        }
    
    async def answer_question(self, repo_id: str, question: str, db: AsyncSession) -> Dict:
        """
        Answer question using stored analysis data + Gemini for intelligent responses.
        Uses ONE Gemini call per question for better quality.
        """
        # Get stored analysis
        analysis_data = await self.get_analysis(repo_id, db)
        
        # Reconstruct Pydantic model for Gemini
        from services.gemini_service import RepositoryAnalysis
        
        # Get raw analysis response
        result = await db.execute(
            select(RawAnalysisResponse).where(RawAnalysisResponse.repo_id == repo_id)
        )
        raw_response = result.scalar_one_or_none()
        
        if raw_response:
            # Parse the stored Pydantic model
            analysis_obj = RepositoryAnalysis(**json.loads(raw_response.raw_json))
        else:
            # Fallback: construct from analysis_data
            from services.gemini_service import TechStackItem, ComponentItem, FileInsight
            
            analysis_obj = RepositoryAnalysis(
                summary=analysis_data['summary'],
                purpose=analysis_data['purpose'],
                tech_stack=[TechStackItem(**t) for t in analysis_data['tech_stack']],
                primary_language=analysis_data.get('primary_language', 'Unknown'),
                architecture_pattern=analysis_data['architecture_pattern'],
                components=[ComponentItem(**c) for c in analysis_data.get('components', [])],
                data_flow=analysis_data['data_flow'],
                key_files=[FileInsight(**f) for f in analysis_data.get('key_files', [])],
                setup_steps=analysis_data.get('setup_steps', []),
                contribution_areas=analysis_data.get('contribution_areas', []),
                risky_areas=analysis_data.get('risky_areas', []),
                known_issues=analysis_data.get('known_issues', []),
                confidence_score=analysis_data.get('confidence_score', 0.8)
            )
        
        # Build additional context
        key_files_context = "\n".join([
            f"- {f['path']}: {f['purpose']}"
            for f in analysis_data.get('key_files', [])[:5]
        ])
        
        additional_context = f"Key Files:\n{key_files_context}" if key_files_context else ""
        
        # Use Gemini to answer with context
        answer = await self.gemini.answer_question(
            question=question,
            analysis=analysis_obj,
            additional_context=additional_context
        )
        
        # Log Q&A
        qa_id = str(uuid.uuid4())
        qa_log = QALog(
            id=qa_id,
            repo_id=repo_id,
            question=question,
            answer=answer,
            created_at=datetime.utcnow()
        )
        db.add(qa_log)
        
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"Warning: Failed to log Q&A: {str(e)}")
        
        return {
            'repo_id': repo_id,
            'question': question,
            'answer': answer,
            'created_at': qa_log.created_at
        }
