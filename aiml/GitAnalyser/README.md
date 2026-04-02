# GitHub Repository Analyzer

A complete backend system that analyzes GitHub repositories to help new developers understand and contribute to projects.

## Features

### Core Analysis
- **Automated Repository Analysis**: Fetches and analyzes repository structure, code, and issues
- **AI-Powered Insights**: Uses Gemini LLM to generate:
  - Project overview
  - Tech stack analysis with reasoning
  - Architecture summary along with Architecture diagram
  - Issues-based insights
  - Contributor guide for new developers
- **Intelligent File Filtering**: Focuses on important files (entry points, configs, core modules)
- **Context-Aware Q&A**: Answer questions about the repository using analyzed context

### Advanced Features (NEW)
- **Real-time Progress**: WebSocket support for live analysis updates
- **Code Quality Metrics**: Automated scoring for documentation, tests, organization, and dependencies
- **Comparative Analysis**: Compare multiple repositories across tech stack, architecture, and complexity
- **Smart Caching**: Reduces GitHub API calls and improves response times
- **Rate Limiting**: Prevents abuse with configurable request limits
- **Structured Logging**: JSON-formatted logs for production monitoring

### Production Ready
- **Async Architecture**: Non-blocking analysis using FastAPI background tasks
- **SQLite Database**: Stores all analysis results for quick retrieval
- **Comprehensive Testing**: pytest-based test suite with 70%+ coverage target
- **CI/CD Pipeline**: Automated testing with GitHub Actions
- **Deployment Ready**: Docker support, multiple deployment options

## Tech Stack

- **Backend**: Python, FastAPI
- **Database**: SQLite with async SQLAlchemy
- **LLM**: Gemini 3 (Flash or Pro, with mock fallback)
- **HTTP Client**: httpx for GitHub API
- **Validation**: Pydantic

## Database Schema

All tables use TEXT for UUID and JSON fields (SQLite compatible):

- **repositories**: Stores repository metadata
- **analysis_sessions**: Tracks analysis progress
- **repo_files**: Analyzed files with roles
- **tech_stack**: Identified technologies
- **architecture_summary**: Architecture overview and components
- **issues_insights**: Insights from GitHub issues
- **contributor_guide**: Generated guide for new contributors
- **qa_logs**: Question-answer history

## Installation & Setup

### Prerequisites

- Python 3.9 or higher
- pip

### Step 1: Clone or Extract the Project

```bash
cd repo-analyzer
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required for full AI-powered analysis
GEMINI_API_KEY=your_gemini_api_key_here

# Gemini Model Selection: "flash" (Gemini 3 Flash) or "pro" (Gemini 3 Pro)
# Flash is faster and more cost-effective (recommended)
GEMINI_MODEL=flash

# Optional - for higher GitHub API rate limits
GITHUB_TOKEN=your_github_token_here
```

**Note**: The system will work with mock responses if `GEMINI_API_KEY` is not provided, but analysis quality will be limited to placeholder text.

**Gemini 3 Models:**
- **Flash** (default): Faster responses, lower cost, good quality
- **Pro**: Higher quality analysis, slower, higher cost

### Step 5: Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once running, access interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

#### 1. Analyze Repository (POST /api/analyze-repo)

**POST** `/api/analyze-repo`

Starts background analysis of a GitHub repository.

**Request:**
```json
{
  "repo_url": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
  "repo_id": "uuid-string",
  "status": "processing",
  "message": "Repository analysis started..."
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/analyze-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/fastapi/fastapi"}'
```

#### 2. Ask Question

**POST** `/api/ask`

Ask context-aware questions about an analyzed repository.

**Request:**
```json
{
  "repo_id": "uuid-from-analyze-response",
  "question": "What is the purpose of main.py?"
}
```

**Response:**
```json
{
  "repo_id": "uuid-string",
  "question": "What is the purpose of main.py?",
  "answer": "Based on the repository analysis...",
  "created_at": "2024-01-15T10:30:00"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "your-repo-id",
    "question": "How is the authentication implemented?"
  }'
```

#### 3. Get Analysis Status (GET /api/status/{repo_id})

Check the status of an ongoing or completed analysis.

#### 4. Get Code Quality Metrics (GET /api/code-quality/{repo_id})

Get automated code quality scores for a repository.

**Response:**
```json
{
  "repo_id": "uuid",
  "repo_name": "owner/repo",
  "metrics": {
    "documentation_score": 8.5,
    "test_coverage_estimate": 65,
    "code_organization": 9.0,
    "dependency_health": 7.5,
    "overall_score": 7.8,
    "strengths": ["Excellent documentation"],
    "improvements": ["Increase test coverage"]
  }
}
```

#### 5. Compare Repositories (POST /api/compare)

Compare multiple repositories across different dimensions.

**Request:**
```json
{
  "repo_ids": ["uuid1", "uuid2"],
  "comparison_type": "tech_stack"
}
```

**Response:**
```json
{
  "comparison_type": "tech_stack",
  "repositories": ["owner1/repo1", "owner2/repo2"],
  "common_technologies": ["Python", "FastAPI"],
  "unique_technologies": {
    "owner1/repo1": ["Redis"],
    "owner2/repo2": ["PostgreSQL"]
  }
}
```

#### 6. WebSocket Progress (WS /ws/analysis/{repo_id})

Connect to receive real-time analysis progress updates.

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analysis/repo-id');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update.message);
};
```

#### 7. Health Check

**GET** `/api/health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "repo-analyzer"
}
```

## How It Works

### Analysis Flow

1. **Repository Validation**: Validates GitHub URL and fetches metadata
2. **File Discovery**: Fetches repository tree and filters important files
3. **Content Extraction**: Retrieves README, config files, and key source files
4. **Issue Analysis**: Fetches open and recently closed issues
5. **LLM Analysis**: Generates insights using Gemini:
   - Project overview
   - Tech stack identification
   - Architecture analysis
   - Issue pattern recognition
   - Contributor guidance
6. **Database Storage**: Stores all results in SQLite
7. **Background Processing**: Analysis runs asynchronously, doesn't block requests

### File Filtering Logic

The system intelligently selects files based on:

- **Supported Languages**: Python, C, C++, Java, JavaScript, HTML, CSS
- **Ignored Directories**: node_modules, venv, build, dist, .git, etc.
- **Priority System**:
  - Entry points (main.py, index.js): Priority 100
  - Config files (package.json, requirements.txt): Priority 80
  - Root/src files: Priority 60
  - Other source files: Priority 40
- **Size Limits**: Limits total content to prevent overload

### Question Answering

When you ask a question:

1. System retrieves all stored analysis for the repository
2. Builds context with overview, architecture, tech stack, and files
3. If question mentions specific files, adds detailed file context
4. Gemini generates answer based on context
5. Q&A is logged for future reference

## Testing Locally

### Test 1: Analyze a Repository

```bash
# Start the server
python main.py

# In another terminal, test analysis
curl -X POST http://localhost:8000/api/analyze-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/fastapi/fastapi"}'
```

Expected response includes a `repo_id`. Save this for the next test.

### Test 2: Ask Questions

```bash
# Wait 30-60 seconds for analysis to complete, then:
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "YOUR_REPO_ID_FROM_ABOVE",
    "question": "What is this project about?"
  }'
```

### Test 3: Check Database

```bash
# Install SQLite browser or use CLI
sqlite3 app.db

# Example queries:
.tables
SELECT * FROM repositories;
SELECT * FROM tech_stack;
SELECT * FROM contributor_guide;
```

## Configuration

### GitHub API Rate Limits

Without authentication: 60 requests/hour
With GITHUB_TOKEN: 5,000 requests/hour

To add a token:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (no special scopes needed for public repos)
3. Add to `.env`: `GITHUB_TOKEN=your_token`

### Gemini API Setup

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add to `.env`:
   ```env
   GEMINI_API_KEY=your_key
   GEMINI_MODEL=flash  # or "pro" for Gemini 3 Pro
   ```

**Available Models:**
- **gemini-3-flash-preview** (default): Fast, cost-effective, excellent for this use case
- **gemini-3-pro-preview**: Higher quality analysis, better reasoning, slower

The system automatically uses **Gemini 3 Flash** by default for optimal speed and cost. Set `GEMINI_MODEL=pro` to use Gemini 3 Pro for more complex analysis.

**Installation:**
```bash
pip install google-genai
```

## Error Handling

The system includes comprehensive error handling for:

- Invalid GitHub URLs
- Repository not found (404)
- GitHub API rate limits (403)
- Network failures
- LLM API errors (falls back to mock)
- Database constraint violations

## Mental Testing Verification

### Test Flow 1: Full Analysis Pipeline
✅ URL validation (regex parsing)
✅ Repository metadata fetch (GitHub API)
✅ README fetch with error handling
✅ File tree retrieval with branch fallback
✅ File filtering (priority algorithm)
✅ Content fetching with size limits
✅ Issues fetch (open + closed)
✅ LLM context building
✅ Sequential analysis generation
✅ Database storage with foreign keys
✅ Background task execution

### Test Flow 2: Question Answering
✅ Repository existence check
✅ Context retrieval from database
✅ File-specific context enhancement
✅ LLM question answering
✅ Q&A logging

### Test Flow 3: Error Scenarios
✅ Invalid URL → 400 error
✅ Repository not found → 404 from GitHub
✅ Rate limit → 403 with clear message
✅ Missing repo_id → 404 error
✅ Database errors → proper rollback

### Test Flow 4: Edge Cases
✅ Large files → truncated to 10KB
✅ Many files → limited to 30 files
✅ Missing README → handled gracefully
✅ No issues → empty list handled
✅ Gemini unavailable → mock responses
✅ Re-analysis → updates existing records

## Production Considerations

For production deployment:

1. **Security**:
   - Use environment-specific CORS origins
   - Add rate limiting
   - Implement authentication
   - Secure API keys

2. **Database**:
   - Consider PostgreSQL for better concurrency
   - Add indexes for frequent queries
   - Implement connection pooling

3. **Scalability**:
   - Use task queue (Celery, RQ) for background jobs
   - Add caching layer (Redis)
   - Implement request queuing

4. **Monitoring**:
   - Add structured logging
   - Implement health checks
   - Set up error tracking (Sentry)

## Troubleshooting

### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Database errors
```bash
# Delete and recreate database
rm app.db
python main.py  # Will recreate on startup
```

### GitHub API rate limit
```bash
# Add GITHUB_TOKEN to .env file
# Or wait 1 hour for rate limit reset
```

### Gemini API errors
```bash
# Verify API key in .env
# Check https://makersuite.google.com/ for quota
# System will fall back to mock responses if needed
```

## License

This is a demonstration project for educational purposes.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API documentation at `/docs`
3. Examine logs in the console output
