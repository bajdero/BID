# User Stories — Real-Time Photo Management Application

## Overview

This application is a real-time photo management tool used by photographers and PR teams responsible for social media. Its primary goal is to provide a fast, easy-to-use platform for managing photos, including uploading, sorting, filtering, categorizing, and exporting them.

---

## Actors

| Actor | Description |
|---|---|
| **Photographer** | Uploads photos from the field; views and sorts their own submissions |
| **PR Team Member** | Reviews all uploaded photos; manages tags and descriptions for social media use. Can download photos for external use. |
| **Admin** | Full system control: manages users, events, exports, and monitors system health |
| **System** | Performs automatic background tasks: indexing, categorization, rating, export |

---

## Shared Features

### US-S01 — Authentication
> As **any user**, I want to log in with my unique credentials, so that my access is restricted to my role and my actions are traceable.

**Acceptance criteria:**
- Each user has a unique username/email and password.
- Access to features is determined by the user's role (Photographer, PR, Admin).
- Failed login attempts are logged.

---

### US-S02 — Photo Filtering
> As **any user**, I want to filter photos by multiple criteria, so that I can quickly find the photos I need.

**Acceptance criteria:**
- Filters available: date of creation, aspect ratio, tags, event, photographer.
- Negative filtering is supported (e.g., "exclude photos without exports", "exclude photos without a specific tag").
- Multiple filters can be combined simultaneously.

---

### US-S03 — Semantic/Vector Search
> As **any user**, I want to search photos using natural language, so that I can find relevant photos without knowing exact metadata values.

**Acceptance criteria:**
- Search engine considers: description, tags, aspect ratio, event name, and other metadata.
- Search uses semantic/vector retrieval with relevance ranking.
- Results are ranked by relevance.

---

### US-S04 — Photo Description
> As **any user**, I want to add and edit a text description for each photo, so that context and notes can be attached to individual images. This should be accessible and editable via API for integration with external systems.

**Acceptance criteria:**
- Each photo has a description field that is readable and writable via API, for integration with external systems.
- Descriptions are included in semantic/vector search indexing.
- Description updates are available in both UI and external API.

---

### US-S05 — Language Support
> As **any user**, I want the application to support multiple languages, so that I can use it in my preferred language.

**Acceptance criteria:**
- The application supports at least English and Polish.
- UI translations are available in EN/PL for all core views.
- Tag vocabulary and metadata labels support EN/PL usage rules.

---

### US-S06 — Multi-User RBAC (Day 1)
> As **any user**, I want role-based access control from the first release, so that each role only has the permissions required for their work.

**Acceptance criteria:**
- Multi-user operation is enabled in the first production release.
- Role matrix is enforced for Photographer, PR Team Member, and Admin.
- Unauthorized actions are rejected and logged.

---

### US-S07 — Hash-Based Deduplication
> As **any user**, I want photos identified by content hash, so that duplicate and re-upload behavior is reliable regardless of filename.

**Acceptance criteria:**
- Canonical photo identity is content hash only.
- Re-uploading a file with the same name but different bytes is treated as a new photo.
- Re-uploading identical bytes is detected as duplicate without creating inconsistent state.

## Photographer Stories

### US-P00 — Upload Photos
> As a **photographer**, I want to upload photos, so that they are available in the system for review and export.

**Acceptance criteria:**
- Uploaded photos are validated against supported format allowlist.
- Unsupported auxiliary/system files are skipped without blocking valid files.
- Upload completion state is tracked before indexing begins.


### US-P01 — View Own Photos
> As a **photographer**, I want to see all photos I have uploaded, so that I can review my own submissions.

**Acceptance criteria:**
- The default view shows only the authenticated photographer's photos.
- Photos can be sorted by date, aspect ratio, and location.

---

### US-P02 — Automatic Event Categorization on Upload
> As a **photographer**, when I upload a photo, I want it to be automatically assigned to the correct event, so that I do not need to categorize it manually.

**Acceptance criteria:**
- Event assignment is based on the EXIF capture date/time matched against defined event time ranges.
- If no matching event is found, the photo is placed in an "Uncategorized" bucket.

---

### US-P03 — Automatic Rating on Upload
> As a **photographer**, when I upload a photo, I want it to receive an automatic quality rating based on its EXIF data, so that I can prioritize the best shots faster.

**Acceptance criteria:**
- Rating is calculated from available EXIF metadata (e.g., exposure, focus, ISO).
- Rating is visible in the photo detail view.
- Rating logic in v1 is deterministic and rule-based.
- ML-based scoring is treated as a future enhancement.

---

## PR Team Stories

### US-PR01 — View All Photos
> As a **PR team member**, I want to see all photos uploaded by all photographers, so that I can select the best images for social media.

**Acceptance criteria:**
- PR members can browse the full photo library across all photographers and events.

---

### US-PR02 — Filter and Search Photos
> As a **PR team member**, I want to filter and search photos by date, event, aspect ratio, and tags, so that I can find suitable photos efficiently.

**Acceptance criteria:**
- All shared filters (US-S02, US-S03) are available.

---

### US-PR03 — Manage Tags
> As a **PR team member**, I want to add, edit, and remove tags on photos, so that photos are easier to find and organize for publication.

**Acceptance criteria:**
- Tags can be added or removed individually or in bulk.
- Tags are readable/writable in both UI and external API (subject to permissions).
- Tag changes are reflected immediately in search results.

---

### US-PR04 — Curated Collections
> As a **PR team member**, I want to create curated collections from selected photos, so that campaign-ready sets can be prepared quickly.

**Acceptance criteria:**
- PR can create, rename, and delete collections.
- Photos can be added/removed in bulk.
- Collections are filterable by event and photographer.

---

### US-PR05 — Approval Workflow
> As a **PR team member**, I want to submit selected photos for approval, so that publishing decisions are traceable.

**Acceptance criteria:**
- Photos support approval states (e.g., draft, in_review, approved, rejected).
- State changes are logged in audit history.
- Admin can override approval state when needed.

---

### US-PR06 — Scheduled Social Publish Packs
> As a **PR team member**, I want to schedule publish packs, so that approved photo sets are prepared and delivered on time.

**Acceptance criteria:**
- A publish pack can include selected photos, target channels, and schedule timestamp.
- Only approved photos can be included in scheduled packs.
- Pack execution and failures are logged and visible in UI.

---

## Admin Stories

### US-A01 — User Management
> As an **admin**, I want to add and remove photographers and PR team members, so that access to the system reflects current team membership.

**Acceptance criteria:**
- Admin can create, deactivate, and delete user accounts.
- Admin can assign or change user roles.

---

### US-A02 — Event Management
> As an **admin**, I want to add and remove events with defined time ranges, so that photos are automatically categorized correctly.

**Acceptance criteria:**
- Each event has a name, start datetime, and end datetime.
- Photos already indexed are re-evaluated when events are modified.

---

### US-A03 — Photo Management
> As an **admin**, I want to add and remove photos in the system, so that the library stays accurate and clean.

**Acceptance criteria:**
- Admin can delete individual photos or batches.
- Deleted photos are removed from all indexes and exports.

---

### US-A04 — Configure Automatic Export
> As an **admin**, I want to configure automatic photo export rules (destination folder, file naming pattern), so that photos are delivered to the right place without manual work.

**Acceptance criteria:**
- Admin defines target export folder path and file naming template.
- Export rules can be scoped to specific events or tags.
- Admin can start and stop the automatic export process at any time.
- Export conflict policy is block by default (no silent overwrite).
- Admin can resolve blocked conflicts in UI for single file, multi-selection, or apply-to-all action.
- Export does not fail silently — errors are logged and surfaced in the UI.

---

### US-A05 — Action History / Audit Log
> As an **admin**, I want to see a full history of actions performed by all users, so that I can audit usage and troubleshoot issues.

**Acceptance criteria:**
- Logged actions include: photo uploads, tag changes, exports, logins, user management changes.
- Logs are filterable by user, action type, and date range.
- Event System Manager changes are included in the history.
- Audit records are immutable append-only.

---

### US-A06 — Queue and Worker Monitoring
> As an **admin**, I want to see real-time queue and worker health, so that I can ensure processing is running smoothly and identify bottlenecks.

**Acceptance criteria:**
- Dashboard shows queue length, worker utilization, and processing error rate.
- Monitoring data is updated in near real-time.

---

### US-A07 — Task Queue Monitoring
> As an **admin**, I want to see the list of pending and active system tasks and which worker (CPU/GPU) is handling each, so that I can identify bottlenecks and monitor processing progress.

**Acceptance criteria:**
- Task queue lists all pending, in-progress, and recently completed tasks.
- Each task shows: type, status, assigned worker, start time, and duration.
- Queue view includes aggregate queue length and per-worker utilization.

---

### US-A08 — Export Conflict Resolution
> As an **admin**, I want blocked export conflicts to be resolved explicitly, so that file replacement decisions remain controlled and auditable.

**Acceptance criteria:**
- On conflict, export is paused/blocked and surfaced in UI.
- Admin can choose action for one item, selected items, or all pending conflicts.
- Each decision is written to immutable audit history.

---

## Known Bugs (Backlog)

These issues have been identified in the current system and must be resolved:

| ID | Description | Priority |
|---|---|---|
| BUG-01 | When a file is indexed, then deleted, and a new file with the same name is uploaded, the new file is not re-indexed. | High |
| BUG-02 | The application cannot overwrite an already existing export file. | High |
| BUG-03 | Some platforms (e.g., iOS) upload auxiliary/system files alongside photos. The application must only process files with supported extensions (`.jpg`, `.jpeg`, `.png`, `.tiff`, `.raw`, etc.) and silently skip unsupported files. | Medium |
| BUG-04 | Intermittent "file is not seekable" error occurs during file processing. | High |
| BUG-05 | Indexing a file while it is still being uploaded/downloaded does not work correctly. This must function for both in-app uploads and filebrowser-based indexing. | High |
| BUG-06 | The Event System Manager lacks a change history. All configuration changes must be logged. | Medium |

---

## Suggestions

### SUG-01 — Webhook / API Integration for Descriptions and Tags
The requirement that descriptions be accessible and editable via API suggests a need for a well-documented REST (or GraphQL) API with authentication tokens (e.g., API keys or OAuth2). This API should be part of the technical specification from the start, not added as an afterthought.

### SUG-02 — File Deduplication
BUG-01 reveals a missing deduplication strategy. Use a content hash (e.g., SHA-256 of file bytes) as the canonical identifier rather than filename alone. This solves re-upload issues and prevents duplicate photos in general.

### SUG-03 — Supported Format Allowlist (BUG-03)
Define and maintain a server-side allowlist of accepted MIME types and file extensions. Validation should happen at the upload boundary (before any processing begins) to avoid wasted resources and potential security issues with unexpected file types.

### SUG-04 — Resumable / Chunked Uploads (BUG-04, BUG-05)
"File is not seekable" and "indexing while downloading" errors are strongly related to streaming uploads. Implementing chunked or resumable uploads (e.g., using the tus protocol or multipart upload) would resolve both issues: indexing would only begin after the full file has been received and written to disk.

### SUG-05 — Role-Based Access Control (RBAC)
As the number of roles grows (Photographer, PR, Admin), explicitly define permissions as a matrix in the technical requirements. This prevents scope creep and makes it easier to implement and audit security boundaries.

### SUG-06 — Event History as an Immutable Append-Only Log
For both the Event System Manager history (BUG-06) and the Admin audit log (US-A05), consider an append-only log model. Records are never modified or deleted — this ensures a trustworthy audit trail and simplifies data integrity.

### SUG-07 — Async Task Processing Architecture
Given that automatic rating, EXIF parsing, event categorization, and export are all background tasks, the technical architecture should include a dedicated job/task queue (e.g., Celery, RQ, or a similar system). This directly supports US-A07 and ensures the UI remains responsive during heavy processing.

### SUG-08 — PR Team Story Completion
PR workflow should include curated collections, approval flow, and scheduled social publish packs.


