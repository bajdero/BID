# BID Web Migration — Implementation Plan

> **Version:** 1.0  
> **Date:** 2026-03-20  
> **Prerequisites:** Python 3.10+, Node.js 20+, Docker (optional)  

---

## Roadmap Overview

```
Phase 1 ──► Phase 2 ──► Phase 5 ──► Phase 8
  │           │                        ▲
  │           │     Phase 6 ───────────┤
  │           │                        │
  └──► Phase 3 ──► Phase 4 ──► Phase 7 ┘
```

| Phase | Name | Depends On | Estimated Effort |
|-------|------|-----------|-----------------|
| **1** | Backend API Extraction | — | High |
| **2** | WebSocket Real-Time Layer | Phase 1 | Medium |
| **3** | Next.js Frontend Shell | — (parallel with 2) | Medium |
| **4** | Core UI Components | Phase 3 | High |
| **5** | Processing Dashboard | Phases 2 + 4 | Medium |
| **6** | FileBrowser Integration | Phase 3 | Low |
| **7** | Event System UI | Phase 4 | Medium |
| **8** | Testing & Deployment | All phases | Medium |

---

## Phase 1: Backend API Extraction

### Objective
Wrap the existing `bid/` Python package in a FastAPI service layer. Zero changes to business logic — only add an HTTP interface on top.

### Tasks

1. **Scaffold FastAPI project structure**
   ```
   backend/
   ├── api/
   │   ├── __init__.py
   │   ├── main.py            # FastAPI app factory
   │   ├── deps.py            # Dependency injection (project path, settings)
   │   ├── auth.py            # JWT auth utilities
   │   ├── models/
   │   │   ├── __init__.py
   │   │   ├── project.py     # Pydantic: ProjectSettings, ProjectDetails
   │   │   ├── source.py      # Pydantic: PhotoEntry, SourceTree
   │   │   ├── processing.py  # Pydantic: ProcessRequest, ProcessStatus
   │   │   ├── events.py      # Pydantic: EventSource, Schedule, Event
   │   │   └── auth.py        # Pydantic: LoginRequest, TokenResponse
   │   └── routers/
   │       ├── __init__.py
   │       ├── projects.py    # /api/v1/projects/*
   │       ├── sources.py     # /api/v1/projects/{id}/sources/*
   │       ├── processing.py  # /api/v1/projects/{id}/process/*
   │       ├── events.py      # /api/v1/projects/{id}/events/*
   │       └── auth.py        # /api/v1/auth/*
   └── requirements.txt       # fastapi, uvicorn, pydantic, python-jose, passlib
   ```

2. **Create Pydantic models** from existing JSON schemas (settings.json, export_option.json, source_dict entries, Event/Schedule dataclasses).

3. **Implement routers** — each router imports directly from `bid.*` modules and calls existing functions.

4. **Add dependency injection** — `get_project_path(id)` dependency resolves project ID to filesystem path using `ProjectManager`.

5. **Add JWT authentication** — login endpoint, token validation middleware, user store (JSON file).

6. **Add CORS middleware** — allow frontend origin.

7. **Write API integration tests** — reuse existing test fixtures from `tests/conftest.py`.

### AI-Ready Prompt — Phase 1

```
You are building a FastAPI backend for the BID (Batch Image Delivery) application.
The existing business logic lives in the `bid/` Python package and must NOT be modified.
Your job is to create an HTTP API layer that wraps these existing modules.

PROJECT STRUCTURE:
- Create a `backend/api/` package alongside the existing `bid/` package
- The FastAPI app should be importable as `api.main:app`
- Use `uvicorn` as the ASGI server

EXISTING MODULES TO WRAP (do NOT modify these files):

1. `bid/project_manager.py` — ProjectManager class with classmethods:
   - `get_recent_projects() -> list[str]`
   - `add_recent_project(project_path: str) -> None`
   - `create_project(name: str, source_folder: str, export_folder: str, export_settings: dict) -> Path`
   - `get_last_project() -> str | None`
   - `get_project_details(project_path: str) -> dict` returns {path, name, last_modified, photo_count}
   - `prune_recent_projects() -> None`
   Projects are stored in: `projects/{name}/` with settings.json, export_option.json, source_dict.json

2. `bid/config.py` — Functions:
   - `load_settings(path: Path | None = None) -> dict` returns {"source_folder": str, "export_folder": str}
   - `load_export_options(path: Path | None = None) -> dict` returns {profile_name: {size_type, size, format, quality, ratio, logo, logo_required}}
   - Constant: `PROJECT_DIR: Path` = workspace root

3. `bid/source_manager.py` — Functions:
   - `create_source_dict(source_folder, export_folder, export_settings) -> dict`
     Returns {folder_name: {file_name: {path, state, exported, size, size_bytes, created, mtime, exif}}}
   - `update_source_dict(source_dict, source_folder, export_folder, export_settings) -> tuple[dict, bool]`
   - `check_integrity(source_dict, export_settings, export_folder) -> dict`
   - `monitor_incomplete_files(source_dict, max_checks, check_interval) -> dict`
   - `save_source_dict(source_dict, project_dir) -> None`
   - `load_source_dict(project_dir) -> dict | None`
   - States: "downloading", "new", "processing", "ok", "ok_old", "error", "export_fail", "deleted", "skip"

4. `bid/image_processing.py` — Functions:
   - `process_photo_task(photo_path, folder_name, photo_name, created_date, export_folder, export_settings, existing_exports, event_folder=None) -> dict`
     Returns {success: bool, exported: {profile: path}, duration: float, error_msg: str|None}
   - `get_all_exif(img) -> dict[str, str]`

5. `bid/events/manager.py` — EventManager class:
   - `__init__(project_dir, tz_offset_hours=1.0, local_tz_name="Europe/Warsaw")`
   - `add_source(location, label, source_type) -> EventSource`
   - `remove_source(location) -> bool`
   - `list_sources() -> list[dict]`
   - `load_all(timeout=15.0) -> list[Schedule]`
   - `annotate(source_dict) -> dict[str, str]`
   - `schedules` attribute: list[Schedule]
   - `folder_map` attribute: dict[str, str]

6. `bid/validators.py` — Functions:
   - `validate_export_profile(name, profile) -> list[str]` (returns error messages)
   - `validate_path_exists(path, label) -> str | None`
   - `validate_source_export_different(source, export) -> str | None`

7. `bid/errors.py` — Exception hierarchy:
   - YapaError (base) -> ConfigError, ImageProcessingError, SourceManagerError, ProjectError

REQUIREMENTS:

1. Create Pydantic v2 models for all data structures listed above.
   Use `model_config = ConfigDict(from_attributes=True)` where needed.

2. Create FastAPI routers:
   - `routers/projects.py`: CRUD for projects
     GET /api/v1/projects — list recent projects (call get_recent_projects + get_project_details for each)
     POST /api/v1/projects — create project (body: {name, source_folder, export_folder, export_settings})
     GET /api/v1/projects/{project_name} — get details
     DELETE /api/v1/projects/{project_name} — delete project folder
     GET /api/v1/projects/{project_name}/settings — load settings.json
     PUT /api/v1/projects/{project_name}/settings — save settings.json
     GET /api/v1/projects/{project_name}/export-profiles — load export_option.json
     PUT /api/v1/projects/{project_name}/export-profiles — save export_option.json

   - `routers/sources.py`:
     GET /api/v1/projects/{project_name}/sources — load_source_dict
     POST /api/v1/projects/{project_name}/sources/scan — create_source_dict (full scan)
     POST /api/v1/projects/{project_name}/sources/update — update_source_dict (incremental)
     POST /api/v1/projects/{project_name}/sources/integrity — check_integrity
     GET /api/v1/projects/{project_name}/sources/{folder}/{photo}/preview — generate thumbnail
       Use PIL to open the photo, resize to max 800px, return as JPEG response

   - `routers/processing.py`:
     POST /api/v1/projects/{project_name}/process — process specific photos
       Body: {photos: [[folder, photo], ...], profiles: [str] | null}
       Submit each to ThreadPoolExecutor (max_workers=3)
       Return 202 Accepted with job ID
     GET /api/v1/projects/{project_name}/process/status — current queue length + active jobs

   - `routers/events.py`:
     Full CRUD wrapping EventManager methods

   - `routers/auth.py`:
     POST /api/v1/auth/login — validate credentials, return JWT
     POST /api/v1/auth/refresh — refresh token
     GET /api/v1/auth/validate — validate token (for Nginx auth_request)

3. Create `deps.py` with dependency injection:
   - `get_project_path(project_name: str) -> Path` — resolves to projects/{name}/, raises 404 if missing
   - `get_current_user(token: str = Depends(oauth2_scheme)) -> dict` — JWT validation

4. Create `main.py` with:
   - FastAPI app with lifespan (startup: create ThreadPoolExecutor; shutdown: cleanup)
   - CORS middleware (allow localhost:3000)
   - Exception handlers mapping YapaError subclasses to HTTP status codes
   - Include all routers

5. Path security: ALL file operations must validate that resolved paths are within
   the project's configured source_folder or export_folder. Use:
   ```python
   resolved = Path(path).resolve()
   if not resolved.is_relative_to(allowed_root):
       raise HTTPException(403, "Access denied: path outside allowed directory")
   ```

6. requirements.txt: fastapi>=0.110, uvicorn[standard], pydantic>=2.0,
   python-jose[cryptography], passlib[bcrypt], python-multipart

Generate ALL files with complete, working code. Do not use placeholders or TODOs.
The API must work with the existing bid/ package without any modifications to it.
```

---

## Phase 2: WebSocket Real-Time Layer

### Objective
Add WebSocket support to FastAPI for real-time state updates, replacing Tkinter's `after()` polling pattern.

### Tasks

1. **Create WebSocket manager** — connection registry, room-based broadcasting (per project).
2. **Integrate with processing pipeline** — after each `process_photo_task` completes, broadcast result.
3. **Integrate with source monitoring** — background thread runs `monitor_incomplete_files()`, broadcasts state transitions.
4. **Integrate with source scanning** — `update_source_dict()` results broadcast as scan updates.
5. **Add heartbeat** — server pings every 30s, client reconnects on disconnect.

### AI-Ready Prompt — Phase 2

```
You are adding WebSocket real-time support to the BID FastAPI backend created in Phase 1.

EXISTING CODE:
- FastAPI app in `backend/api/main.py`
- Routers in `backend/api/routers/`
- ThreadPoolExecutor for photo processing

CURRENT POLLING PATTERN (from legacy Tkinter app, in bid/app.py):
The legacy app used three queue.Queue objects polled via Tk after():
1. `_update_queue` — receives (source_dict, found_new) from source scan thread
2. `_monitor_queue` — receives {folder: {photo: ready}} from file monitor thread
3. `_event_queue` — receives reloaded schedules from event refresh thread
Processing results were tracked via Future objects checked by check_futures().

YOUR TASK: Replace this polling pattern with WebSocket push.

CREATE:

1. `backend/api/ws_manager.py`:
   ```python
   class ConnectionManager:
       """Manages WebSocket connections grouped by project."""
       
       async def connect(self, websocket: WebSocket, project_name: str) -> None
       def disconnect(self, websocket: WebSocket, project_name: str) -> None
       async def broadcast(self, project_name: str, message: dict) -> None
       async def send_personal(self, websocket: WebSocket, message: dict) -> None
   ```

2. Add WebSocket route to `routers/sources.py` or a new `routers/ws.py`:
   ```
   ws:///api/v1/projects/{project_name}/ws
   ```
   - Authenticate via query parameter token: `?token=xxx`
   - Keep connection alive with 30s ping/pong
   - Accept subscription messages: {"type": "subscribe", "folders": [...]}

3. Modify `routers/processing.py`:
   - When a photo task completes (from ThreadPoolExecutor), broadcast:
     {"type": "progress", "folder": "...", "photo": "...", "profile": "...",
      "status": "completed", "duration_sec": 2.3, "exported_path": "..."}
   - When a task fails:
     {"type": "error", "folder": "...", "photo": "...", "message": "..."}
   - When processing starts:
     {"type": "state_change", "folder": "...", "photo": "...",
      "old_state": "new", "new_state": "processing"}

4. Create background task for file monitoring:
   - On FastAPI startup, launch a background async task
   - Every 2 seconds, call `monitor_incomplete_files(source_dict)`
   - For each file that becomes ready, broadcast:
     {"type": "monitor_update", "folder": "...", "photo": "...", "ready": true}
   - Also update source_dict state from "downloading" to "new"

5. Create background task for periodic source scanning (optional, configurable):
   - Every 60 seconds, call `update_source_dict()`
   - If found_new is True, broadcast:
     {"type": "scan_update", "found_new": true, "new_count": 12,
      "updated_folders": ["Session1", "Session2"]}

MESSAGE PROTOCOL (all JSON):
- Server → Client messages always have a "type" field
- Types: "state_change", "progress", "scan_update", "monitor_update", "error", "pong"
- Client → Server types: "subscribe", "ping"

REQUIREMENTS:
- Use `asyncio.create_task()` for background loops (not threading for the WS part)
- The ThreadPoolExecutor for image processing should use `loop.run_in_executor()`
  to bridge sync processing with async WebSocket broadcasting
- Handle disconnections gracefully (remove from ConnectionManager)
- Log all WebSocket connections/disconnections
- If no clients are connected to a project, skip broadcasting (save resources)

Generate complete, working code for all files.
```

---

## Phase 3: Next.js Frontend Shell

### Objective
Scaffold the Next.js 14 application with App Router, authentication flow, layout, and project selection page.

### Tasks

1. **Initialize Next.js project** with TypeScript, Tailwind CSS, shadcn/ui.
2. **Set up authentication** — login page, JWT cookie management, protected routes via middleware.
3. **Create shared layout** — sidebar navigation, top bar with user info.
4. **Build project list page** — card grid showing recent projects with metadata.
5. **Build setup wizard** — multi-step form for new project creation.
6. **Configure API client** — typed fetch wrapper with auth header injection.

### AI-Ready Prompt — Phase 3

```
You are building the Next.js 14 frontend shell for the BID (Batch Image Delivery)
web application. This is the initial scaffold — no business logic UI yet.

TECH STACK:
- Next.js 14+ with App Router (app/ directory)
- TypeScript 5+
- Tailwind CSS 3+
- shadcn/ui components (use `npx shadcn-ui@latest add` for components)
- TanStack Query v5 for server state
- React Hook Form + Zod for forms
- Lucide React for icons

PROJECT CONTEXT:
BID is a professional photo processing tool. Users create "projects" that define:
- A source folder (containing photographer subfolders with photos)
- An export folder (where processed images are saved)
- Export profiles (size, format, quality, watermark settings)

The backend API is at `/api/v1/` (proxied by Next.js rewrites or Nginx).

CREATE THE FOLLOWING:

1. `frontend/` directory with `npx create-next-app@latest` structure

2. `next.config.js`:
   - Rewrites: `/api/v1/:path*` → `http://localhost:8000/api/v1/:path*`
   - Rewrites: `/files/:path*` → `http://localhost:8080/files/:path*`
   - Image domains: localhost

3. `lib/api-client.ts`:
   - Typed fetch wrapper that reads JWT from cookie
   - Functions for each API endpoint group:
     ```typescript
     // Projects
     getProjects(): Promise<Project[]>
     createProject(data: CreateProjectRequest): Promise<Project>
     getProjectDetails(name: string): Promise<ProjectDetails>
     deleteProject(name: string): Promise<void>
     getProjectSettings(name: string): Promise<ProjectSettings>
     updateProjectSettings(name: string, settings: ProjectSettings): Promise<void>
     getExportProfiles(name: string): Promise<Record<string, ExportProfile>>
     updateExportProfiles(name: string, profiles: Record<string, ExportProfile>): Promise<void>
     
     // Sources
     getSourceDict(name: string): Promise<SourceDict>
     triggerScan(name: string): Promise<void>
     triggerUpdate(name: string): Promise<SourceUpdateResult>
     checkIntegrity(name: string): Promise<IntegrityResult>
     getPhotoPreview(name: string, folder: string, photo: string): string // URL
     
     // Processing
     processPhotos(name: string, request: ProcessRequest): Promise<{job_id: string}>
     getProcessingStatus(name: string): Promise<ProcessingStatus>
     
     // Events
     getEventSources(name: string): Promise<EventSource[]>
     addEventSource(name: string, data: AddEventSourceRequest): Promise<EventSource>
     removeEventSource(name: string, location: string): Promise<void>
     loadEvents(name: string): Promise<Schedule[]>
     annotateEvents(name: string): Promise<Record<string, string>>
     ```

4. `lib/types.ts`:
   TypeScript interfaces matching the Pydantic models:
   ```typescript
   interface Project {
     path: string;
     name: string;
     last_modified: string;
     photo_count: number;
   }
   
   interface ProjectSettings {
     source_folder: string;
     export_folder: string;
   }
   
   interface ExportProfile {
     size_type: "longer" | "width" | "height" | "shorter";
     size: number;
     format: "JPEG" | "PNG";
     quality: number;
     ratio: number[] | null;
     logo: Record<string, LogoSettings> | null;
     logo_required: boolean;
   }
   
   interface LogoSettings {
     size: number;
     opacity: number;
     x_offset: number;
     y_offset: number;
   }
   
   interface PhotoEntry {
     path: string;
     state: "downloading" | "new" | "processing" | "ok" | "ok_old" | "error" | "export_fail" | "deleted" | "skip";
     exported: Record<string, string>;
     size: string;
     size_bytes: number;
     created: string;
     mtime: number;
     exif: Record<string, string>;
     error_msg: string | null;
     duration_sec: number | null;
     event_folder: string | null;
     event_id: string | null;
     event_name: string | null;
   }
   
   type SourceDict = Record<string, Record<string, PhotoEntry>>;
   // ... etc
   ```

5. `lib/ws.ts`:
   WebSocket hook for real-time updates:
   ```typescript
   function useProjectWebSocket(projectName: string) {
     // Connect to ws:///api/v1/projects/{name}/ws
     // Auto-reconnect with exponential backoff
     // Parse incoming JSON messages
     // Invalidate TanStack Query cache based on message type:
     //   "state_change" / "progress" → invalidate sources query
     //   "scan_update" → invalidate sources query
     //   "monitor_update" → invalidate sources query
     //   "error" → show toast notification
     // Return: { isConnected, lastMessage }
   }
   ```

6. `app/layout.tsx`:
   - TanStack QueryClientProvider
   - Toaster component (sonner or shadcn toast)

7. `app/(auth)/login/page.tsx`:
   - Email/password form
   - POST to /api/v1/auth/login
   - Store JWT in httpOnly cookie (via API response Set-Cookie)
   - Redirect to dashboard on success

8. `middleware.ts`:
   - Check for auth cookie on all routes except /login
   - Redirect to /login if not authenticated

9. `app/(dashboard)/layout.tsx`:
   - Sidebar with navigation:
     - Projects (home icon)
     - New Project (plus icon)
   - Top bar: app name "BID", user avatar, logout button
   - Main content area (children)

10. `app/(dashboard)/page.tsx` — Project List:
    - Use TanStack Query to fetch projects
    - Display as card grid (shadcn Card component)
    - Each card shows: project name, photo count, last modified date
    - Click → navigate to /projects/[name]
    - "New Project" card/button → navigate to /new

11. `app/(dashboard)/new/page.tsx` — Setup Wizard:
    Multi-step form (3 steps) using React Hook Form + Zod:
    Step 1: Project name (text input, validated: no special chars)
    Step 2: Source folder path + Export folder path (text inputs)
            Validate: both paths are different (call validate endpoint)
    Step 3: Initial export profile (or skip to use defaults)
    On submit: POST /api/v1/projects → redirect to /projects/[name]

12. `app/(dashboard)/projects/[id]/layout.tsx` — Project Shell:
    - Secondary sidebar or tab bar:
      - Sources (folder icon)
      - Processing (play icon)
      - Events (calendar icon)
      - Export Profiles (settings icon)
      - Files (hard-drive icon) — FileBrowser
      - Settings (gear icon)
    - Initialize WebSocket connection (useProjectWebSocket)
    - Show connection status indicator

13. `app/(dashboard)/projects/[id]/page.tsx`:
    - Placeholder: "Select a tab to get started" or redirect to sources

STYLING REQUIREMENTS:
- Dark mode by default (dark background, light text)
- Use Inter font
- Responsive: works on 1024px+ screens (desktop-first, this is a professional tool)
- Color accents: Use blue-500 for primary actions
- State colors: green for OK, yellow for processing, red for error, gray for downloading

Generate ALL files with complete, working code.
Install shadcn/ui components needed: card, button, input, label, form,
  dropdown-menu, avatar, separator, toast, badge, tabs, dialog.
```

---

## Phase 4: Core UI Components

### Objective
Build the main application components: source tree, details panel, and image preview.

### Tasks

1. **Source tree component** — virtualized file tree with state icons and multi-select.
2. **Details panel** — EXIF metadata display, export status, file info.
3. **Image preview** — source photo preview with zoom, side-by-side export comparison.
4. **Source page integration** — combine tree + details + preview in project source page.

### AI-Ready Prompt — Phase 4

```
You are building the core UI components for the BID web application.
The Next.js shell from Phase 3 is already set up with TanStack Query, shadcn/ui,
and TypeScript types. The backend API is available at /api/v1/.

CONTEXT — What these components replace:
The legacy Tkinter app had:
- SourceTree: A ttk.Treeview widget showing folders and photos with colored state indicators
- DetailsPanel: A panel showing EXIF data, file size, dimensions, export status per profile
- PrevWindow: Two separate Tk Toplevel windows for source and export image preview

BUILD THESE COMPONENTS:

1. `components/source-tree.tsx` — File Tree with State:
   PROPS:
   ```typescript
   interface SourceTreeProps {
     sourceDict: SourceDict;  // {folder: {photo: PhotoEntry}}
     selectedPhotos: Set<string>;  // "folder/photo" keys
     onSelectionChange: (selected: Set<string>) => void;
     onPhotoClick: (folder: string, photo: string) => void;
   }
   ```
   
   FEATURES:
   - Render as collapsible folder tree (similar to VS Code file explorer)
   - Each folder is expandable/collapsible
   - Each photo shows: filename, state icon, file size
   - State icons (use colored dots or badges):
     - "ok" / "ok_old" → green circle
     - "new" → blue circle
     - "processing" → yellow spinning indicator
     - "error" / "export_fail" → red triangle
     - "downloading" → gray down-arrow
     - "deleted" → strikethrough text
     - "skip" → gray dash
   - Multi-select: Shift+click for range, Ctrl+click for toggle
   - Folder header shows: folder name + count badge (e.g., "Session1 (24)")
   - Virtualize with @tanstack/react-virtual for large lists (1000+ photos)
   - Right-click context menu: "Process selected", "Mark as skip", "Reset to new"
   
   KEYBOARD:
   - Arrow up/down: navigate
   - Space: toggle selection
   - Enter: open preview
   - Ctrl+A: select all in current folder

2. `components/details-panel.tsx` — Photo Details:
   PROPS:
   ```typescript
   interface DetailsPanelProps {
     photo: PhotoEntry | null;
     folder: string;
     projectName: string;
     exportProfiles: Record<string, ExportProfile>;
   }
   ```
   
   SECTIONS (when a photo is selected):
   a) File Info:
      - Filename (bold)
      - Path (truncated, hover for full)
      - Size (e.g., "33.97 MB")
      - State badge (colored)
      - Created date
   
   b) Image Info (from EXIF):
      - Dimensions: WxH px
      - Camera: Make + Model
      - Lens: LensModel
      - Settings: FocalLength, FNumber, ISO, ExposureTime
      - Orientation
   
   c) Export Status:
      - For each profile in exportProfiles:
        - Profile name
        - Status: "Exported" (green) with path, or "Pending" (gray), or "Error" (red)
        - If exported: show output dimensions and file size
   
   d) Event Assignment (if event_folder is set):
      - Event name
      - Event folder
   
   When no photo is selected: show "Select a photo to view details"

3. `components/image-preview.tsx` — Photo Preview:
   PROPS:
   ```typescript
   interface ImagePreviewProps {
     projectName: string;
     folder: string;
     photo: string;
     photoEntry: PhotoEntry;
     exportProfiles: Record<string, ExportProfile>;
   }
   ```
   
   FEATURES:
   - Main preview area showing source photo (loaded from API)
   - Use: GET /api/v1/projects/{name}/sources/{folder}/{photo}/preview
   - Zoom: scroll wheel or pinch
   - Tabs or toggle to switch between:
     - Source image (original)
     - Each export profile result (if exported)
   - Side-by-side mode: source on left, selected export on right
   - Loading spinner while image loads
   - Error state if image fails to load
   - Keyboard: Left/Right arrows to navigate to prev/next photo in folder

4. `app/(dashboard)/projects/[id]/page.tsx` — Sources Page:
   LAYOUT (3-column):
   ```
   ┌──────────────┬──────────────────────┬───────────────────┐
   │  Source Tree  │   Image Preview      │  Details Panel    │
   │  (300px)      │   (flexible)         │  (350px)          │
   │              │                      │                   │
   │  [folders]   │  [photo preview]     │  File Info        │
   │  [photos]    │                      │  EXIF Data        │
   │              │                      │  Export Status    │
   │              │                      │  Event Info       │
   └──────────────┴──────────────────────┴───────────────────┘
   ```
   
   - Resizable panels (use a splitter/drag handle)
   - Source tree on left
   - Preview in center (fills available space)
   - Details panel on right
   - Top toolbar: "Scan" button, "Update" button, "Process Selected" button
   - Use TanStack Query for data fetching:
     - `useQuery(['sources', projectName], () => getSourceDict(projectName))`
     - `useQuery(['profiles', projectName], () => getExportProfiles(projectName))`
   - WebSocket updates automatically invalidate queries

5. `components/toolbar.tsx` — Action Toolbar:
   - Scan Sources (refresh icon) → POST /sources/scan
   - Update Sources (sync icon) → POST /sources/update
   - Process Selected (play icon) → POST /process
   - Check Integrity (shield icon) → POST /sources/integrity
   - Each button shows loading state while request is in flight
   - Disabled states: "Process Selected" disabled when no selection

Use shadcn/ui components: Badge, Button, ScrollArea, Tabs, Tooltip,
  ContextMenu, Separator, ResizablePanel (or build simple splitter).
Use Lucide icons: Folder, FileImage, Circle, AlertTriangle, Download,
  ChevronRight, ChevronDown, Play, RefreshCw, Shield, Settings.

Generate complete, working code for all components and the page.
```

---

## Phase 5: Processing Dashboard

### Objective
Build the processing control panel with real-time progress tracking via WebSocket.

### Tasks

1. **Processing page** — trigger batch processing, view progress.
2. **Progress tracking** — real-time progress bars fed by WebSocket events.
3. **Export profile editor** — CRUD for export profiles with validation.
4. **Toast notifications** — error/success alerts for processing events.

### AI-Ready Prompt — Phase 5

```
You are building the processing dashboard for the BID web application.
Phase 4 components (source tree, details, preview) are already built.
The WebSocket is connected and delivers real-time processing updates.

CONTEXT:
When the user clicks "Process", the backend:
1. For each selected photo × each export profile, runs `process_photo_task()`
2. Each task: loads image → reads EXIF → resizes → converts to sRGB → applies watermark → saves
3. Takes 1-5 seconds per photo per profile
4. Results stream via WebSocket as {"type": "progress", ...} messages

BUILD:

1. `app/(dashboard)/projects/[id]/processing/page.tsx` — Processing Dashboard:
   
   LAYOUT:
   ```
   ┌─────────────────────────────────────────────────────┐
   │  PROCESSING DASHBOARD                               │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │  [Process All NEW]  [Process Selected]  [Stop]      │
   │                                                     │
   │  Overall Progress   ████████████░░░░░░░  67% (45/67)│
   │                                                     │
   │  ┌─────────────────────────────────────────────┐    │
   │  │ Active Jobs                                 │    │
   │  │                                             │    │
   │  │ Session1/IMG_001.tif  [fb ██████ 100%]     │    │
   │  │                       [insta ███░░░ 60%]   │    │
   │  │                                             │    │
   │  │ Session1/IMG_002.tif  [fb ░░░░░░ queued]   │    │
   │  └─────────────────────────────────────────────┘    │
   │                                                     │
   │  ┌─────────────────────────────────────────────┐    │
   │  │ Recent Results                              │    │
   │  │                                             │    │
   │  │ ✓ Session1/IMG_000.tif  2.3s  4 profiles   │    │
   │  │ ✗ Session2/IMG_005.tif  "EXIF read error"  │    │
   │  └─────────────────────────────────────────────┘    │
   └─────────────────────────────────────────────────────┘
   ```
   
   - "Process All NEW": POST /process/all — processes all photos with state "new"
   - "Process Selected": Takes selection from source tree (shared state via URL params or context)
   - "Stop": Cancels queued (not in-progress) tasks
   - Overall progress bar: total processed / total queued
   - Active jobs list: shows currently processing photos with per-profile progress
   - Recent results: scrollable list of completed/failed tasks
   - All updates come from WebSocket — NO polling
   
   WebSocket message handling:
   ```typescript
   // On "state_change" (new → processing):
   //   Add to active jobs list
   // On "progress" (profile completed):
   //   Update active job's profile progress
   //   If all profiles done, move to recent results
   // On "error":
   //   Show in recent results with red styling
   //   Show toast notification
   ```

2. `app/(dashboard)/projects/[id]/export-profiles/page.tsx` — Profile Editor:
   
   - List all export profiles as cards
   - Each card shows: profile name, size, format, quality, watermark settings
   - Edit button → opens dialog/drawer with form:
     - Size type: dropdown (longer, width, height, shorter)
     - Size: number input (100-10000)
     - Format: radio (JPEG, PNG)
     - Quality: slider (1-100 for JPEG, 1-9 for PNG)
     - Aspect ratio filter: optional [min, max] inputs
     - Watermark settings per orientation (landscape/portrait):
       - Size, Opacity, X offset, Y offset
     - Logo required: checkbox
   - Validate using POST /export-profiles/validate before saving
   - "Add Profile" button at the top
   - "Delete Profile" with confirmation dialog
   - Save: PUT /export-profiles with full profiles dict

3. `components/toast-handler.tsx`:
   - Listen to WebSocket "error" messages
   - Show toast: red background, photo name, error message, auto-dismiss 10s
   - Listen to WebSocket "scan_update"
   - Show toast: blue, "Found 12 new photos in 3 folders", auto-dismiss 5s
   - Use sonner or shadcn/ui toast

4. `hooks/use-processing-state.ts`:
   Custom hook that maintains processing state from WebSocket:
   ```typescript
   interface ProcessingState {
     activeJobs: Map<string, ActiveJob>;  // key: "folder/photo"
     recentResults: ProcessingResult[];   // last 50
     totalQueued: number;
     totalCompleted: number;
     totalFailed: number;
     isProcessing: boolean;
   }
   
   function useProcessingState(projectName: string): ProcessingState
   ```

Generate complete, working code for all files.
```

---

## Phase 6: FileBrowser Integration

### Objective
Embed FileBrowser into the BID web application with shared authentication.

### Tasks

1. **Docker service** — add FileBrowser to docker-compose.yml.
2. **Nginx config** — proxy rules with auth injection.
3. **Frontend embed** — iframe integration in project files page.
4. **Auth bridge** — pass BID JWT to FileBrowser via proxy header.

### AI-Ready Prompt — Phase 6

```
You are integrating FileBrowser (https://filebrowser.org) into the BID web application.
The Next.js frontend and FastAPI backend are already running.

REQUIREMENTS:
- FileBrowser must use proxy authentication (no its own login page)
- The user authenticates via BID's login page; FileBrowser trusts the proxy
- FileBrowser is scoped to the project's source and export folders
- FileBrowser is embedded within the BID UI (not a separate tab)

CREATE:

1. `docker/docker-compose.yml` — Add FileBrowser service:
   - Image: filebrowser/filebrowser:v2-alpine
   - Mount shared data volume at /srv
   - Configure proxy auth via command flags:
     --auth.method=proxy --auth.header=X-Auth-User
   - Set --baseurl=/files
   - Network: internal only (not exposed to host)

2. `docker/nginx.conf` — Complete Nginx configuration:
   ```nginx
   upstream frontend { server frontend:3000; }
   upstream backend { server backend:8000; }
   upstream filebrowser { server filebrowser:8080; }
   
   server {
       listen 80;
       
       # Frontend (Next.js)
       location / {
           proxy_pass http://frontend;
       }
       
       # Backend API
       location /api/ {
           proxy_pass http://backend;
           # WebSocket support
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
       
       # FileBrowser — auth validated by backend
       location /files/ {
           # Sub-request to validate JWT
           auth_request /api/v1/auth/validate;
           auth_request_set $auth_user $upstream_http_x_auth_user;
           
           proxy_pass http://filebrowser/files/;
           proxy_set_header X-Auth-User $auth_user;
       }
   }
   ```

3. `app/(dashboard)/projects/[id]/files/page.tsx` — FileBrowser Page:
   ```typescript
   // Embed FileBrowser in an iframe
   // Pass project context so FileBrowser opens in the right directory
   // Add toolbar above iframe: "Source Folder" tab, "Export Folder" tab
   // The iframe src changes based on selected tab:
   //   Source: /files/source/{project_source_folder}/
   //   Export: /files/export/{project_export_folder}/
   ```

4. `backend/api/routers/auth.py` — Add validate endpoint:
   ```python
   @router.get("/validate")
   async def validate_token(current_user = Depends(get_current_user)):
       """Endpoint for Nginx auth_request subrequest.
       Returns 200 + X-Auth-User header if token is valid.
       Returns 401 if token is invalid."""
       response = Response(status_code=200)
       response.headers["X-Auth-User"] = current_user["username"]
       return response
   ```

5. `docker/filebrowser.json` — FileBrowser configuration:
   ```json
   {
     "port": 8080,
     "baseURL": "/files",
     "address": "0.0.0.0",
     "log": "stdout",
     "root": "/srv",
     "auth": {
       "method": "proxy",
       "header": "X-Auth-User"
     },
     "branding": {
       "name": "BID Files",
       "disableExternal": true
     }
   }
   ```

Generate complete, working configurations and code.
```

---

## Phase 7: Event System UI

### Objective
Build the event management interface for photo-to-event sorting.

### Tasks

1. **Event sources management** — add/remove event JSON sources (URLs or file paths).
2. **Schedule viewer** — display loaded event schedules as a timeline.
3. **Photo-event assignments** — visualize which photos are assigned to which events.
4. **Folder map display** — show the event-to-folder mapping used during export.

### AI-Ready Prompt — Phase 7

```
You are building the Event System UI for the BID web application.
This replaces the legacy EventsWindow Tkinter widget.

CONTEXT — How events work in BID:
1. Users register "event sources" — URLs pointing to JSON schedules (concert timetables)
2. Each schedule contains events with: id, name, start time, end time, status
3. Photos are matched to events by comparing EXIF CreateDate with event time windows
4. During export, photos are sorted into subfolders named after their matched event
5. Example: export/fb/12_06-12_13_BandName/ contains all photos taken during that performance

BACKEND API (already implemented):
- GET  /api/v1/projects/{name}/events/sources → list of {location, label, enabled, source_type}
- POST /api/v1/projects/{name}/events/sources → {location, label} → add source
- DELETE /api/v1/projects/{name}/events/sources/{encoded_location} → remove source
- POST /api/v1/projects/{name}/events/load → reload all sources → returns schedules
- GET  /api/v1/projects/{name}/events/schedules → loaded schedules with events
- POST /api/v1/projects/{name}/events/annotate → annotate source_dict → returns assignment map
- GET  /api/v1/projects/{name}/events/folder-map → {event_id: folder_name}

DATA MODELS:
```typescript
interface EventSource {
  location: string;       // URL or file path
  label: string;
  enabled: boolean;
  source_type: "url" | "file";
}

interface ScheduleEvent {
  id: string;
  name: string;
  start: string;         // ISO datetime
  end: string;           // ISO datetime
  duration_seconds: number;
  status: "was" | "will" | "now";
  type_color: string;    // hex color code
  time_display: string;  // "12:06 - 12:13"
}

interface Schedule {
  title: string;         // "Sobota KONKURS"
  events: ScheduleEvent[];
  last_update: string;
  source_url: string;
}
```

BUILD:

1. `app/(dashboard)/projects/[id]/events/page.tsx` — Events Page:
   
   LAYOUT:
   ```
   ┌─────────────────────────────────────────────────────────┐
   │  EVENT MANAGEMENT                                       │
   ├──────────────────────┬──────────────────────────────────┤
   │  Event Sources       │  Schedule Timeline               │
   │                      │                                  │
   │  [+ Add Source]      │  Sobota KONKURS                  │
   │                      │  ┌────┬────┬────┬────┬────┐     │
   │  ☑ Saturday          │  │Setup│Band│Band│Break│Band│     │
   │    https://...       │  │12:00│12:06│12:30│13:00│13:15│  │
   │    [reload] [delete] │  └────┴────┴────┴────┴────┘     │
   │                      │                                  │
   │  ☑ Sunday            │  Niedziela GALA                  │
   │    https://...       │  ┌────┬────┬────┐               │
   │    [reload] [delete] │  │Setup│Show│End│               │
   │                      │  └────┴────┴────┘               │
   │                      │                                  │
   ├──────────────────────┴──────────────────────────────────┤
   │  Photo Assignments                                      │
   │                                                         │
   │  [Annotate Photos]  [Create Folders]                    │
   │                                                         │
   │  Event: 12:06 - 12:13 BandName                         │
   │    → 15 photos assigned                                 │
   │    → Folder: 12_06-12_13_BandName                       │
   │                                                         │
   │  Event: 12:30 - 13:00 AnotherBand                      │
   │    → 8 photos assigned                                  │
   │    → Folder: 12_30-13_00_AnotherBand                    │
   └─────────────────────────────────────────────────────────┘
   ```

2. `components/event-source-list.tsx`:
   - List of registered event sources
   - Each source: checkbox (enabled/disabled), label, URL (truncated), reload button, delete button
   - "Add Source" button → dialog:
     - URL input (text field)
     - Label input (text field)
     - Auto-detect source type (URL vs file path)
     - Submit: POST /events/sources
   - Delete: confirmation dialog → DELETE /events/sources/{location}
   - Reload single source: POST /events/load

3. `components/schedule-timeline.tsx`:
   - Horizontal timeline visualization for each schedule
   - Events rendered as colored blocks proportional to their duration
   - Color from event's type_color field
   - Hover tooltip: event name, exact time range, duration, status
   - Only "was" status events are highlighted (others are dimmed)
   - Scroll horizontally if timeline is wider than container

4. `components/photo-assignments.tsx`:
   - "Annotate Photos" button → POST /events/annotate
   - Shows results grouped by event:
     - Event time range + name
     - Photo count assigned to this event
     - Target folder name (from folder_map)
     - Expandable list of assigned photo filenames
   - Unmatched photos section: photos that don't fall into any event window

Generate complete, working code for all components.
Use shadcn/ui: Dialog, Checkbox, Badge, Tooltip, Collapsible, Alert.
Use Lucide icons: Calendar, Link, Trash2, RefreshCw, FolderOpen, ImageIcon.
```

---

## Phase 8: Testing & Deployment

### Objective
Comprehensive testing, deployment configuration, and documentation.

### Tasks

1. **API integration tests** — test all endpoints against real `bid/` modules.
2. **Frontend E2E tests** — Playwright tests for critical workflows.
3. **Docker Compose production config** — with TLS, volumes, restart policies.
4. **CI/CD pipeline** — GitHub Actions for test + build + deploy.
5. **Documentation** — README updates, environment setup guide.

### AI-Ready Prompt — Phase 8

```
You are finalizing the BID web application for production deployment.
All components (backend API, frontend, FileBrowser integration) are built.

CREATE:

1. `backend/tests/test_api_projects.py` — Project API tests:
   - Use pytest + httpx.AsyncClient (TestClient)
   - Fixtures: create temp project directory with settings.json, export_option.json
   - Tests:
     - test_list_projects_empty
     - test_create_project
     - test_create_project_duplicate_name → 409
     - test_get_project_details
     - test_get_project_settings
     - test_update_project_settings
     - test_get_export_profiles
     - test_update_export_profiles_valid
     - test_update_export_profiles_invalid → 422
     - test_delete_project
     - test_get_nonexistent_project → 404

2. `backend/tests/test_api_sources.py` — Source API tests:
   - Fixtures: project with sample source_dict, temp source folder with test images
   - Tests:
     - test_get_source_dict
     - test_scan_sources_creates_dict
     - test_update_sources_finds_new_files
     - test_integrity_check_detects_missing
     - test_photo_preview_returns_image
     - test_photo_preview_nonexistent → 404
     - test_path_traversal_blocked → 403

3. `backend/tests/test_api_processing.py` — Processing API tests:
   - Tests:
     - test_process_single_photo
     - test_process_batch
     - test_process_nonexistent_photo → 404
     - test_processing_status

4. `backend/tests/test_api_auth.py` — Auth tests:
   - test_login_valid_credentials
   - test_login_invalid_credentials → 401
   - test_protected_endpoint_no_token → 401
   - test_protected_endpoint_expired_token → 401
   - test_protected_endpoint_valid_token → 200
   - test_refresh_token

5. `frontend/e2e/projects.spec.ts` — Playwright E2E:
   - test_create_new_project
   - test_view_project_list
   - test_navigate_to_project
   - test_view_source_tree
   - test_select_photo_shows_details
   - test_login_redirect

6. `docker/docker-compose.prod.yml`:
   - Nginx with TLS (certbot/Let's Encrypt)
   - All services with restart: unless-stopped
   - Health checks for each service
   - Named volumes for persistent data
   - Resource limits (memory, CPU)
   - Environment variables from .env file

7. `docker/Dockerfile.backend`:
   - Python 3.10-slim base
   - Copy bid/ and backend/ packages
   - Install requirements
   - Run: uvicorn api.main:app --host 0.0.0.0 --port 8000
   - Non-root user

8. `docker/Dockerfile.frontend`:
   - Node 20-alpine base
   - Multi-stage: build then serve
   - Copy frontend/
   - Build: npm run build
   - Run: npm start
   - Non-root user

9. `.github/workflows/ci.yml`:
   - On: push to main, pull_request
   - Jobs:
     a) Backend tests: Python 3.10, pytest
     b) Frontend tests: Node 20, npm test
     c) E2E tests: Playwright (needs both services running)
     d) Docker build: verify images build successfully

10. Update `README.md`:
    - Architecture overview (link to web_architecture.md)
    - Quick start: docker-compose up
    - Development setup: individual service startup
    - API documentation: link to /api/v1/docs (FastAPI Swagger)
    - Environment variables reference

Generate complete, working code for all files.
Reuse existing test fixtures from tests/conftest.py where applicable.
All tests should be runnable with `pytest` (backend) and `npx playwright test` (frontend).
```

---

## File Deliverables Checklist

### Phase 1 — Backend API
- [ ] `backend/api/__init__.py`
- [ ] `backend/api/main.py`
- [ ] `backend/api/deps.py`
- [ ] `backend/api/auth.py`
- [ ] `backend/api/models/*.py` (5 files)
- [ ] `backend/api/routers/*.py` (5 files)
- [ ] `backend/requirements.txt`

### Phase 2 — WebSocket
- [ ] `backend/api/ws_manager.py`
- [ ] `backend/api/routers/ws.py`
- [ ] Updates to `routers/processing.py`
- [ ] Background task registration in `main.py`

### Phase 3 — Frontend Shell
- [ ] `frontend/` (Next.js project)
- [ ] `frontend/lib/api-client.ts`
- [ ] `frontend/lib/types.ts`
- [ ] `frontend/lib/ws.ts`
- [ ] `frontend/app/(auth)/login/page.tsx`
- [ ] `frontend/app/(dashboard)/layout.tsx`
- [ ] `frontend/app/(dashboard)/page.tsx`
- [ ] `frontend/app/(dashboard)/new/page.tsx`
- [ ] `frontend/app/(dashboard)/projects/[id]/layout.tsx`
- [ ] `frontend/middleware.ts`

### Phase 4 — Core UI
- [ ] `frontend/components/source-tree.tsx`
- [ ] `frontend/components/details-panel.tsx`
- [ ] `frontend/components/image-preview.tsx`
- [ ] `frontend/components/toolbar.tsx`
- [ ] `frontend/app/(dashboard)/projects/[id]/page.tsx`

### Phase 5 — Processing
- [ ] `frontend/app/(dashboard)/projects/[id]/processing/page.tsx`
- [ ] `frontend/app/(dashboard)/projects/[id]/export-profiles/page.tsx`
- [ ] `frontend/components/toast-handler.tsx`
- [ ] `frontend/hooks/use-processing-state.ts`

### Phase 6 — FileBrowser
- [ ] `docker/docker-compose.yml`
- [ ] `docker/nginx.conf`
- [ ] `docker/filebrowser.json`
- [ ] `frontend/app/(dashboard)/projects/[id]/files/page.tsx`

### Phase 7 — Events UI
- [ ] `frontend/app/(dashboard)/projects/[id]/events/page.tsx`
- [ ] `frontend/components/event-source-list.tsx`
- [ ] `frontend/components/schedule-timeline.tsx`
- [ ] `frontend/components/photo-assignments.tsx`

### Phase 8 — Testing & Deploy
- [ ] `backend/tests/test_api_*.py` (4 files)
- [ ] `frontend/e2e/*.spec.ts`
- [ ] `docker/docker-compose.prod.yml`
- [ ] `docker/Dockerfile.backend`
- [ ] `docker/Dockerfile.frontend`
- [ ] `.github/workflows/ci.yml`
