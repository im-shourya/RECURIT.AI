"""
Refactored Gemini 3 service - SINGLE API CALL architecture.
Generates all analysis in one structured response to avoid rate limits.
"""
import os
import json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator

# Try to import Google GenAI SDK
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ============================================================================
# STRUCTURED OUTPUT SCHEMA - Enforces deterministic, frontend-ready responses
# ============================================================================

class TechStackItem(BaseModel):
    """Single technology in the stack."""
    name: str = Field(..., max_length=50, description="Technology name")
    category: str = Field(..., max_length=30, description="Category (Language/Framework/Database/Tool)")
    version: Optional[str] = Field(None, max_length=20, description="Version if detected")


class ComponentItem(BaseModel):
    """Single architectural component."""
    name: str = Field(..., max_length=50, description="Component name")
    purpose: str = Field(..., max_length=200, description="What this component does")
    files: List[str] = Field(default_factory=list, max_items=5, description="Key files")


class FileInsight(BaseModel):
    """Insight about a specific file."""
    path: str = Field(..., max_length=200)
    role: str = Field(..., max_length=30, description="entry_point/config/core/utility")
    purpose: str = Field(..., max_length=150, description="One-line explanation")


class RepositoryAnalysis(BaseModel):
    """Complete repository analysis - single structured response."""
    
    # Core summary (comprehensive overview)
    summary: str = Field(..., min_length=200, max_length=1500, description="10-20 sentence comprehensive project summary")
    purpose: str = Field(..., max_length=150, description="What problem this solves")
    
    # Tech stack
    tech_stack: List[TechStackItem] = Field(..., min_items=1, max_items=15)
    primary_language: str = Field(..., max_length=30)
    
    # Architecture
    architecture_pattern: str = Field(..., max_length=50, description="MVC/Microservices/Monolith/etc")
    components: List[ComponentItem] = Field(default_factory=list, max_items=10)
    data_flow: str = Field(..., max_length=300, description="How data moves through the system")
    
    # File organization
    key_files: List[FileInsight] = Field(default_factory=list, max_items=10)
    
    # Setup and contribution
    setup_steps: List[str] = Field(..., min_items=2, max_items=6, description="Setup steps as short strings")
    contribution_areas: List[str] = Field(default_factory=list, max_items=5, description="Safe areas for new contributors")
    
    # Risks and limitations
    risky_areas: List[str] = Field(default_factory=list, max_items=5, description="Areas requiring caution")
    known_issues: List[str] = Field(default_factory=list, max_items=5, description="From GitHub issues analysis")
    
    # Metadata
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0, description="Analysis confidence")
    
    @validator('summary', 'purpose', 'data_flow')
    def no_fluff(cls, v):
        """Remove common AI fluff phrases."""
        fluff_phrases = [
            "it's important to note",
            "it should be noted",
            "as mentioned",
            "basically",
            "essentially",
            "in conclusion",
            "to summarize"
        ]
        result = v
        for phrase in fluff_phrases:
            result = result.replace(phrase, "").replace(phrase.title(), "")
        return result.strip()


# ============================================================================
# GEMINI SERVICE - Single call, validated output
# ============================================================================

class GeminiServiceV2:
    """Refactored Gemini service - ONE call per repository analysis."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = None
        self.using_mock = False
        
        gemini_model = os.getenv("GEMINI_MODEL", "flash")
        
        if GEMINI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = 'gemini-3-pro-preview' if gemini_model.lower() == "pro" else 'gemini-3-flash-preview'
        else:
            self.using_mock = True
    
    async def analyze_repository(self, context: Dict) -> RepositoryAnalysis:
        """
        SINGLE API CALL to analyze entire repository.
        Returns validated, structured, frontend-ready data.
        """
        prompt = self._build_unified_prompt(context)
        
        if self.client and self.model_name:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                raw_text = response.text
                
                # Clean response (remove markdown fences if present)
                if raw_text.strip().startswith("```"):
                    raw_text = raw_text.split("```json")[-1].split("```")[0].strip()
                elif raw_text.strip().startswith("{"):
                    pass  # Already clean JSON
                else:
                    # Try to extract JSON from text
                    import re
                    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if json_match:
                        raw_text = json_match.group(0)
                
                # Parse and validate
                data = json.loads(raw_text)
                analysis = RepositoryAnalysis(**data)
                return analysis
                
            except json.JSONDecodeError as e:
                print(f"Gemini returned invalid JSON: {str(e)}")
                return self._fallback_analysis(context)
            except Exception as e:
                print(f"Gemini API error: {str(e)}")
                return self._fallback_analysis(context)
        else:
            return self._fallback_analysis(context)
    
    def _build_unified_prompt(self, context: Dict) -> str:
        """Build single comprehensive prompt for all analysis."""
        
        repo_name = context.get('repo_name', 'Unknown')
        primary_lang = context.get('primary_language', 'Unknown')
        readme = (context.get('readme') or 'No README available')[:3000]
        
        files_list = "\n".join([
            f"- {f['path']} ({f.get('language', 'unknown')})"
            for f in context.get('files', [])[:20]
        ])
        
        config_files = [f['path'] for f in context.get('config_files', [])[:10]]
        entry_files = [f['path'] for f in context.get('source_files', []) if f.get('role') == 'entry_point'][:5]
        
        issues_summary = f"{len(context.get('open_issues', []))} open, {len(context.get('closed_issues', []))} recently closed"
        
        # Extract issue titles for pattern detection
        issue_titles = [
            issue.get('title', '')
            for issue in (context.get('open_issues', [])[:10] + context.get('closed_issues', [])[:5])
        ]

        dependencies = context.get('dependencies', {})
        dep_frameworks = ", ".join(dependencies.get('frameworks', [])) if dependencies else "None detected"
        dep_libraries = ", ".join(dependencies.get('libraries', [])) if dependencies else "None detected"
        dep_languages = ", ".join(dependencies.get('languages', [])) if dependencies else "None detected"

        architecture_hints = context.get('architecture_hints', {})
        arch_pattern = architecture_hints.get('pattern', 'Unknown')
        arch_conf = architecture_hints.get('confidence', 0.0)
        arch_indicators = ", ".join(architecture_hints.get('indicators', [])) if architecture_hints else "None"

        # Include code snippets (limited by pre-truncation in analysis service)
        code_snippets = []
        for path, content in context.get('file_contents', {}).items():
            snippet = content[:10000]
            code_snippets.append(f"### {path}\n{snippet}")
        code_section = "\n\n".join(code_snippets) if code_snippets else "No code content available"
        
        prompt = f"""Analyze this GitHub repository and return ONLY valid JSON (no markdown, no prose).

Repository: {repo_name}
Primary Language: {primary_lang}

README (first 3000 chars, weight 20%):
{readme}

Code Structure (weight 30%):
{files_list}

Configuration Files: {', '.join(config_files) if config_files else 'None detected'}
Entry Points: {', '.join(entry_files) if entry_files else 'Not identified'}

Code Content (weight 25%):
{code_section}

Dependencies (weight 20%):
Frameworks: {dep_frameworks}
Libraries: {dep_libraries}
Languages: {dep_languages}

Architecture Hints (structure-only, non-LLM):
Pattern: {arch_pattern} (confidence {arch_conf})
Indicators: {arch_indicators}

GitHub Issues (weight 5%): {issues_summary}
Recent Issue Patterns: {', '.join(issue_titles[:5]) if issue_titles else 'No issues'}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON matching this exact schema
2. Use SHORT, SCANNABLE strings (no essays)
3. Be SPECIFIC and EVIDENCE-BASED (no speculation)
4. NO fluff phrases like "it's important to note" or "essentially"
5. Keep arrays to specified max lengths
6. All strings must be concise and frontend-ready

Return JSON with these exact keys:

{{
  "summary": "Comprehensive 10-20 sentence explanation covering: what this project does, its main features, key technologies used, target audience, primary use cases, and overall architecture approach. Be thorough and detailed.",
  "purpose": "What problem does this solve (max 150 chars)",
  "tech_stack": [
    {{
      "name": "TechName",
      "category": "Language|Framework|Database|Tool|Library",
      "version": "1.0.0 or null"
    }}
  ],
  "primary_language": "{primary_lang}",
  "architecture_pattern": "MVC|Microservices|Monolith|Library|CLI|etc",
  "components": [
    {{
      "name": "ComponentName",
      "purpose": "What it does (max 200 chars)",
      "files": ["file1.py", "file2.py"]
    }}
  ],
  "data_flow": "How data moves through system (max 300 chars)",
  "key_files": [
    {{
      "path": "path/to/file",
      "role": "entry_point|config|core|utility",
      "purpose": "One-line explanation (max 150 chars)"
    }}
  ],
  "setup_steps": [
    "Step 1: Clone repo",
    "Step 2: Install dependencies",
    "Step 3-6: ..."
  ],
  "contribution_areas": [
    "Documentation",
    "Tests",
    "etc"
  ],
  "risky_areas": [
    "Authentication module",
    "Database migrations"
  ],
  "known_issues": [
    "Issue pattern 1 from GitHub",
    "Issue pattern 2"
  ],
  "confidence_score": 0.9
}}

If README is missing or thin, use structure + dependencies + code content to infer everything. Assign confidence based on data quality, not README presence.
Analyze using the weighted sources above. Use evidence only. Be concise. Return valid JSON only.
"""
        return prompt
    
    def _fallback_analysis(self, context: Dict) -> RepositoryAnalysis:
        """Deterministic fallback when Gemini unavailable."""
        primary_lang = context.get('primary_language') or 'Unknown'
        repo_name = context.get('repo_name') or 'Unknown Repository'
        
        return RepositoryAnalysis(
            summary=f"{repo_name} is a {primary_lang} project currently experiencing API analysis limitations. This repository contains code, documentation, and configuration files typical of modern software development. Due to temporary API constraints, automated deep analysis is unavailable at this moment. However, basic project structure and primary technology stack have been identified. Please try again later for comprehensive analysis.",
            purpose="Project analysis unavailable",
            tech_stack=[
                TechStackItem(
                    name=primary_lang,
                    category="Programming Language",
                    version=None
                )
            ],
            primary_language=primary_lang,
            architecture_pattern="Unknown",
            components=[],
            data_flow="Analysis unavailable",
            key_files=[],
            setup_steps=[
                "Clone repository",
                "Review README for setup instructions"
            ],
            contribution_areas=["Documentation"],
            risky_areas=[],
            known_issues=[],
            confidence_score=0.3
        )
    
    async def answer_question(self, question: str, analysis: RepositoryAnalysis, additional_context: str = "") -> str:
        """
        Answer question using pre-analyzed data.
        This is a SEPARATE call (for Q&A), not part of initial analysis.
        """
        # Build rich context from analysis
        tech_details = "\n".join([
            f"- {t.name} ({t.category})" + (f" v{t.version}" if t.version else "")
            for t in analysis.tech_stack[:8]
        ])
        
        comp_details = "\n".join([
            f"- {c.name}: {c.purpose}"
            for c in analysis.components[:5]
        ])
        
        setup_details = "\n".join([
            f"{i+1}. {step}"
            for i, step in enumerate(analysis.setup_steps[:5])
        ])
        
        context_str = f"""Repository Analysis:

OVERVIEW:
{analysis.summary}

PURPOSE:
{analysis.purpose}

TECH STACK:
{tech_details}

ARCHITECTURE:
Pattern: {analysis.architecture_pattern}
{analysis.data_flow}

COMPONENTS:
{comp_details if comp_details else "Not specified"}

SETUP:
{setup_details if setup_details else "Not specified"}

CONTRIBUTION AREAS:
{', '.join(analysis.contribution_areas) if analysis.contribution_areas else "Not specified"}

KNOWN ISSUES:
{', '.join(analysis.known_issues[:3]) if analysis.known_issues else "None identified"}

{additional_context}
"""
        
        prompt = f"""Answer this question about the repository using ONLY the provided analysis data.

Question: {question}

Repository Analysis Data:
{context_str}

CRITICAL RULES:
1. Answer in 2-5 sentences (50-150 words max)
2. Be specific and reference actual data from the analysis
3. DO NOT make up information not in the analysis
4. If the analysis doesn't contain the answer, say so briefly
5. DO NOT just repeat the summary - answer the specific question asked
6. Use a natural, helpful tone
7. Focus on what's relevant to the question

Answer:"""
        
        if self.client and self.model_name:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                # Log the error for debugging
                print(f"⚠️ Gemini API error in Q&A: {str(e)}")
                import traceback
                traceback.print_exc()
                # Fallback to simple response
                return self._generate_fallback_answer(question, analysis)
        else:
            print("⚠️ Gemini client not available, using fallback answers")
            return self._generate_fallback_answer(question, analysis)
    
    def _generate_fallback_answer(self, question: str, analysis: RepositoryAnalysis) -> str:
        """Generate a contextual answer when Gemini is unavailable."""
        question_lower = question.lower()
        
        # Extract key information for more dynamic responses
        tech_names = [t.name for t in analysis.tech_stack[:5]]
        comp_names = [c.name for c in analysis.components[:4]]
        
        # More specific keyword matching with varied responses
        if any(word in question_lower for word in ['what is', 'what does', 'explain', 'describe', 'about']):
            if 'architecture' in question_lower or 'structure' in question_lower:
                comp_list = ', '.join(comp_names) if comp_names else "various modules"
                return f"This project follows a {analysis.architecture_pattern} architecture with components including {comp_list}. {analysis.data_flow}"
            elif any(tech in question_lower for tech in ['tech', 'technology', 'stack', 'language', 'framework']):
                tech_list = ', '.join(tech_names) if tech_names else "various technologies"
                return f"The project is built with {tech_list}. The primary language is {analysis.primary_language}."
            else:
                return f"{analysis.summary} {analysis.purpose}"
        
        elif any(word in question_lower for word in ['how', 'setup', 'install', 'start', 'run', 'deploy']):
            if analysis.setup_steps:
                steps = '. '.join(analysis.setup_steps[:3])
                return f"To get started: {steps}. Check the repository for complete setup instructions."
            return "Setup instructions: Clone the repository and follow the README for detailed setup steps."
        
        elif any(word in question_lower for word in ['tech', 'technology', 'stack', 'built', 'language', 'framework', 'library']):
            tech_list = ', '.join(tech_names) if tech_names else "various technologies"
            return f"This project uses {tech_list}. The architecture follows a {analysis.architecture_pattern} pattern."
        
        elif any(word in question_lower for word in ['architecture', 'structure', 'organized', 'design', 'pattern']):
            comp_list = ', '.join(comp_names) if comp_names else "multiple components"
            return f"Architecture: {analysis.architecture_pattern}. Main components: {comp_list}. {analysis.data_flow}"
        
        elif any(word in question_lower for word in ['contribute', 'help', 'where', 'area']):
            if analysis.contribution_areas:
                areas = ', '.join(analysis.contribution_areas[:3])
                return f"You can contribute in these areas: {areas}."
            return "Check the repository issues and README for contribution guidelines."
        
        elif any(word in question_lower for word in ['issue', 'problem', 'bug', 'risk', 'concern']):
            issues = analysis.known_issues[:3] if analysis.known_issues else []
            risks = analysis.risky_areas[:2] if analysis.risky_areas else []
            
            if issues or risks:
                result = []
                if issues:
                    result.append(f"Known issues: {', '.join(issues)}")
                if risks:
                    result.append(f"Risky areas: {', '.join(risks)}")
                return ". ".join(result) + "."
            return "No specific issues or risks identified in the analysis."
        
        elif any(word in question_lower for word in ['file', 'code', 'source', 'important']):
            if analysis.key_files:
                files = ', '.join([f.path for f in analysis.key_files[:3]])
                return f"Key files in this project include: {files}. These files are central to the project's functionality."
            return "File structure information is available in the repository."
        
        elif any(word in question_lower for word in ['data', 'flow', 'work', 'process']):
            return f"Data flow: {analysis.data_flow}. The system follows a {analysis.architecture_pattern} pattern."
        
        elif any(word in question_lower for word in ['component', 'module', 'part']):
            if comp_names:
                return f"Main components: {', '.join(comp_names)}. Each component serves a specific purpose in the {analysis.architecture_pattern} architecture."
            return f"The project is organized following a {analysis.architecture_pattern} architecture pattern."
        
        else:
            # More varied default response based on available data
            tech_summary = f" using {', '.join(tech_names[:3])}" if tech_names else ""
            return f"{analysis.summary}{tech_summary}. It follows a {analysis.architecture_pattern} architecture. {analysis.purpose}"
