# BID Web Architecture — System Design Document

> **Version:** 1.2  
> **Date:** 2026-03-23  
> **Stack:** Next.js 14 (React/TypeScript) · FastAPI (Python 3.10+) · FileBrowser · Nginx · SQLite · Vector Index  

---

## 1. System Topology

```
┌──────────────────────────────────────────────────────────────────────┐
│                        REVERSE PROXY (Nginx / Caddy)                 │
│                        :443 (HTTPS) / :80 (HTTP)                     │
│                                                                      │
│   /              → Next.js   (frontend SSR + static assets)          │
│   /api/*         → FastAPI   (backend REST + WebSocket)              │
│   /files/*       → FileBrowser (filesystem management UI)            │
└────────────┬─────────────────────┬─────────────────┬─────────────────┘
             │                     │                 │
     ┌───────▼───────┐    ┌───────▼───────┐  ┌──────▼──────┐
     │   NEXT.JS     │    │   FASTAPI     │  │ FILEBROWSER │
     │   :3000       │    │   :8000       │  │   :8080     │
     │               │    │               │  │             │
     │ React 18+     │    │ bid/ package  │  │ Go binary   │
    │ TanStack Query│    │ ARQ queue     │  │ Auth: proxy │
     │ Tailwind CSS  │    │ WebSocket     │  │ Scope: per  │
     │ shadcn/ui     │    │ Pydantic v2   │  │   project   │
     └───────────────┘    └───────┬───────┘  └──────┬──────┘
                                  │                  │
                          ┌───────▼──────────────────▼───────┐
                          │      SHARED FILESYSTEM VOLUME    │
                          │                                  │
                          │  /data/projects/{name}/          │
                          │    ├── settings.json             │
                          │    ├── export_option.json        │
                          │    ├── event_sources.json        │
                          │    └── bid.sqlite3               │
                          │                                  │
                          │  /data/source/   (photo sources) │
                          │  /data/export/   (processed out) │
                          │  /data/logs/     (application)   │
                          └──────────────────────────────────┘
```

### 1.1 Service Responsibilities

| Service | Role | Port | Replicas |
|---------|------|------|----------|
| **Nginx** | TLS termination, routing, static cache | 443/80 | 1 |
| **Next.js** | SSR pages, client SPA, BFF proxy | 3000 | 1 |
| **FastAPI** | Business logic API, WebSocket hub | 8000 | 1 (stateful) |
| **FileBrowser** | Visual file manager for source/export folders | 8080 | 1 |

> **Note:** Multi-user support is mandatory in v1. User/auth/audit/source metadata are persisted in SQLite from day 1, using relative paths resolved at runtime.

---

## 2. API Layer Design

### 2.1 REST Endpoints

All endpoints are prefixed with `/api/v1`. Request/response bodies are JSON.

#### 2.1.1 Projects

| Method | Path | Maps To | Description |
|--------|------|---------|-------------|
| `GET` | `/projects` | `ProjectManager.get_recent_projects()` | List recent projects |
| `POST` | `/projects` | `ProjectManager.create_project()` | Create new project |
| `GET` | `/projects/{id}` | `ProjectManager.get_project_details()` | Project metadata |
| `DELETE` | `/projects/{id}` | Remove project + prune recent | Delete project |
| `GET` | `/projects/{id}/settings` | `config.load_settings()` | Get project settings |
| `PUT` | `/projects/{id}/settings` | Write `settings.json` | Update settings |
| `GET` | `/projects/{id}/export-profiles` | `config.load_export_options()` | Get export profiles |
| `PUT` | `/projects/{id}/export-profiles` | Write `export_option.json` | Update profiles |
| `POST` | `/projects/{id}/export-profiles/validate` | `validators.validate_export_profile()` | Validate a profile |

#### 2.1.2 Source Management

| Method | Path | Maps To | Description |
|--------|------|---------|-------------|
| `GET` | `/projects/{id}/sources` | Source repository service | Full source index (SQLite-backed) |
| `GET` | `/projects/{id}/sources/tree` | Derived from source index | Processing-state folder/file structure |
| `POST` | `/projects/{id}/sources/scan` | Source scanner service | Full initial scan and index build |
| `POST` | `/projects/{id}/sources/update` | Source scanner service | Incremental update and reconciliation |
| `POST` | `/projects/{id}/sources/integrity` | `source_manager.check_integrity()` | Integrity check |
| `GET` | `/projects/{id}/sources/{folder}/{photo}` | Lookup in source index | Single photo metadata |
| `GET` | `/projects/{id}/sources/{folder}/{photo}/preview` | PIL thumbnail generation | Photo preview (resized) |
| `GET` | `/projects/{id}/sources/{folder}/{photo}/exif` | Lookup EXIF from metadata store | EXIF data |
| `PATCH` | `/projects/{id}/sources/{folder}/{photo}/description` | Update metadata field | Update photo description |
| `PATCH` | `/projects/{id}/sources/{folder}/{photo}/tags` | Update metadata field | Add/remove tags |

**Identity rule:** Canonical photo identity is content hash only (`hash_id`, e.g., SHA-256). Filenames are treated as mutable attributes.

#### 2.1.3 Processing

| Method | Path | Maps To | Description |
|--------|------|---------|-------------|
| `POST` | `/projects/{id}/process` | `image_processing.process_photo_task()` | Process selected photos |
| `POST` | `/projects/{id}/process/all` | Enqueue batch in ARQ worker queue | Process all NEW photos |
| `DELETE` | `/projects/{id}/process/{folder}/{photo}` | Reset state to NEW | Re-queue photo |
| `GET` | `/projects/{id}/process/status` | Read processing queue | Current queue status |
| `GET` | `/projects/{id}/exports/conflicts` | Query blocked exports | List export conflicts |
| `POST` | `/projects/{id}/exports/conflicts/resolve` | Admin action handler | Resolve one/many/all conflicts |

#### 2.1.4 Events

| Method | Path | Maps To | Description |
|--------|------|---------|-------------|
| `GET` | `/projects/{id}/events/sources` | `EventManager.list_sources()` | List event sources |
| `POST` | `/projects/{id}/events/sources` | `EventManager.add_source()` | Register event source |
| `DELETE` | `/projects/{id}/events/sources/{loc}` | `EventManager.remove_source()` | Remove event source |
| `POST` | `/projects/{id}/events/load` | `EventManager.load_all()` | Load/reload all schedules |
| `GET` | `/projects/{id}/events/schedules` | `EventManager.schedules` | Active schedules |
| `POST` | `/projects/{id}/events/annotate` | `EventManager.annotate()` | Annotate source_dict |
| `GET` | `/projects/{id}/events/folder-map` | `EventManager.folder_map` | Event-to-folder mapping |

Default event refresh cadence is 5 minutes, with manual reload available in UI.

#### 2.1.5 System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/version` | API version + BID version |
| `GET` | `/metrics/queue` | Queue length + worker utilization + error rate |

#### 2.1.6 Search

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/projects/{id}/search/semantic` | Semantic/vector photo search |
| `POST` | `/projects/{id}/search/reindex` | Rebuild embeddings for descriptions/tags/metadata |

#### 2.1.7 Auth & Users

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Login and issue tokens |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/users` | Admin list users |
| `POST` | `/users` | Admin create user |
| `PUT` | `/users/{id}` | Admin update user role/state |
| `DELETE` | `/users/{id}` | Admin deactivate/delete user |

#### 2.1.8 Audit & PR Workflow

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/projects/{id}/audit/logs` | Filterable immutable audit stream |
| `GET` | `/projects/{id}/collections` | List curated collections |
| `POST` | `/projects/{id}/collections` | Create curated collection |
| `POST` | `/projects/{id}/approvals` | Update approval state |
| `POST` | `/projects/{id}/publish-packs` | Schedule social publish pack |

### 2.2 WebSocket Endpoint

```
ws:///api/v1/projects/{id}/ws
```

**Purpose:** Replace Tkinter's `after()` polling with server-push for real-time state updates.

**Message Protocol (JSON frames):**

```jsonc
// Server → Client: State transition
{
  "type": "state_change",
  "folder": "Session1",
  "photo": "IMG_0001.tif",
  "old_state": "new",
  "new_state": "processing",
  "timestamp": "2026-03-20T14:30:00Z"
}

// Server → Client: Processing progress
{
  "type": "progress",
  "folder": "Session1",
  "photo": "IMG_0001.tif",
  "profile": "fb",
  "status": "completed",      // "started" | "completed" | "failed"
  "duration_sec": 2.3,
  "exported_path": "export/fb/YAPA2025-03-16_Session1_IMG_0001.jpg"
}

// Server → Client: Scan update
{
  "type": "scan_update",
  "found_new": true,
  "new_count": 12,
  "updated_folders": ["Session1", "Session2"]
}

// Server → Client: Monitor update (DOWNLOADING → NEW)
{
  "type": "monitor_update",
  "folder": "Session1",
  "photo": "IMG_0002.tif",
  "ready": true
}

// Server → Client: Error
{
  "type": "error",
  "folder": "Session1",
  "photo": "IMG_0001.tif",
  "message": "Cannot read EXIF: corrupt header"
}

// Server → Client: Queue metrics update
{
  "type": "queue_metrics",
  "queue_length": 42,
  "worker_utilization": {
    "worker-1": 0.88,
    "worker-2": 0.63
  },
  "error_rate": 0.04
}

// Server → Client: Export conflict detected
{
  "type": "export_conflict",
  "profile": "fb",
  "folder": "Session1",
  "photo": "IMG_0001.tif",
  "target_path": "export/fb/YAPA2025-03-16_Session1_IMG_0001.jpg",
  "status": "blocked"
}

// Client → Server: Subscribe to specific folders (optional)
{
  "type": "subscribe",
  "folders": ["Session1"]  // empty = all
}
```

**Implementation:** The existing queue-based pattern (`_update_queue`, `_monitor_queue`, `_event_queue`) maps directly to WebSocket broadcast. Each queue consumer becomes a WebSocket message emitter.

### 2.3 Pydantic Models (Request/Response Schemas)

```python
# Core schemas derived from existing data structures

class ProjectSettings(BaseModel):
    source_folder: str
    export_folder: str

class LogoSettings(BaseModel):
    size: int = Field(ge=10, le=2000)
    opacity: int = Field(ge=0, le=100)
    x_offset: int = Field(ge=0)
    y_offset: int = Field(ge=0)

class ExportProfile(BaseModel):
    size_type: Literal["longer", "width", "height", "shorter"]
    size: int = Field(ge=100, le=10000)
    format: Literal["JPEG", "PNG"]
    quality: int = Field(ge=1, le=100)
    ratio: list[float] | None = None
    logo: dict[str, LogoSettings] | None = None
    logo_required: bool = False

class PhotoEntry(BaseModel):
    hash_id: str
    path: str
    state: Literal["downloading","new","processing","ok","ok_old","error","export_fail","deleted","skip"]
    exported: dict[str, str]
    description: str = ""
    tags: list[str] = []
    size: str
    size_bytes: int
    created: str
    mtime: float
    exif: dict[str, str]
    quality_score: float | None = None
    quality_model: Literal["exif_rules", "ml"] | None = None
    error_msg: str | None = None
    duration_sec: float | None = None
    event_folder: str | None = None
    event_id: str | None = None
    event_name: str | None = None

class SourceTree(BaseModel):
    """Folder tree for UI rendering."""
    folders: dict[str, dict[str, PhotoEntry]]

class ProcessRequest(BaseModel):
    photos: list[tuple[str, str]]  # [(folder, photo), ...]
    profiles: list[str] | None = None  # None = all profiles

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=50, ge=1, le=500)

class ConflictResolutionRequest(BaseModel):
    mode: Literal["single", "selection", "all"]
    action: Literal["skip", "replace"]
    items: list[tuple[str, str]] | None = None

class EventSourceCreate(BaseModel):
    location: str  # URL or file path
    label: str = ""

class ScheduleResponse(BaseModel):
    title: str
    events: list[EventResponse]
    last_update: str
    source_url: str

class EventResponse(BaseModel):
    id: str
    name: str
    start: datetime
    end: datetime
    duration_seconds: float
    status: str
    type_color: str
    time_display: str
```

---

## 3. Communication Protocols

### 3.1 Frontend → Backend

```
┌──────────┐    REST (JSON)     ┌──────────┐
│ Next.js  │ ─── HTTP/1.1 ───►  │ FastAPI  │
│ (Client) │ ◄── HTTP/1.1 ────  │ (Server) │
│          │                    │          │
│          │    WebSocket       │          │
│          │ ◄── ws:// ──────►  │          │
└──────────┘                    └──────────┘
```

- **REST:** All CRUD + action-triggering operations.
- **WebSocket:** Persistent connection per active project session. Server pushes state changes; client sends subscription filters.
- **Preview images:** Served as binary responses (`image/jpeg`) with `Cache-Control: max-age=300` headers. Thumbnails generated on-demand via PIL and cached in `/data/.cache/thumbnails/`.

### 3.2 Backend → FileBrowser

```
┌──────────┐   X-Auth-User hdr   ┌──────────────┐
│ Nginx    │ ─── HTTP/1.1 ────►  │ FileBrowser  │
│ (Proxy)  │ ◄── HTTP/1.1 ─────  │ (Proxy Auth) │
└──────────┘                     └──────┬───────┘
                                        │
                                 ┌──────▼───────┐
                                 │  Shared FS   │
                                 │  Volume      │
                                 └──────────────┘
```

- FileBrowser uses **proxy authentication** (`--auth.method=proxy`).
- Nginx injects `X-Auth-User` header after JWT validation.
- No direct client → FileBrowser communication; all traffic routed through Nginx.

### 3.3 Frontend → FileBrowser (Embedded)

FileBrowser UI is loaded in the Next.js app via either:
- **Option A:** `<iframe src="/files/" />` — simplest, full isolation.
- **Option B:** Next.js `rewrites` in `next.config.js` + custom React wrapper component for tighter integration.

Recommended: **Option A** for Phase 1, migrate to Option B if deeper integration is needed.

---

## 4. Security Model

### 4.1 Authentication

```
┌────────┐  POST /api/v1/auth/login    ┌──────────┐
│ Client │ ────────────────────────►   │ FastAPI  │
│        │ ◄─ { access_token, ... } ── │          │
│        │                             │ JWT sign │
│        │  Authorization: Bearer xxx  │ (HS256)  │
│        │ ────────────────────────►   │          │
└────────┘                             └──────────┘
```

| Aspect | Implementation |
|--------|----------------|
| **Token format** | JWT (HS256), 24h expiry for access, 7d for refresh |
| **Storage** | `httpOnly` + `Secure` + `SameSite=Strict` cookies |
| **Refresh** | `POST /api/v1/auth/refresh` with refresh token cookie |
| **FileBrowser SSO** | Nginx reads JWT cookie → injects `X-Auth-User` header |
| **Password hashing** | `bcrypt` (via `passlib`) |
| **User store** | SQLite in v1 (multi-user mandatory) |

### 4.2 Authorization

| Resource | Rule |
|----------|------|
| Projects | Multi-user RBAC in v1 (Photographer, PR, Admin) |
| Source files | Read via API only; paths validated against project's `source_folder` |
| Export files | Read-only via API; write only through processing pipeline |
| FileBrowser | Scoped to project root; per-user isolation via `--scope` flag |
| Admin endpoints | Protected by admin role claim in JWT |
| Description/tag API | Editable in UI + external API (permission-guarded) |
| PR workflows | PR + Admin can manage collections/approvals/publish packs by policy |

### 4.3 CORS Configuration

```python
# FastAPI CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bid.yourdomain.com",  # Production
        "http://localhost:3000",         # Development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

### 4.4 Input Validation & Security Hardening

| Threat | Mitigation |
|--------|-----------|
| **Path traversal** | All file paths resolved and validated against project's allowed directories using `Path.resolve()` + `is_relative_to()` check |
| **Injection** | Pydantic models validate all inputs; parameterized SQLAlchemy queries only |
| **XSS** | React auto-escapes; `Content-Security-Policy` headers set by Nginx |
| **CSRF** | `SameSite=Strict` cookies + CORS origin check |
| **DoS on processing** | Rate limit: max 5 concurrent `process_photo_task` calls via semaphore |
| **File upload** | Handled by FileBrowser with server-side extension/MIME allowlist; API does not accept uploads |
| **EXIF injection** | EXIF values rendered as text-only in frontend; no `dangerouslySetInnerHTML` |
| **Symlink attacks** | `os.path.realpath()` + containment check before any file operation |

### 4.5 Transport Security

- **TLS:** Nginx terminates HTTPS (self-signed in initial deployment, configurable for Let's Encrypt).
- **Internal traffic:** HTTP between services on Docker network (not exposed).
- **Headers:** `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`.

---

## 5. FileBrowser Integration

### 5.1 Deployment Configuration

```yaml
# docker-compose.yml (FileBrowser service)
filebrowser:
  image: filebrowser/filebrowser:v2
  volumes:
    - bid_data:/srv:rw            # Mount shared volume
    - ./filebrowser.json:/config/settings.json:ro
  environment:
    - FB_NOAUTH=true              # Auth handled by proxy
  command: >
    --auth.method=proxy
    --auth.header=X-Auth-User
    --root=/srv
    --address=0.0.0.0
    --port=8080
    --baseurl=/files
  networks:
    - internal
  expose:
    - "8080"
```

### 5.2 Nginx Routing

```nginx
# FileBrowser proxy pass with auth injection
location /files/ {
    # Validate JWT from cookie
    auth_request /api/v1/auth/validate;
    auth_request_set $auth_user $upstream_http_x_auth_user;

    # Forward to FileBrowser with user identity
    proxy_pass http://filebrowser:8080/files/;
    proxy_set_header X-Auth-User $auth_user;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # WebSocket support for FileBrowser live updates
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 5.3 Scoped Access per Project

When a user opens a project, the frontend sets a cookie or query parameter identifying the active project. Nginx rewrites the FileBrowser path to scope the root:

```
User opens project "Concert_2026"
  → FileBrowser scope: /srv/source/Concert_2026/ + /srv/export/Concert_2026/
```

For multiple root directories, use FileBrowser's `--scope` flag or configure per-user rules in FileBrowser's database.

Project scoping is role-aware in v1, with one active project instance at a time:
- Photographer: own uploads by default, with explicit shared-project permissions.
- PR Team Member: read/write metadata access on assigned projects.
- Admin: full project scope and conflict-resolution controls.

### 5.4 Integration Points

| Feature | How |
|---------|-----|
| **Browse source photos** | FileBrowser scoped to project's `source_folder` (primary file-management UI) |
| **Browse exports** | FileBrowser tab/link scoped to project's `export_folder` |
| **Upload new photos** | FileBrowser upload → triggers source index refresh via webhook or filesystem watcher |
| **Download exports** | FileBrowser native download (zip support built-in) |
| **Delete files** | FileBrowser delete → integrity check detects `DELETED` state |

### 5.5 Filesystem Watcher (Optional Enhancement)

```python
# FastAPI startup event — watch for filesystem changes
from watchfiles import awatch

async def watch_source_folder(project_path: Path, ws_manager: WebSocketManager):
    """Notify frontend when new files appear in source folder."""
    source_folder = load_settings(project_path)["source_folder"]
    async for changes in awatch(source_folder):
        for change_type, path in changes:
            if change_type == Change.added:
                await ws_manager.broadcast({
                    "type": "file_added",
                    "path": str(path),
                })
```

---

## 6. Data Flow Diagrams

### 6.1 Photo Processing Pipeline

```
                        ┌─────────────────┐
                        │   Next.js UI    │
                        │ "Process All"   │
                        └────────┬────────┘
                                 │ POST /api/v1/projects/{id}/process/all
                                 ▼
                        ┌─────────────────┐
                        │   FastAPI       │
                        │   Router        │
                        └────────┬────────┘
                                 │ Enqueue to ARQ queue
                                 ▼
           ┌─────────────────────────────────────────┐
           │                ARQ Queue                 │
           │      (default concurrency=1, RAM-aware)  │
           ├────────────┬───────────┬────────────────┤
           │  Worker 1  │ Worker 2  │   Worker N     │
           │            │           │                │
           │ process_   │ process_  │  process_      │
           │ photo_task │ photo_task│  photo_task    │
           └─────┬──────┴─────┬─────┴───────┬───────┘
                 │            │             │
                 │  Result dict per photo   │
                 ▼            ▼             ▼
           ┌─────────────────────────────────────────┐
           │     WebSocket Broadcast Manager          │
           │                                          │
           │  {"type":"progress", "photo":"X", ...}  │
           └──────────────────┬──────────────────────┘
                              │ ws push
                              ▼
                     ┌─────────────────┐
                     │   Next.js UI    │
                     │ Progress bars   │
                     │ State icons     │
                     │ Toast alerts    │
                     └─────────────────┘
```

### 6.2 Source Scanning & Monitoring

```
        ┌──────────┐  POST /sources/update   ┌──────────┐
        │  Client  │ ─────────────────────►  │ FastAPI  │
        └──────────┘                          └────┬─────┘
                                                   │
                              ┌─────────────────────┤
                              │                     │
                    ┌─────────▼──────────┐  ┌──────▼──────────────┐
                    │ update_source_dict  │  │ monitor_incomplete  │
                    │ (foreground)        │  │ (background thread) │
                    │                     │  │ every 2s            │
                    │ Walks filesystem    │  │                     │
                    │ Adds new files      │  │ Checks DOWNLOADING  │
                    │ Sets NEW/DOWNLOADING│  │ files for stability │
                    └─────────┬──────────┘  └──────┬──────────────┘
                              │                     │
                              ▼                     ▼
                    ┌──────────────────────────────────────┐
                    │     SQLite source index + audit log   │
                    │   (relative paths, runtime resolution)│
                    └──────────────────┬───────────────────┘
                                       │ ws push
                                       ▼
                              ┌─────────────────┐
                              │  Client UI      │
                              │  FileBrowser +   │
                              │  state panels    │
                              │  (live updates)  │
                              └─────────────────┘
```

### 6.3 Event-Based Photo Sorting

```
   ┌──────────┐ POST /events/sources  ┌──────────────┐
   │  Client  │ ────────────────────► │ EventManager │
   └──────────┘ {"location":"https:.. │              │
                 "label":"Saturday"}   └──────┬───────┘
                                              │
                          POST /events/load   │ load_all()
                                              ▼
                                    ┌──────────────────┐
                                    │ source_loader.py │
                                    │ HTTP GET / file  │
                                    │ read JSON        │
                                    │ Parse Schedule   │
                                    └────────┬─────────┘
                                             │
                         POST /events/annotate
                                             ▼
                                    ┌──────────────────┐
                                    │   sorter.py      │
                                    │ Match photos to  │
                                    │ events by EXIF   │
                                    │ CreateDate        │
                                    │                  │
                                    │ Add event_folder │
                                    │ to source_dict   │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Export routing:   │
                                    │ export/{profile}/ │
                                    │   {event_folder}/│
                                    │     YAPA...jpg   │
                                    └──────────────────┘
```

---

## 7. Frontend Architecture

### 7.1 Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Framework** | Next.js 14+ (App Router) | SSR for initial load; API routes as BFF; image optimization |
| **Language** | TypeScript 5+ | Type safety across API boundary; matches Pydantic models |
| **State** | TanStack Query v5 | Server-state caching, auto-refetch, WebSocket integration |
| **i18n** | next-intl (EN/PL) | Day-1 multilingual UI support |
| **UI Components** | shadcn/ui + Radix | Headless, accessible, customizable; no heavy runtime |
| **Styling** | Tailwind CSS 3+ | Utility-first; fast iteration; consistent design system |
| **Search** | pgvector or Qdrant client | Semantic/vector retrieval |
| **Image viewer** | react-photo-album + lightbox | Gallery grid + fullscreen preview; replaces `PrevWindow` |
| **State panel** | Custom or @tanstack/virtual | Virtualized processing-state list; file operations delegated to FileBrowser |
| **Forms** | React Hook Form + Zod | Validation mirrors Pydantic schemas; type-safe |
| **WebSocket** | Native WebSocket + TanStack Query | Real-time updates invalidate query cache |
| **Icons** | Lucide React | Consistent icon set, tree-shakeable |

### 7.2 Page Structure

```
app/
├── (auth)/
│   ├── login/page.tsx
│   └── layout.tsx
├── (dashboard)/
│   ├── layout.tsx                    # Sidebar + top bar
│   ├── page.tsx                      # Project list (replaces ProjectSelector)
│   ├── new/page.tsx                  # Setup wizard (replaces SetupWizard)
│   └── projects/[id]/
│       ├── layout.tsx                # Project shell (settings in sidebar)
│       ├── page.tsx                  # Processing state panel + details
│       ├── processing/page.tsx       # Processing dashboard + progress
│       ├── events/page.tsx           # Event management (replaces EventsWindow)
│       ├── export-profiles/page.tsx  # Profile editor (replaces ExportWizard)
│       ├── search/page.tsx           # Semantic search
│       ├── collections/page.tsx      # PR curated collections
│       ├── approvals/page.tsx        # PR/Admin approval workflow
│       ├── publish-packs/page.tsx    # Scheduled social publish packs
│       ├── files/page.tsx            # FileBrowser iframe embed
│       ├── audit/page.tsx            # Immutable audit log viewer
│       ├── users/page.tsx            # Admin user management
│       └── settings/page.tsx         # Project settings editor
├── api/                              # BFF proxy routes (optional)
│   └── [...proxy]/route.ts
└── globals.css
```

### 7.3 Component Mapping (Legacy → Web)

| Legacy (Tkinter) | Web (React) | Notes |
|-------------------|-------------|-------|
| `MainApp` (app.py) | `layout.tsx` + React context | State management via TanStack Query |
| `ProjectSelector` | `/(dashboard)/page.tsx` | Card grid with recent projects |
| `SetupWizard` | `/(dashboard)/new/page.tsx` | Multi-step form (React Hook Form) |
| `SourceTree` | Processing state panel + FileBrowser integration | FileBrowser handles file operations; panel focuses on processing state |
| `DetailsPanel` | `<DetailsPanel />` component | EXIF table + export status badges |
| `PrevWindow` (×2) | `<ImagePreview />` component | Side-by-side source/export comparison |
| `EventsWindow` | `/projects/[id]/events/page.tsx` | Schedule timeline + source management |
| `ExportWizard` | `/projects/[id]/export-profiles/page.tsx` | Profile form with live preview |
| `Toast` | `sonner` or `shadcn/ui toast` | Bottom-right notification stack |
| Tk `after()` polling | WebSocket + TanStack Query invalidation | Real-time updates |
| `ARQ queue` status | Progress bars + status badges | Fed by WebSocket `progress` events |

---

## 8. Upgrade Path & Scalability Notes

### 8.1 Database Migration (Future)

User/auth/audit/source metadata are already database-backed in v1:

```
Phase 1 (current):  Full SQLite (users, auth, audit, source metadata)
Phase 2:            SQLite optimization (indexes, partition strategy, retention)
Phase 3:            PostgreSQL (high-scale multi-user ACID)
```

The API layer abstracts persistence — frontend code does not change.

### 8.2 Processing at Scale

```
Phase 1 (current):  ARQ queue (default worker concurrency=1, configurable)
Phase 2:            Multi-worker ARQ + Redis persistence + retry policy
Phase 3:            Kubernetes Jobs (auto-scaling, cloud-native)
```

### 8.3 Caching Layers

| Cache | Technology | What |
|-------|-----------|------|
| **Thumbnail** | Filesystem (`/data/.cache/thumbs/`) | Pre-generated previews |
| **API response** | TanStack Query (client-side) | source index, settings |
| **Static assets** | Nginx `proxy_cache` | Next.js pages, JS bundles |
| **EXIF data** | SQLite + optional memory cache | Persisted and queryable metadata |

---

## 9. Deployment Options

### 9.1 Docker Compose (Recommended for v1)

```yaml
version: "3.9"
services:
  nginx:
    image: nginx:alpine
    ports: ["443:443", "80:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on: [frontend, backend, filebrowser]

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=/api/v1
      - NEXT_PUBLIC_WS_URL=ws://localhost/api/v1
    expose: ["3000"]

  backend:
    build: ./backend
    volumes:
      - bid_data:/data
    environment:
      - BID_DATA_DIR=/data
      - JWT_SECRET=${JWT_SECRET}
      - VECTOR_INDEX_URL=http://vector:6333
    expose: ["8000"]

  vector:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    expose: ["6333"]

  filebrowser:
    image: filebrowser/filebrowser:v2
    volumes:
      - bid_data:/srv
    command: --auth.method=proxy --auth.header=X-Auth-User --baseurl=/files
    expose: ["8080"]

volumes:
  bid_data:
    driver: local
  qdrant_data:
    driver: local
```

### 9.2 Bare Metal (Alternative)

For NAS or local workstation deployment without Docker:

1. Python 3.10+ with `uvicorn` serving FastAPI on port 8000
2. Node.js 20+ with `next start` on port 3000
3. FileBrowser binary on port 8080
4. Caddy as reverse proxy (automatic HTTPS)

---

## 10. Delivery Governance

AI agents working from this architecture must post progress to the exact issue IDs defined in `migration_to_web_plan/github_milestones_and_issues_plan.md`.

- Every workstream maps to one epic ID (`E1`..`E12`) and one child issue ID (`P*`, `POC-*`, `AUD-*`, `REL-*`, `G*`).
- Each progress update includes milestone ID (`M1`..`M13`), status, and completion percentage.
- Cross-cutting work must list related issue IDs to keep milestone traceability explicit.
- Freeze-sensitive blockers must reference relevant gate issue (`G1`, `G2`, or `G3`).

---

## 11. Error Handling Strategy

### 11.1 Exception → HTTP Status Mapping

| Exception (bid/errors.py) | HTTP Status | Response Body |
|---------------------------|-------------|---------------|
| `ConfigError` | `422 Unprocessable Entity` | `{"detail": "...", "field": "..."}` |
| `ImageProcessingError` | `500 Internal Server Error` | `{"detail": "...", "photo": "..."}` |
| `SourceManagerError` | `500 Internal Server Error` | `{"detail": "..."}` |
| `ProjectError` | `404 Not Found` or `409 Conflict` | `{"detail": "..."}` |
| `ValidationError` (Pydantic) | `422 Unprocessable Entity` | Auto-generated by FastAPI |
| `FileNotFoundError` | `404 Not Found` | `{"detail": "File not found"}` |
| `PermissionError` | `403 Forbidden` | `{"detail": "Access denied"}` |

### 11.2 WebSocket Error Handling

- Connection drops: Client auto-reconnects with exponential backoff (1s, 2s, 4s, max 30s).
- Server errors during processing: Sent as `{"type": "error"}` messages, never crash the WebSocket.
- Stale connections: Server pings every 30s; closes idle connections after 5 minutes.
