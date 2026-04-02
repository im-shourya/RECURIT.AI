"""
Database migration helper for V2 schema.
Adds new analysis_results table while preserving old tables for backward compatibility.
"""
from sqlalchemy import text
from db.database import engine


async def migrate_to_v2():
    """
    Create new analysis_results table.
    Old tables remain for backward compatibility but are deprecated.
    """
    async with engine.begin() as conn:
        # Enable foreign keys
        await conn.exec_driver_sql("PRAGMA foreign_keys = ON;")
        
        # Check if new table exists
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_results';"
        ))
        exists = result.scalar() is not None
        
        if not exists:
            print("Creating analysis_results table...")
            
            await conn.execute(text("""
                CREATE TABLE analysis_results (
                    repo_id TEXT PRIMARY KEY,
                    summary TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    primary_language TEXT NOT NULL,
                    architecture_pattern TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.8,
                    tech_stack_json TEXT NOT NULL,
                    components_json TEXT NOT NULL,
                    key_files_json TEXT NOT NULL,
                    setup_steps_json TEXT NOT NULL,
                    contribution_areas_json TEXT NOT NULL,
                    risky_areas_json TEXT NOT NULL,
                    known_issues_json TEXT NOT NULL,
                    data_flow TEXT NOT NULL,
                    raw_llm_response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analysis_version TEXT DEFAULT '2.0',
                    FOREIGN KEY (repo_id) REFERENCES repositories(id)
                );
            """))
            
            print("✓ analysis_results table created")
        else:
            print("✓ analysis_results table already exists")
        
        # Create index for faster queries
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_analysis_confidence ON analysis_results(confidence_score);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_analysis_language ON analysis_results(primary_language);"
        ))
        
        print("✓ Migration complete")


async def check_schema_version():
    """Check which schema version is in use."""
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ))
        tables = [row[0] for row in result.fetchall()]
        
        has_v2 = 'analysis_results' in tables
        has_v1 = 'tech_stack' in tables and 'architecture_summary' in tables
        
        if has_v2:
            print("✓ Schema V2 detected (unified analysis_results)")
            return "v2"
        elif has_v1:
            print("⚠ Schema V1 detected (legacy tables)")
            return "v1"
        else:
            print("! No schema detected")
            return None


async def add_diagram_column():
    """
    Idempotent migration: adds `architecture_diagram_mermaid` TEXT column
    to the `analysis_summary` table if it does not already exist.

    Safe to run on every startup — does nothing when the column already exists.
    """
    async with engine.begin() as conn:
        # Check existing columns via PRAGMA
        result = await conn.execute(text("PRAGMA table_info(analysis_summary);"))
        columns = [row[1] for row in result.fetchall()]   # row[1] = column name

        if "architecture_diagram_mermaid" not in columns:
            await conn.execute(text(
                "ALTER TABLE analysis_summary "
                "ADD COLUMN architecture_diagram_mermaid TEXT;"
            ))
            print("✓ Added architecture_diagram_mermaid column to analysis_summary")
        else:
            print("✓ architecture_diagram_mermaid column already exists")