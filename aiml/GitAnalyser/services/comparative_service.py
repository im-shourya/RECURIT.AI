"""
Comparative analysis service.
Compare multiple repositories across various dimensions.
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.schemas import Repository, AnalysisSummary, TechStack


class ComparativeAnalysisService:
    """Service for comparing multiple repositories."""
    
    async def compare_repositories(
        self,
        repo_ids: List[str],
        db: AsyncSession,
        comparison_type: str = "tech_stack"
    ) -> Dict[str, Any]:
        """
        Compare multiple repositories.
        
        Args:
            repo_ids: List of repository IDs to compare
            db: Database session
            comparison_type: Type of comparison (tech_stack, architecture, complexity)
            
        Returns:
            Comparison results
        """
        if len(repo_ids) < 2:
            raise ValueError("At least 2 repositories required for comparison")
        
        if len(repo_ids) > 5:
            raise ValueError("Maximum 5 repositories can be compared at once")
        
        # Fetch repository data
        repos_data = []
        for repo_id in repo_ids:
            data = await self._fetch_repo_data(repo_id, db)
            if data:
                repos_data.append(data)
        
        if len(repos_data) < 2:
            raise ValueError("Not enough valid repositories for comparison")
        
        # Perform comparison based on type
        if comparison_type == "tech_stack":
            return await self._compare_tech_stack(repos_data)
        elif comparison_type == "architecture":
            return await self._compare_architecture(repos_data)
        elif comparison_type == "complexity":
            return await self._compare_complexity(repos_data)
        else:
            raise ValueError(f"Unknown comparison type: {comparison_type}")
    
    async def _fetch_repo_data(self, repo_id: str, db: AsyncSession) -> Dict:
        """Fetch repository data for comparison."""
        # Get repository
        repo_result = await db.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        repo = repo_result.scalar_one_or_none()
        
        if not repo:
            return None
        
        # Get analysis summary
        summary_result = await db.execute(
            select(AnalysisSummary).where(AnalysisSummary.repo_id == repo_id)
        )
        summary = summary_result.scalar_one_or_none()
        
        # Get tech stack
        tech_result = await db.execute(
            select(TechStack).where(TechStack.repo_id == repo_id)
        )
        tech_stack = list(tech_result.scalars())
        
        return {
            "repo_id": repo_id,
            "name": f"{repo.owner}/{repo.name}",
            "url": repo.repo_url,
            "primary_language": repo.primary_language,
            "summary": summary,
            "tech_stack": tech_stack
        }
    
    async def _compare_tech_stack(self, repos_data: List[Dict]) -> Dict:
        """Compare technology stacks."""
        # Collect all technologies
        all_techs = {}
        for repo in repos_data:
            repo_techs = set()
            for tech in repo.get("tech_stack", []):
                tech_name = tech.name
                repo_techs.add(tech_name)
                
                if tech_name not in all_techs:
                    all_techs[tech_name] = {
                        "repos": [],
                        "category": tech.category
                    }
                all_techs[tech_name]["repos"].append(repo["name"])
        
        # Find common and unique technologies
        repo_names = [r["name"] for r in repos_data]
        common_techs = [
            tech for tech, data in all_techs.items()
            if len(data["repos"]) == len(repos_data)
        ]
        
        unique_techs = {}
        for repo in repos_data:
            repo_tech_names = {tech.name for tech in repo.get("tech_stack", [])}
            unique = repo_tech_names - set(common_techs)
            if unique:
                unique_techs[repo["name"]] = list(unique)
        
        return {
            "comparison_type": "tech_stack",
            "repositories": repo_names,
            "common_technologies": common_techs,
            "unique_technologies": unique_techs,
            "technology_matrix": all_techs,
            "summary": f"Compared {len(repos_data)} repositories. Found {len(common_techs)} common technologies."
        }
    
    async def _compare_architecture(self, repos_data: List[Dict]) -> Dict:
        """Compare architectural patterns."""
        architectures = {}
        
        for repo in repos_data:
            summary = repo.get("summary")
            if summary:
                architectures[repo["name"]] = {
                    "pattern": summary.architecture_pattern,
                    "data_flow": summary.data_flow
                }
        
        # Find common patterns
        patterns = [data["pattern"] for data in architectures.values()]
        pattern_counts = {}
        for pattern in patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        most_common_pattern = max(pattern_counts.items(), key=lambda x: x[1])[0] if pattern_counts else None
        
        return {
            "comparison_type": "architecture",
            "repositories": [r["name"] for r in repos_data],
            "architectures": architectures,
            "most_common_pattern": most_common_pattern,
            "pattern_distribution": pattern_counts
        }
    
    async def _compare_complexity(self, repos_data: List[Dict]) -> Dict:
        """Compare complexity metrics."""
        complexity_scores = {}
        
        for repo in repos_data:
            summary = repo.get("summary")
            if summary:
                # Use confidence score as a proxy for complexity
                # Lower confidence might indicate higher complexity
                complexity_scores[repo["name"]] = {
                    "confidence_score": summary.confidence_score,
                    "estimated_complexity": round((1 - summary.confidence_score) * 10, 1)
                }
        
        # Sort by complexity
        sorted_repos = sorted(
            complexity_scores.items(),
            key=lambda x: x[1]["estimated_complexity"],
            reverse=True
        )
        
        return {
            "comparison_type": "complexity",
            "repositories": [r["name"] for r in repos_data],
            "complexity_scores": complexity_scores,
            "ranking": [{"repo": name, **data} for name, data in sorted_repos],
            "summary": f"Most complex: {sorted_repos[0][0]}, Least complex: {sorted_repos[-1][0]}"
        }
