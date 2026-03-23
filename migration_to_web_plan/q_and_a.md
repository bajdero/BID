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

**Q1.2:** Is Docker available and acceptable on the target machine?  

**[Impact]:** The architecture assumes Docker Compose for orchestration. If Docker is unavailable, we need systemd/PM2 service configs instead.

---

### 2. Multi-User & Collaboration

**Q2.1:** Will multiple users access the system concurrently?  

**[Impact]:** If single-user, we can skip the auth system entirely (or use a simple PIN). If multi-user:
- `source_dict.json` needs locking or migration to SQLite
- Per-user project isolation (RBAC) is needed
- FileBrowser needs per-user scope configuration

**Q2.2:** If multi-user — should different users see each other's projects?  

**[Impact]:** Affects project listing and FileBrowser scoping.

---

### 3. Filesystem Access

**Q3.1:** Are source/export folders always on the local filesystem, or can they be on network shares (SMB/CIFS, NFS)?  

**[Impact]:** Network shares introduce:
- Latency for file operations (the async DOWNLOADING → NEW monitor is already designed for this)
- Permission issues (NTFS vs POSIX ACLs)
- FileBrowser may need special mount configuration
- Docker volume mapping differs for network mounts

**Q3.2:** What is the typical size of a source folder? (number of subfolders × photos per subfolder)  

**[Impact]:** 
- <1,000 photos: JSON persistence is fine
- 1,000–10,000: JSON works but tree virtualization is mandatory in frontend
- 10,000+: Consider SQLite migration in Phase 1 instead of deferring

**Q3.3:** What is the largest `source_dict.json` you've encountered (in MB)?  

**[Impact]:** If >10MB, we need paginated API responses and incremental tree loading instead of sending the full dict to the frontend.

---

### 4. FileBrowser Specifics

**Q4.1:** Which FileBrowser version do you plan to use? (latest v2.x stable?) Are there any custom configurations or plugins?  

**[Impact]:** Proxy auth method, API compatibility, and embedding behavior differ across versions.

**Q4.2:** What specific FileBrowser features do you need?  
- a) Browse files (read-only)
- b) Upload new photos via FileBrowser
- c) Delete/rename files via FileBrowser
- d) Share download links
- e) File editing (text/code files)

**[Impact]:** If (b), we need a filesystem watcher to trigger `update_source_dict()` when new files appear. If (c), integrity checks must handle unexpected deletions.

**Q4.3:** Should FileBrowser replace the source tree component, or complement it?  

**[Impact]:** If replace — the source tree component (Phase 4) is simplified to a processing-state view only. If complement — both coexist, FileBrowser handles raw file management, source tree handles processing state.

---

### 5. Authentication & Security

**Q5.1:** Is there an existing identity provider (Active Directory, LDAP, OAuth2/OIDC) that the system should integrate with?  

**[Impact]:** If yes — replace the custom JWT auth with passport/OAuth2 flow. If no — the simple JSON-backed user store in the plan is sufficient.

**Q5.2:** Is the application internet-facing or purely local network?  

**[Impact]:** Internet-facing requires: TLS (mandatory), rate limiting, fail2ban integration, CSP headers, and more aggressive input validation. Local-only allows relaxed security posture.

**Q5.3:** How many user accounts are expected?  

**[Impact]:** 1–5 users: JSON file is fine. 5+: SQLite user table. 50+: Postgres with proper password policies.

---

### 6. Event System

**Q6.1:** Are event source URLs always HTTP(S), or can they be local file paths?  

**[Impact]:** The current code supports both via `detect_source_type()`. The API needs to handle both — local paths need filesystem access validation; URLs need timeout handling and SSL verification.

**Q6.2:** How frequently do event schedules change during a live event?  

**[Impact]:** If schedules change every few minutes during a concert, the 60-second background refresh may not be fast enough. Consider adding a manual "Reload Now" button (already planned) and potentially reducing the auto-refresh interval.

**Q6.3:** Is the event system used for every project, or only for specific "concert photography" projects?  

**[Impact]:** If optional — the events tab should be hidden/collapsible for projects that don't use it, reducing UI clutter.

---

### 7. Image Processing Pipeline

**Q7.1:** Is the current 3-thread `ThreadPoolExecutor` sufficient for your workloads, or do you need faster processing?  

**[Impact]:** If faster processing is needed:
- Increase worker count (limited by RAM — each image load can be 50–200MB for TIF)
- Move to multiprocessing (already ruled out due to Tkinter, but viable in web context)
- Move to Celery + Redis for distributed processing

**Q7.2:** Are there plans to add new export operations (e.g., AI upscaling, face detection, auto-crop)?  

**[Impact]:** If yes — the plugin architecture should be designed now. Each processing step should be a composable unit, not hardcoded in `process_photo_task`.

**Q7.3:** Should processed images be viewable through the web UI (full resolution), or only as thumbnails/previews?  

**[Impact]:** Full-resolution serving requires:
- Nginx static file serving from export folder (efficient)
- Progressive JPEG loading in frontend
- Potential CDN if internet-facing

---

### 8. Data & Persistence

**Q8.1:** Should the system support project import/export (e.g., zip a project's JSON files and re-import elsewhere)?  

**[Impact]:** Adds API endpoints for archive creation/extraction. Affects how paths are stored (relative vs. absolute).

**Q8.2:** Is there any need for historical tracking (e.g., "who processed this photo and when")?  

**[Impact]:** Currently `source_dict` only stores the latest state. An audit log would require either:
- Appending to a log file (simple)
- State history in a database (complex but queryable)

**Q8.3:** The current `source_dict.json` stores absolute file paths (e.g., `D:\source\Session1\photo.tif`). Is this acceptable for the web version, or should paths be relative?  

**[Impact]:** Absolute paths:
- Break when moving between machines
- Expose filesystem structure in API responses
- Don't work in Docker (different mount paths)

Recommendation: Store relative paths in `source_dict.json`, resolve to absolute using project settings at runtime.

---

### 9. Existing Infrastructure

**Q9.1:** Is there an existing CI/CD pipeline (GitHub Actions, GitLab CI, Jenkins)?  

**[Impact]:** Determines whether `.github/workflows/ci.yml` (Phase 8) is the right format.

**Q9.2:** Is version control currently used? If so, which platform (GitHub, GitLab, Bitbucket)?  

**[Impact]:** Affects deployment strategy and CI/CD configuration.

**Q9.3:** Are there any existing monitoring or logging systems in use?  

**[Impact]:** The backend currently writes to `logs/YYYY-MM-DD.log`. For web deployment, consider centralized logging (Loki, ELK) or at minimum structured JSON logging.

---

### 10. Migration Priorities

**Q10.1:** What is the single most important feature to have working first in the web version?  
- a) Photo browsing + EXIF viewing (read-only)
- b) Photo processing (full pipeline)
- c) Event-based sorting
- d) FileBrowser integration

**[Impact]:** Determines which phase to prioritize. If (a), Phase 4 is the MVP. If (b), Phase 5. If (d), Phase 6 can be brought forward.

**Q10.2:** Should the existing Tkinter desktop app continue working alongside the web version during migration?  

**[Impact]:** If yes — the backend `bid/` package must remain backward-compatible with `app.py` (Tkinter). No breaking changes to function signatures. The API layer is purely additive.

**Q10.3:** Is there a deadline or specific event (e.g., a concert season) this needs to be ready for?  

**[Impact]:** Affects scope — may need to cut Phase 7 (events UI) or Phase 8 (full testing) for an initial release.

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
