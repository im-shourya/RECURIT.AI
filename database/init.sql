-- ══════════════════════════════════════════════════════════════
-- RECRUIT.AI — PostgreSQL Schema Initialization
-- Run this to create all tables from scratch.
-- Usage:  psql -U recruit_user -d recruit_ai -f init.sql
-- ══════════════════════════════════════════════════════════════

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ──────────────────────────────────────────────
-- ENUM TYPES
-- ──────────────────────────────────────────────
DO $$ BEGIN
    CREATE TYPE task_type_enum AS ENUM ('task', 'github');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE question_level_enum AS ENUM ('beginner', 'intermediate', 'advanced');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE drive_status_enum AS ENUM ('active', 'closed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE applicant_status_enum AS ENUM (
        'applied', 'task_sent', 'submitted',
        'interview_sent', 'interviewed', 'selected', 'rejected'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE email_type_enum AS ENUM ('applied', 'task', 'interview', 'result');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ──────────────────────────────────────────────
-- ORGANISATIONS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS organisations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    description     TEXT DEFAULT '',
    domain_tags     TEXT[] DEFAULT '{}',
    logo_url        TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_organisations_email ON organisations(email);


-- ──────────────────────────────────────────────
-- DRIVES (Recruitment Campaigns)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS drives (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id              UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    domain              VARCHAR(255) NOT NULL,
    task_type           task_type_enum NOT NULL,
    task_description    TEXT DEFAULT '',
    question_level      question_level_enum DEFAULT 'beginner',
    apply_deadline      DATE NOT NULL,
    task_deadline       DATE,
    link_token          VARCHAR(64) NOT NULL UNIQUE,
    qr_code_url         TEXT DEFAULT '',
    status              drive_status_enum DEFAULT 'active',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drives_org_id ON drives(org_id);
CREATE INDEX IF NOT EXISTS idx_drives_link_token ON drives(link_token);


-- ──────────────────────────────────────────────
-- APPLICANTS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS applicants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drive_id        UUID NOT NULL REFERENCES drives(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) NOT NULL,
    reg_no          VARCHAR(100) DEFAULT '',
    skills          TEXT[] DEFAULT '{}',
    primary_domain  VARCHAR(255) DEFAULT '',
    github_url      TEXT DEFAULT '',
    status          applicant_status_enum DEFAULT 'applied',
    applied_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_applicants_drive_id ON applicants(drive_id);
CREATE INDEX IF NOT EXISTS idx_applicants_email ON applicants(email);


-- ──────────────────────────────────────────────
-- SUBMISSIONS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS submissions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    applicant_id        UUID NOT NULL UNIQUE REFERENCES applicants(id) ON DELETE CASCADE,
    file_url            TEXT DEFAULT '',
    github_url          TEXT DEFAULT '',
    description         TEXT DEFAULT '',
    repolens_analysis   JSONB DEFAULT '{}',
    submitted_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_submissions_applicant_id ON submissions(applicant_id);


-- ──────────────────────────────────────────────
-- INTERVIEWS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS interviews (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    applicant_id        UUID NOT NULL UNIQUE REFERENCES applicants(id) ON DELETE CASCADE,
    token               VARCHAR(64) NOT NULL UNIQUE,
    started_at          TIMESTAMPTZ,
    ended_at            TIMESTAMPTZ,
    recording_url       TEXT DEFAULT '',
    transcript          JSONB DEFAULT '[]',
    score_intro         INTEGER DEFAULT 0,
    score_project       INTEGER DEFAULT 0,
    score_domain        INTEGER DEFAULT 0,
    total_score         INTEGER DEFAULT 0,
    malpractice_flags   JSONB DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_interviews_applicant_id ON interviews(applicant_id);
CREATE INDEX IF NOT EXISTS idx_interviews_token ON interviews(token);


-- ──────────────────────────────────────────────
-- EMAIL LOGS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS email_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    applicant_id    UUID NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    type            email_type_enum NOT NULL,
    sent_at         TIMESTAMPTZ DEFAULT NOW(),
    emailjs_msg_id  VARCHAR(255) DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_email_logs_applicant_id ON email_logs(applicant_id);


-- ══════════════════════════════════════════════════════════════
-- DONE — All tables and indexes created
-- ══════════════════════════════════════════════════════════════
