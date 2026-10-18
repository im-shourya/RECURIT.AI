# Changelog

All notable changes to RECRUIT.AI are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [2.1.0] — 2026-10-18

### Added

- **Sign in with Google or GitHub.** An existing account signs straight in,
  pending team invitations are accepted, and someone new names their
  organisation. Only verified provider email addresses are accepted. (#157)
- **In-app notifications.** The dashboard bell lists new applications, task
  submissions and finished interviews, with read state kept per person. (#158)
- **Interview-completed email preference** on the settings page. (#120)
- **Audit entries** for registration, sign-in, failed sign-in and CSV exports.
  (#101, #121)
- **`GET /api/applicants/{id}/interview`** for reading a transcript by
  applicant id. (#95)
- **A new design system**: a lagoon accent on paper neutrals, SF Pro on Apple
  devices with Inter elsewhere, and control radii of 8–12px. (#161)
- **Liquid glass** for navigation bars and overlays, falling back to opaque
  surfaces when transparency is reduced. (#162)
- **A scroll-scrubbed canvas** on the landing page that follows a cohort from
  application to decision, with a static frame for reduced motion and
  low-end devices. (#163)
- **A rebuilt footer** with an appearance switcher and the release version.
  (#165)

### Changed

- **The landing page describes only features that ship.** Adaptive AI
  interviews, GitHub analysis, gaze tracking and NLP scoring were advertised
  but don't exist. (#164)
- **The sign-in panel shows real product facts** instead of an invented
  testimonial and usage figures. (#113)
- **Secondary text meets WCAG AA**: 4.9:1, up from 3.3:1. (#161)
- **Members no longer see team-administration history** in the audit
  trail. (#94)
- **Production deploys stop serving `/docs`, `/redoc` and `/openapi.json`.**
  (#116)
- **The frontend package is now `recruit-ai-frontend`**, versioned with the
  API. (#112)

### Fixed

- **Recruiters no longer receive candidates' interview tokens.** (#95)
- **Candidate-supplied links accept only http(s) URLs**, and GitHub links must
  point at github.com. (#92)
- **Registration requires eight-character passwords**, like every other
  password form. (#91)
- **Free text and interview transcripts have size limits**, so one candidate's
  record can't grow too large to save. (#96)
- **Skipped email is recorded as failed in production** instead of
  delivered. (#90)
- **The CSV export is rate-limited**, capped at 10,000 rows and audited.
  (#121)

### Removed

- **Dead API schemas** (`EmailLogResponse`, `ApplicantStatusUpdate`) and the
  ignored `recording_url` field on interview end. (#103)
- **Four landing sections that were never rendered.** (#109)

## [2.0.0]

The MongoDB release: the move from PostgreSQL, membership of several
organisations, the email outbox, roles and the audit trail. Recorded in the
pull request history up to #155.

[2.1.0]: https://github.com/im-shourya/RECURIT.AI/releases/tag/v2.1.0
[2.0.0]: https://github.com/im-shourya/RECURIT.AI/commits/c1e7709c
