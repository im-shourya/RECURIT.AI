"""
Code quality analyzer service.
Provides objective metrics for repository code quality.
"""
from typing import Dict, List, Any
import re


class CodeQualityAnalyzer:
    """Analyze code quality metrics for repositories."""
    
    def __init__(self):
        self.test_file_patterns = [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'tests?/.*\.py$',
            r'spec/.*\.js$',
            r'.*\.test\.js$',
            r'.*\.spec\.js$'
        ]
    
    async def analyze(
        self,
        files: List[Dict],
        readme: str = None,
        tech_stack: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze code quality metrics.
        
        Args:
            files: List of repository files
            readme: README content
            tech_stack: Identified technologies
            
        Returns:
            Dictionary with quality scores and metrics
        """
        metrics = {
            "documentation_score": self._calculate_documentation_score(readme, files),
            "test_coverage_estimate": self._estimate_test_coverage(files),
            "code_organization": self._analyze_organization(files),
            "dependency_health": self._analyze_dependencies(files, tech_stack),
            "overall_score": 0.0,
            "strengths": [],
            "improvements": []
        }
        
        # Calculate overall score (weighted average)
        metrics["overall_score"] = (
            metrics["documentation_score"] * 0.25 +
            metrics["test_coverage_estimate"] / 10 * 0.30 +
            metrics["code_organization"] * 0.25 +
            metrics["dependency_health"] * 0.20
        )
        
        # Identify strengths and improvements
        metrics["strengths"] = self._identify_strengths(metrics)
        metrics["improvements"] = self._identify_improvements(metrics)
        
        return metrics
    
    def _calculate_documentation_score(self, readme: str, files: List[Dict]) -> float:
        """Calculate documentation quality score (0-10)."""
        score = 0.0
        
        if readme:
            # Check README length
            if len(readme) > 500:
                score += 3.0
            elif len(readme) > 200:
                score += 2.0
            elif len(readme) > 50:
                score += 1.0
            
            # Check for common sections
            readme_lower = readme.lower()
            sections = [
                'installation', 'setup', 'usage', 'example',
                'contributing', 'license', 'api', 'documentation'
            ]
            found_sections = sum(1 for section in sections if section in readme_lower)
            score += min(found_sections * 0.5, 3.0)
            
            # Check for code examples
            if '```' in readme or '    ' in readme:
                score += 2.0
        
        # Check for docstrings/comments in files
        doc_files = [f for f in files if f.get('path', '').endswith(('.py', '.js', '.java'))]
        if doc_files:
            score += min(len(doc_files) * 0.1, 2.0)
        
        return min(score, 10.0)
    
    def _estimate_test_coverage(self, files: List[Dict]) -> float:
        """Estimate test coverage percentage (0-100)."""
        source_files = [
            f for f in files
            if f.get('path', '').endswith(('.py', '.js', '.java', '.cpp', '.c'))
            and not any(re.search(pattern, f.get('path', '')) for pattern in self.test_file_patterns)
        ]
        
        test_files = [
            f for f in files
            if any(re.search(pattern, f.get('path', '')) for pattern in self.test_file_patterns)
        ]
        
        if not source_files:
            return 0.0
        
        # Rough estimate: assume each test file covers 5 source files
        estimated_coverage = min((len(test_files) * 5) / len(source_files) * 100, 100)
        
        return round(estimated_coverage, 1)
    
    def _analyze_organization(self, files: List[Dict]) -> float:
        """Analyze code organization score (0-10)."""
        score = 5.0  # Start with average
        
        file_paths = [f.get('path', '') for f in files]
        
        # Check for organized directory structure
        has_src = any('src/' in path for path in file_paths)
        has_tests = any('test' in path.lower() for path in file_paths)
        has_docs = any('doc' in path.lower() for path in file_paths)
        has_config = any(path.endswith(('.json', '.yml', '.yaml', '.toml')) for path in file_paths)
        
        if has_src:
            score += 1.0
        if has_tests:
            score += 2.0
        if has_docs:
            score += 1.0
        if has_config:
            score += 1.0
        
        # Penalize too many root-level files
        root_files = [p for p in file_paths if '/' not in p.lstrip('./')]
        if len(root_files) > 15:
            score -= 1.0
        
        return min(max(score, 0.0), 10.0)
    
    def _analyze_dependencies(self, files: List[Dict], tech_stack: List[Dict]) -> float:
        """Analyze dependency health score (0-10)."""
        score = 7.0  # Start with good score
        
        # Check for dependency files
        file_paths = [f.get('path', '') for f in files]
        
        has_requirements = any('requirements.txt' in path for path in file_paths)
        has_package_json = any('package.json' in path for path in file_paths)
        has_gemfile = any('Gemfile' in path for path in file_paths)
        has_pom = any('pom.xml' in path for path in file_paths)
        
        if any([has_requirements, has_package_json, has_gemfile, has_pom]):
            score += 1.0
        
        # Check for lock files (good practice)
        has_lock = any(
            path.endswith(('.lock', 'package-lock.json', 'yarn.lock', 'Pipfile.lock'))
            for path in file_paths
        )
        if has_lock:
            score += 1.0
        
        # Bonus for having CI/CD
        has_ci = any('.github/workflows' in path or '.gitlab-ci' in path for path in file_paths)
        if has_ci:
            score += 1.0
        
        return min(score, 10.0)
    
    def _identify_strengths(self, metrics: Dict) -> List[str]:
        """Identify project strengths based on metrics."""
        strengths = []
        
        if metrics["documentation_score"] >= 7.0:
            strengths.append("Excellent documentation")
        if metrics["test_coverage_estimate"] >= 60:
            strengths.append("Good test coverage")
        if metrics["code_organization"] >= 7.0:
            strengths.append("Well-organized codebase")
        if metrics["dependency_health"] >= 8.0:
            strengths.append("Healthy dependency management")
        
        return strengths
    
    def _identify_improvements(self, metrics: Dict) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        
        if metrics["documentation_score"] < 5.0:
            improvements.append("Add comprehensive README and documentation")
        if metrics["test_coverage_estimate"] < 30:
            improvements.append("Increase test coverage")
        if metrics["code_organization"] < 5.0:
            improvements.append("Improve code organization and structure")
        if metrics["dependency_health"] < 6.0:
            improvements.append("Update dependencies and add lock files")
        
        return improvements
