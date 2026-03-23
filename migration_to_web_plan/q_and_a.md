# BID Web Migration — Technical Discovery & Strategic Suggestions

> **Version:** 1.0  
> **Date:** 2026-03-20  

---

## Part 1: Technical Discovery Questions

These questions must be answered before finalizing the architecture. Each answer may impact design decisions noted in **[Impact]**.

---

### 1. Deployment Environment

**Q1.1:** Where will the web application be deployed?  
- a) Local workstation (same machine as photos)  
- b) NAS / home server (local network)  
- c) Cloud VM (e.g., VPS, AWS EC2)  
- d) Docker-native platform (e.g., Unraid, Synology Docker)  

**[Impact]:** Determines TLS strategy (self-signed vs. Let's Encrypt), FileBrowser volume mapping, and whether Docker is even available. If (a), we can simplify to a single `uvicorn` + `next dev` setup without Nginx.

**Answer**:
- Web app will be deployed on local home server, with VPN access for remote users. Docker is available and preferred for ease of deployment and isolation.

**Q1.2:** Is Docker available and acceptable on the target machine?  

**[Impact]:** The architecture assumes Docker Compose for orchestration. If Docker is unavailable, we need systemd/PM2 service configs instead.

**Answer**:
- Docker is available and acceptable. We will proceed with a Docker Compose-based architecture.

---

### 2. Multi-User & Collaboration

**Q2.1:** Will multiple users access the system concurrently?  

**[Impact]:** If single-user, we can skip the auth system entirely (or use a simple PIN). If multi-user:
- `source_dict.json` needs locking or migration to SQLite
- Per-user project isolation (RBAC) is needed
- FileBrowser needs per-user scope configuration

**Answer**:
- Multiple users will access the system concurrently, primarily for browsing and monitoring export status. There could be multiple users uploading photos at the same time, but processing can be done by the system one photo at a time. 
- `source_dict.json` will be migrated to SQLite. 

**Q2.2:** If multi-user — should different users see each other's projects?  

**[Impact]:** Affects project listing and FileBrowser scoping.

**Answer**:
- There should be only one instance project at a time. 

---

### 3. Filesystem Access

**Q3.1:** Are source/export folders always on the local filesystem, or can they be on network shares (SMB/CIFS, NFS)?  

**[Impact]:** Network shares introduce:
- Latency for file operations (the async DOWNLOADING → NEW monitor is already designed for this)
- Permission issues (NTFS vs POSIX ACLs)
- FileBrowser may need special mount configuration
- Docker volume mapping differs for network mounts

**Answer**:
- System should be prepared for using network shares, but the initial deployment will be on a local filesystem. We will test with a local folder first and then validate with a network share.

**Q3.2:** What is the typical size of a source folder? (number of subfolders × photos per subfolder)  

**[Impact]:** 
- <1,000 photos: JSON persistence is fine
- 1,000–10,000: JSON works but tree virtualization is mandatory in frontend
- 10,000+: Consider SQLite migration in Phase 1 instead of deferring

**Answer**:
- Typical there is around 5,000 photos per project with 5-15 photographers. Typical size is around 7 Gb per project.

**Q3.3:** What is the largest `source_dict.json` you've encountered (in MB)?  

**[Impact]:** If >10MB, we need paginated API responses and incremental tree loading instead of sending the full dict to the frontend.

**Answer**:
- It is hard to say, but `source_dict.json` will be migrated to SQLite, so this question becomes irrelevant.
---

### 4. FileBrowser Specifics

**Q4.1:** Which FileBrowser version do you plan to use? (latest v2.x stable?) Are there any custom configurations or plugins?  

**[Impact]:** Proxy auth method, API compatibility, and embedding behavior differ across versions.

**Answer**:
- Latest stable version. 

**Q4.2:** What specific FileBrowser features do you need?  
- a) Browse files (read-only)
- b) Upload new photos via FileBrowser
- c) Delete/rename files via FileBrowser
- d) Share download links
- e) File editing (text/code files)

**[Impact]:** If (b), we need a filesystem watcher to trigger `update_source_dict()` when new files appear. If (c), integrity checks must handle unexpected deletions.

**Answer**:
- Browse, upload, delete, rename files. 

**Q4.3:** Should FileBrowser replace the source tree component, or complement it?  

**[Impact]:** If replace — the source tree component (Phase 4) is simplified to a processing-state view only. If complement — both coexist, FileBrowser handles raw file management, source tree handles processing state.

**Answer**:
- Yes

---

### 5. Authentication & Security

**Q5.1:** Is there an existing identity provider (Active Directory, LDAP, OAuth2/OIDC) that the system should integrate with?  

**[Impact]:** If yes — replace the custom JWT auth with passport/OAuth2 flow. If no — the simple JSON-backed user store in the plan is sufficient.

**Answer**:
- No. 

**Q5.2:** Is the application internet-facing or purely local network?  

**[Impact]:** Internet-facing requires: TLS (mandatory), rate limiting, fail2ban integration, CSP headers, and more aggressive input validation. Local-only allows relaxed security posture.

**Answer**:
- App should be designed with internet-facing in mind, but initial deployment will be local network only. We will implement TLS with self-signed certs and allow configuration for Let's Encrypt in the future.

**Q5.3:** How many user accounts are expected?  

**[Impact]:** 1–5 users: JSON file is fine. 5+: SQLite user table. 50+: Postgres with proper password policies.

**Answer**:
- 7-17 photographers acount, 3 admin acount, 5-10 PR acounts. So around 30 user accounts total. We will implement a SQLite user table for this scale.

---

### 6. Event System

**Q6.1:** Are event source URLs always HTTP(S), or can they be local file paths?  

**[Impact]:** The current code supports both via `detect_source_type()`. The API needs to handle both — local paths need filesystem access validation; URLs need timeout handling and SSL verification.

**Answer**:
- Event source can be local files or HTTP(S) URLs. We will ensure the API can handle both types with appropriate validation and error handling.

**Q6.2:** How frequently do event schedules change during a live event?  

**[Impact]:** If schedules change every few minutes during a concert, the 60-second background refresh may not be fast enough. Consider adding a manual "Reload Now" button (already planned) and potentially reducing the auto-refresh interval.

**Answer**:
- Ones every 5 minute. 

**Q6.3:** Is the event system used for every project, or only for specific "concert photography" projects?  

**[Impact]:** If optional — the events tab should be hidden/collapsible for projects that don't use it, reducing UI clutter.

**Answer**:
- event system should be configurable per project. There can be project witour event system, and project with event system.

---

### 7. Image Processing Pipeline

**Q7.1:** Is the current 3-thread `ThreadPoolExecutor` sufficient for your workloads, or do you need faster processing?  

**[Impact]:** If faster processing is needed:
- Increase worker count (limited by RAM — each image load can be 50–200MB for TIF)
- Move to multiprocessing (already ruled out due to Tkinter, but viable in web context)
- Move to Celery + Redis for distributed processing

**Answer**:
- This should be configurable, but project should be writen for RAM optimization in mind. We will start with the current `ThreadPoolExecutor` and monitor performance. If we find that processing is too slow, we can explore increasing the worker count or moving to a more robust job queue system like Celery or ARQ.

**Q7.2:** Are there plans to add new export operations (e.g., AI upscaling, face detection, auto-crop)?  

**[Impact]:** If yes — the plugin architecture should be designed now. Each processing step should be a composable unit, not hardcoded in `process_photo_task`.

**Answer**:
- Export profile should cosider only basic information like: resolution in px, scaling methotd, output format, quality, if logo should be applied, logo positioning. 

**Q7.3:** Should processed images be viewable through the web UI (full resolution), or only as thumbnails/previews?  

**[Impact]:** Full-resolution serving requires:
- Nginx static file serving from export folder (efficient)
- Progressive JPEG loading in frontend
- Potential CDN if internet-facing

**Answer**:
- only thumbnails/previews should be viewable through the web UI. Full-resolution images can be accessed on domand. 

---

### 8. Data & Persistence

**Q8.1:** Should the system support project import/export (e.g., zip a project's JSON files and re-import elsewhere)?  

**[Impact]:** Adds API endpoints for archive creation/extraction. Affects how paths are stored (relative vs. absolute).

**Answer**:
- Yes, project import/export is a valuable feature for backup and migration purposes. Zip files should contain the SQLite database (or JSON files if we stick with that) along with any necessary metadata. Paths should be stored as relative to allow for flexibility when importing on different machines.

**Q8.2:** Is there any need for historical tracking (e.g., "who processed this photo and when")?  

**[Impact]:** Currently `source_dict` only stores the latest state. An audit log would require either:
- Appending to a log file (simple)
- State history in a database (complex but queryable)

**Answer**:
- The photo should be proceed automaticly. every photo should have history (data do added, date od every export, date od change etc.)

**Q8.3:** The current `source_dict.json` stores absolute file paths (e.g., `D:\source\Session1\photo.tif`). Is this acceptable for the web version, or should paths be relative?  

**[Impact]:** Absolute paths:
- Break when moving between machines
- Expose filesystem structure in API responses
- Don't work in Docker (different mount paths)

Recommendation: Store relative paths in `source_dict.json`, resolve to absolute using project settings at runtime.

**Answer**:
- Paths should be stored as relative in the database, and resolved to absolute paths at runtime based

---

### 9. Existing Infrastructure

**Q9.1:** Is there an existing CI/CD pipeline (GitHub Actions, GitLab CI, Jenkins)?  

**[Impact]:** Determines whether `.github/workflows/ci.yml` (Phase 8) is the right format.

**Answer**:
- There is currently no CI/CD pipeline in place. 

**Q9.2:** Is version control currently used? If so, which platform (GitHub, GitLab, Bitbucket)?  

**[Impact]:** Affects deployment strategy and CI/CD configuration.

**Answer**:
- Yes, version control is currently used with GitHub. 

**Q9.3:** Are there any existing monitoring or logging systems in use?  

**[Impact]:** The backend currently writes to `logs/YYYY-MM-DD.log`. For web deployment, consider centralized logging (Loki, ELK) or at minimum structured JSON logging.

**Answer**:
- Currently, there are no centralized monitoring or logging systems in place. Logs are written to local files. For the web version, we will implement structured JSON logging and consider integrating with a centralized logging solution in the future for better observability. Logs should be vissible in UI. 

---

### 10. Migration Priorities

**Q10.1:** What is the single most important feature to have working first in the web version?  
- a) Photo browsing + EXIF viewing (read-only)
- b) Photo processing (full pipeline)
- c) Event-based sorting
- d) FileBrowser integration

**[Impact]:** Determines which phase to prioritize. If (a), Phase 4 is the MVP. If (b), Phase 5. If (d), Phase 6 can be brought forward.

**Answer**:
- photo processign (full pipeline) is the most important feature to have working first in the web version. This will be our primary focus for the initial release, ensuring that the core functionality of processing photos is robust and efficient before adding additional features like browsing, event sorting, or FileBrowser integration.

**Q10.2:** Should the existing Tkinter desktop app continue working alongside the web version during migration?  

**[Impact]:** If yes — the backend `bid/` package must remain backward-compatible with `app.py` (Tkinter). No breaking changes to function signatures. The API layer is purely additive.

**Answer**:
- No, this should be ne UI. There is no need to keep the Tkinter app working alongside the web version during migration. The web version will be a complete replacement for the desktop app, and we will focus on ensuring that all necessary features are implemented in the web version before deprecating the Tkinter app.

**Q10.3:** Is there a deadline or specific event (e.g., a concert season) this needs to be ready for?  

**[Impact]:** Affects scope — may need to cut Phase 7 (events UI) or Phase 8 (full testing) for an initial release.

**Answer**:
- Milestones is deecibed in \migration_to_web_plan\github_milestones_and_issues_plan.md, and adde to github. 
---

## Part 2: Strategic Suggestions

### Suggestion 1: Docker Compose Stack with Dev/Prod Profiles

**What:** Package the entire application (FastAPI + Next.js + FileBrowser + Nginx) into a single `docker-compose.yml` with environment-specific profiles.

**Why this adds value:**
- **One-command deployment:** `docker compose up -d` — no Python/Node installation needed on the target machine.
- **Reproducible environments:** Eliminates "works on my machine" problems.
- **Easy updates:** `docker compose pull && docker compose up -d` for version upgrades.
- **Dev/prod parity:** Development uses `docker compose --profile dev up` with hot-reload volumes; production uses pre-built images.

**Effort:** Low — standard Docker Compose configuration. Already partially spec'd in Phase 6/8.

**Risk:** Docker may not be available on all target machines (see Q1.2).

**Answer**:
- We will proceed with a Docker Compose-based architecture as it provides significant benefits in terms of deployment and environment consistency. We will ensure that the `docker-compose.yml` is well-documented and includes profiles for both development and production environments to facilitate ease of use.

---

### Suggestion 2: Thumbnail Cache with Content-Addressable Storage

**What:** Pre-generate and cache image thumbnails using content-hashing (SHA256 of file path + mtime) instead of generating previews on every API request.

**Architecture:**
```
/data/.cache/thumbnails/
  ├── {sha256_hash}_800.jpg    # Preview (800px)
  ├── {sha256_hash}_200.jpg    # Thumbnail (200px, for tree view)
  └── {sha256_hash}_exif.json  # Cached EXIF extraction
```

**Why this adds value:**
- **Performance:** First preview load: ~500ms (PIL resize). Subsequent loads: <10ms (static file serve via Nginx).
- **Bandwidth:** 200px thumbnails (~15KB each) enable a gallery grid view without loading 30MB TIF files.
- **Source tree enrichment:** Tiny thumbnails next to filenames in the source tree.
- **Cache invalidation:** Trivial — if `mtime` changes, the hash changes, old cache entry is orphaned and garbage-collected.

**Effort:** Medium — add a cache layer to the preview endpoint + Nginx static serving rule + periodic cache cleanup background task.

**Risk:** Disk space — ~20KB per photo × 2 sizes = ~40KB per photo. For 10,000 photos: ~400MB. Acceptable.

**Answer**:
- App should use RAM optimalization. Disk space is not a problem. 

---

### Suggestion 3: Background Job Queue with Persistence (Celery / ARQ)

**What:** Replace the in-process `ThreadPoolExecutor` with a proper background job queue that persists across application restarts.

**Why this adds value:**
- **Crash recovery:** If the server crashes mid-processing, queued jobs survive in Redis and resume on restart. Current implementation loses all queued work.
- **Observability:** Job queue dashboards (Flower for Celery) show active/pending/failed jobs.
- **Rate limiting:** Control concurrent processing load independent of API server.
- **Scalability:** Add more worker processes trivially (`celery worker --concurrency=8`).
- **Priority queues:** Urgent re-processing can jump ahead of batch jobs.

**Trade-off:** Adds Redis dependency (or SQLite backend for ARQ). More complex deployment.

**Recommendation:** Use **ARQ** (async Redis queue, Python-native) instead of Celery for lighter footprint. Or defer entirely if the 3-thread ThreadPoolExecutor meets current needs (see Q7.1).

**Answer**:
- Start implementing more robust Job Quere system that will replace the current `ThreadPoolExecutor`. We will evaluate ARQ for its simplicity and Python-native design, which may be a better fit for our use case compared to Celery. This will provide improved reliability and scalability for our photo processing tasks.

---

### Suggestion 4: Progressive Web App (PWA) Support

**What:** Add PWA capabilities to the Next.js frontend — installable, offline-capable (for metadata browsing), push notifications.

**Why this adds value:**
- **Native feel:** Installable on Windows/Mac/Linux as a desktop app — gives users the same UX as the Tkinter app.
- **Notifications:** Push notification when batch processing completes (useful for large jobs that take minutes).
- **Offline metadata:** Cache `source_dict` in IndexedDB for browsing EXIF data and export status without network access.
- **Mobile preview:** Photographers can check export status from their phone at events.

**Effort:** Low — Next.js has first-party PWA support via `next-pwa` package. Service worker configuration + manifest.json.

**Risk:** Minimal — progressive enhancement, doesn't affect core functionality.

**Answer**:
- No. 

---

### Suggestion 5: API Versioning with OpenAPI Spec Export

**What:** Leverage FastAPI's automatic OpenAPI (Swagger) spec generation as a contract between backend and frontend, with version pinning.

**Why this adds value:**
- **Auto-generated documentation:** `/api/v1/docs` gives interactive API documentation for free (Swagger UI).
- **Type safety across boundary:** Use `openapi-typescript-codegen` to auto-generate TypeScript API client from the OpenAPI spec. Eliminates manual type synchronization between Python Pydantic models and TypeScript interfaces.
- **Contract testing:** The OpenAPI spec becomes a testable contract — frontend CI can verify it matches expected schema.
- **Version management:** When breaking changes are needed, deploy `/api/v2/` alongside `/api/v1/` with a deprecation timeline.

**Implementation:**
```bash
# Auto-generate TypeScript client from running API:
npx openapi-typescript-codegen \
  --input http://localhost:8000/api/v1/openapi.json \
  --output frontend/lib/api-generated/ \
  --client fetch
```

**Effort:** Very low — FastAPI generates OpenAPI by default. The codegen step is a single npm script.

**Risk:** None — purely additive, improves development velocity.

**Answer**:
- We will implement API versioning and leverage FastAPI's OpenAPI spec generation to create a robust contract between the backend and frontend. This will improve development velocity and maintainability by ensuring type safety across the API boundary and providing auto-generated documentation for developers.

---

## Part 3: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `source_dict.json` corruption under concurrent access | Medium | High | File-level locking in FastAPI; SQLite migration in Phase 2+ |
| Large TIF files (50MB+) overwhelm preview endpoint | High | Medium | Thumbnail cache (Suggestion 2); lazy loading |
| FileBrowser version incompatibility | Low | Medium | Pin Docker image version; test proxy auth in Phase 6 |
| Tkinter app breaks after `bid/` package changes | Medium | High | Zero modifications to `bid/` in Phase 1; keep Tkinter app runnable |
| WebSocket connection instability | Medium | Low | Auto-reconnect with backoff; REST fallback for critical operations |
| Windows path inconsistencies in Docker | High | Medium | Normalize all paths at API boundary; test on Windows Docker Desktop |
