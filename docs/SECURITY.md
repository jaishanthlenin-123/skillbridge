# SkillBridge Security & Privacy Policy

SkillBridge implements defensive, privacy-first software engineering standards across file uploads, database queries, authentication, and external network boundaries.

## 1. Authentication & Session Management
- **Password Security**: Uses Django's PBKDF2 with SHA-256 password hashing (or Argon2 if configured), with salt and iteration hardening. Plaintext passwords are never logged or stored.
- **Session & Token Protection**: CSRF validation required for non-GET browser requests. Auth tokens are scoped to active user sessions.
- **Strict Authorization**: Every database access object is filtered by `owner=request.user`. ID manipulation (IDOR) attacks are rejected with HTTP 404 or 403.

## 2. Document Processing & File Upload Safeguards
- **File Integrity & MIME Validation**: Accepts strictly `.pdf` and `.docx` extensions with validation against magic bytes (PDF `%PDF-`, DOCX ZIP `PK\x03\x04`).
- **File Size Quota**: Hard limit at 10 MB per document to prevent memory exhaustion / zip-bomb DoS.
- **Safe Storage**: Uploaded files are stored in a dedicated `private_storage/` root outside the web-accessible static media directory with cryptographically randomized filesystem names.
- **Zero Macro/Code Execution**: Documents are parsed purely as static binary structures via PyMuPDF and python-docx without invoking Microsoft Office or Adobe executable engines.

## 3. Data Retention & Privacy Deletion Policy
- **Right to Erasure**: Deleting a resume immediately unlinks and purges the binary file from disk and deletes extracted sections, entities, and evidence from the database.
- **Account Deletion**: Invoking `/api/v1/settings/delete-account/` triggers a cascading purge of all user records, uploaded files, matches, roadmaps, and audit records.
- **Redacted Audit Trails**: System logs and audit events record operation outcomes (e.g. `RESUME_UPLOADED`, `MATCH_GENERATED`) without storing raw resume text or personally identifiable candidate records.
