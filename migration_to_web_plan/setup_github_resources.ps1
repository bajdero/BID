# BID Web Migration — GitHub Resources Setup
# PowerShell script — safe to run on Windows PowerShell and PowerShell Core
# Usage: .\setup_github_resources.ps1 -Repo "bajdero/BID"

param(
    [string]$Repo = "bajdero/BID"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "BID Web Migration — GitHub Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "Repository: $Repo" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Helper: create or update a label
# ---------------------------------------------------------------------------
function Set-GhLabel {
    param([string]$Name, [string]$Color, [string]$Description)
    Write-Host "  Label: $Name" -NoNewline
    $result = & gh label create $Name --color $Color --description $Description --repo $Repo 2>&1
    if ($LASTEXITCODE -ne 0) {
        # Try update if it already exists
        $result2 = & gh label edit $Name --color $Color --description $Description --repo $Repo 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " (updated)" -ForegroundColor Yellow
        } else {
            Write-Host " WARNING: $result" -ForegroundColor Red
        }
    } else {
        Write-Host " (created)" -ForegroundColor Green
    }
}

# ---------------------------------------------------------------------------
# Helper: create a milestone, return its number
# ---------------------------------------------------------------------------
function New-GhMilestone {
    param([string]$Title, [string]$DueOn)
    Write-Host "  Milestone: $Title" -NoNewline
    $json = & gh api "repos/$Repo/milestones" --method POST `
        -f "title=$Title" `
        -f "due_on=$DueOn" `
        -f "state=open" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host " WARNING: $json" -ForegroundColor Red
        return $null
    }
    $data = $json | ConvertFrom-Json
    Write-Host " -> #$($data.number)" -ForegroundColor Green
    return $data.number
}

# ---------------------------------------------------------------------------
# Helper: get existing milestone number by title
# ---------------------------------------------------------------------------
function Get-MilestoneNumber {
    param([string]$Title)
    $json = & gh api "repos/$Repo/milestones" --paginate 2>&1
    if ($LASTEXITCODE -ne 0) { return $null }
    $milestones = $json | ConvertFrom-Json
    foreach ($m in $milestones) {
        if ($m.title -eq $Title) { return $m.number }
    }
    return $null
}

# ---------------------------------------------------------------------------
# Helper: create an issue, return its number
# ---------------------------------------------------------------------------
function New-GhIssue {
    param(
        [string]$Title,
        [string[]]$Labels,
        [string]$Body,
        [int]$Milestone
    )
    Write-Host "  Issue: $Title" -NoNewline
    $labelArgs = @()
    foreach ($l in $Labels) { $labelArgs += @("--label", $l) }

    # Write body to temp file to avoid quoting issues
    $tmpFile = [System.IO.Path]::GetTempFileName()
    Set-Content -Path $tmpFile -Value $Body -Encoding UTF8

    $result = & gh issue create --repo $Repo --title $Title --body-file $tmpFile --milestone $Milestone @labelArgs 2>&1
    Remove-Item $tmpFile -ErrorAction SilentlyContinue

    if ($LASTEXITCODE -ne 0) {
        Write-Host " WARNING: $result" -ForegroundColor Red
        return $null
    }
    $number = ($result -split "/")[-1].Trim()
    Write-Host " -> #$number" -ForegroundColor Green
    return [int]$number
}

# ===========================================================================
# 1. LABELS
# ===========================================================================
Write-Host "`n[1/3] Creating labels..." -ForegroundColor Cyan

Set-GhLabel -Name "type:epic"    -Color "8B00FF" -Description "Epic issue grouping multiple child issues"
Set-GhLabel -Name "type:feature" -Color "0075CA" -Description "New feature or enhancement"
Set-GhLabel -Name "type:task"    -Color "E4E669" -Description "Non-code task (docs, config, planning)"
Set-GhLabel -Name "type:test"    -Color "0E8A16" -Description "Test implementation or test infrastructure"
Set-GhLabel -Name "type:infra"   -Color "BFD4F2" -Description "Infrastructure, CI/CD, DevOps work"
Set-GhLabel -Name "type:audit"   -Color "D93F0B" -Description "Audit, review, or investigation"
Set-GhLabel -Name "type:release" -Color "C2E0C6" -Description "Release governance, gates, sign-off"
Set-GhLabel -Name "priority:p0"  -Color "B60205" -Description "Critical — release blocker"
Set-GhLabel -Name "priority:p1"  -Color "D93F0B" -Description "High — must complete in milestone"
Set-GhLabel -Name "priority:p2"  -Color "FBCA04" -Description "Medium — important but not blocking"
Set-GhLabel -Name "area:backend"  -Color "1D76DB" -Description "Backend / API work"
Set-GhLabel -Name "area:frontend" -Color "0075CA" -Description "Frontend / UI work"
Set-GhLabel -Name "area:devops"   -Color "5319E7" -Description "DevOps, CI/CD, infrastructure"
Set-GhLabel -Name "area:qa"       -Color "0E8A16" -Description "Quality assurance, testing"

# ===========================================================================
# 2. MILESTONES
# ===========================================================================
Write-Host "`n[2/3] Creating milestones..." -ForegroundColor Cyan

$milestoneMap = @{}

$milestones = @(
    @{ Title = "M1 - Backend API Extraction (Phase 1)";                            Due = "2026-05-31T00:00:00Z" },
    @{ Title = "M2 - WebSocket Real-Time Layer (Phase 2)";                          Due = "2026-06-21T00:00:00Z" },
    @{ Title = "M3 - Frontend Shell (Phase 3)";                                     Due = "2026-07-19T00:00:00Z" },
    @{ Title = "M4 - Core UI Components (Phase 4)";                                 Due = "2026-09-06T00:00:00Z" },
    @{ Title = "M5 - PoC Release 2.0.0-rc1";                                        Due = "2026-09-20T00:00:00Z" },
    @{ Title = "M6 - Architecture and Implementation Audit";                        Due = "2026-10-04T00:00:00Z" },
    @{ Title = "M7 - Processing Dashboard (Phase 5)";                               Due = "2026-11-08T00:00:00Z" },
    @{ Title = "M8 - FileBrowser + Vector Search (Phase 6)";                        Due = "2026-12-06T00:00:00Z" },
    @{ Title = "M9 - Event System UI (Phase 7)";                                    Due = "2027-01-10T00:00:00Z" },
    @{ Title = "M10 - Feature Freeze";                                              Due = "2027-01-20T00:00:00Z" },
    @{ Title = "M11 - Test/Deploy Readiness (Phase 8)";                             Due = "2027-02-20T00:00:00Z" },
    @{ Title = "M12 - Code Freeze";                                                 Due = "2027-02-24T00:00:00Z" },
    @{ Title = "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"; Due = "2027-03-10T00:00:00Z" }
)

foreach ($ms in $milestones) {
    $num = New-GhMilestone -Title $ms.Title -DueOn $ms.Due
    if ($null -eq $num) {
        $num = Get-MilestoneNumber -Title $ms.Title
        if ($null -ne $num) {
            Write-Host "    Found existing milestone #$num" -ForegroundColor Yellow
        }
    }
    if ($null -ne $num) {
        $milestoneMap[$ms.Title] = $num
    }
    Start-Sleep -Milliseconds 300
}

Write-Host "  Milestone map: $($milestoneMap | ConvertTo-Json -Compress)"

# ===========================================================================
# 3. ISSUES  (epics + children)
# ===========================================================================
Write-Host "`n[3/3] Creating issues..." -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Issue body builder
# ---------------------------------------------------------------------------
function Build-IssueBody {
    param(
        [string]$Problem,
        [string[]]$InScope,
        [string[]]$OutScope,
        [string[]]$AcItems,
        [string]$DepsMilestone,
        [string[]]$DepsIssues = @(),
        [string[]]$DodExtra = @()
    )
    $ac = ($AcItems | ForEach-Object { "- [ ] $_" }) -join "`n"
    $inS = ($InScope | ForEach-Object { "- $_" }) -join "`n"
    $outS = ($OutScope | ForEach-Object { "- $_" }) -join "`n"
    $deps = "- **Milestone:** $DepsMilestone`n"
    if ($DepsIssues.Count -gt 0) {
        $deps += "- **Depends on:** " + ($DepsIssues -join ", ") + "`n"
    }
    $dodLines = @(
        "- [ ] All child issues closed",
        "- [ ] Code reviewed and approved",
        "- [ ] Tests written and passing",
        "- [ ] Documentation updated (if applicable)",
        "- [ ] Milestone checklist updated"
    )
    foreach ($d in $DodExtra) { $dodLines += "- [ ] $d" }
    $dod = $dodLines -join "`n"

    return @"
## Problem Statement
$Problem

## Scope
**In scope:**
$inS

**Out of scope:**
$outS

## Acceptance Criteria
$ac

## Dependencies
$deps
## Definition of Done
$dod
"@
}

# ---------------------------------------------------------------------------
# PHASE 1
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M1 - Backend API Extraction (Phase 1)"]
if ($ms) {
    Write-Host "`n  --- Phase 1: Backend API Extraction ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "BID is a desktop tkinter app. We need to extract its core logic into a REST API so it can be consumed by a web frontend." `
        -InScope @("Extract image-processing logic to a service layer","Define and implement REST API endpoints","Add API-key authentication","Containerise the backend","Write unit tests") `
        -OutScope @("Frontend implementation","WebSocket layer (Phase 2)","Vector search (Phase 6)") `
        -AcItems @("All Phase 1 child issues are closed","OpenAPI spec published at /docs","Backend runs in Docker","All unit tests pass in CI") `
        -DepsMilestone "M1 - Backend API Extraction (Phase 1)"
    $epicNum = New-GhIssue -Title "[Epic] Phase 1 — Backend API Extraction" -Labels @("type:epic","priority:p1","area:backend") -Body $body -Milestone $ms

    $children = @(
        @{ Title="Extract image-processing core to service layer"; Labels=@("type:feature","priority:p1","area:backend"); Problem="The image-processing logic is tightly coupled to the tkinter UI. It must be decoupled into an independently testable service module."; AcItems=@("Service module callable without UI context","Existing unit tests still pass","No tkinter imports in service layer") },
        @{ Title="Define REST API contract (OpenAPI/Swagger spec)"; Labels=@("type:task","priority:p1","area:backend"); Problem="A formal API contract is needed before implementation to ensure frontend/backend alignment."; AcItems=@("OpenAPI YAML committed to repository","Spec reviewed and approved","All endpoint schemas defined") },
        @{ Title="Implement FastAPI application scaffold"; Labels=@("type:feature","priority:p1","area:backend"); Problem="We need a runnable FastAPI application as the foundation for all API endpoints."; AcItems=@("FastAPI app starts without errors","GET /health returns 200","App included in docker-compose") },
        @{ Title="Implement /jobs CRUD endpoints"; Labels=@("type:feature","priority:p1","area:backend"); Problem="The frontend needs to create, list, retrieve, and cancel processing jobs via the API."; AcItems=@("All four endpoints return correct HTTP status codes","Job state transitions validated","Unit tests cover happy path and error cases") },
        @{ Title="Implement /export-profiles endpoints"; Labels=@("type:feature","priority:p1","area:backend"); Problem="Export profiles must be manageable through the API, replacing the static JSON file."; AcItems=@("CRUD operations work end-to-end","Profiles persisted between restarts","Validation rejects invalid configs") },
        @{ Title="Implement file-upload endpoint (/files/upload)"; Labels=@("type:feature","priority:p1","area:backend"); Problem="Users need to upload source images through the web interface."; AcItems=@("Accepts JPEG, PNG, TIFF up to 100 MB","Returns file ID","Unit tests pass") },
        @{ Title="Implement processed-file download endpoint (/files/download/{id})"; Labels=@("type:feature","priority:p1","area:backend"); Problem="Users need to download processed output files from the web UI."; AcItems=@("Endpoint streams file correctly","Returns appropriate Content-Disposition header","Returns 404 for missing file") },
        @{ Title="Add API authentication (API-key header)"; Labels=@("type:feature","priority:p1","area:backend"); Problem="The API must be protected to prevent unauthorised access."; AcItems=@("All endpoints return 401 without valid key","Valid key grants access","Key not logged or exposed") },
        @{ Title="Containerise backend (Dockerfile + docker-compose)"; Labels=@("type:infra","priority:p1","area:devops"); Problem="The backend must run reliably across environments via Docker."; AcItems=@("docker-compose up starts backend successfully","Health check passes inside container","Image build succeeds in CI") },
        @{ Title="Unit tests for all Phase 1 API endpoints"; Labels=@("type:test","priority:p1","area:backend"); Problem="Each Phase 1 endpoint needs automated unit tests to prevent regressions."; AcItems=@("All tests pass in CI","Coverage report shows >= 80%","Tests run in under 60 seconds") }
    )
    foreach ($c in $children) {
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of phase scope") -AcItems $c.AcItems -DepsMilestone "M1 - Backend API Extraction (Phase 1)" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Phase 1 — Backend API Extraction_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# PHASE 2
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M2 - WebSocket Real-Time Layer (Phase 2)"]
if ($ms) {
    Write-Host "`n  --- Phase 2: WebSocket Real-Time Layer ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "The API supports long-running batch jobs. The frontend needs real-time progress updates without polling." `
        -InScope @("WebSocket server endpoint","Event schema","Event broadcasting in pipeline","Connection lifecycle","WebSocket auth") `
        -OutScope @("Frontend WebSocket client (Phase 3)","Persistent event log API (Phase 7)") `
        -AcItems @("All Phase 2 child issues closed","Frontend can receive live progress events","Reconnect logic tested") `
        -DepsMilestone "M2 - WebSocket Real-Time Layer (Phase 2)" `
        -DepsIssues @("Phase 1 epic")
    $epicNum = New-GhIssue -Title "[Epic] Phase 2 — WebSocket Real-Time Layer" -Labels @("type:epic","priority:p1","area:backend") -Body $body -Milestone $ms

    $children = @(
        @{ Title="Implement WebSocket server endpoint (/ws/jobs/{job_id})"; Labels=@("type:feature","priority:p1","area:backend"); Problem="Clients need a WebSocket endpoint to subscribe to per-job progress events."; AcItems=@("Client receives events when job progresses","Multiple clients can subscribe to same job","Unit tests pass") },
        @{ Title="Define event schema (progress, complete, error, cancelled)"; Labels=@("type:task","priority:p1","area:backend"); Problem="A consistent event schema is needed for frontend parsing and future extensibility."; AcItems=@("Schema document committed","All event types have required fields","Backend events conform to schema") },
        @{ Title="Integrate event broadcasting into image-processing pipeline"; Labels=@("type:feature","priority:p1","area:backend"); Problem="The processing pipeline must emit WebSocket events at each stage so the frontend can show live progress."; AcItems=@("Pipeline emits events observable via WebSocket","Integration test verifies event sequence","No processing performance regression > 5%") },
        @{ Title="Implement connection-lifecycle management (connect/disconnect/reconnect)"; Labels=@("type:feature","priority:p1","area:backend"); Problem="WebSocket connections can drop; the server must handle this gracefully without leaking resources."; AcItems=@("Disconnected clients cleaned up within 5s","No memory leak after 100 connect/disconnect cycles","Unknown job IDs rejected") },
        @{ Title="Add WebSocket authentication (token handshake)"; Labels=@("type:feature","priority:p1","area:backend"); Problem="WebSocket connections must be authenticated to prevent unauthorised job monitoring."; AcItems=@("Unauthenticated connections are rejected","Authenticated connections receive events normally","Token not logged") },
        @{ Title="Integration tests for WebSocket event flow"; Labels=@("type:test","priority:p1","area:backend"); Problem="The complete WebSocket flow must be verified by automated tests."; AcItems=@("All integration tests pass in CI","Tests verify correct event ordering","Runs in under 90 seconds") }
    )
    foreach ($c in $children) {
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of phase scope") -AcItems $c.AcItems -DepsMilestone "M2 - WebSocket Real-Time Layer (Phase 2)" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Phase 2 — WebSocket Real-Time Layer_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# PHASE 3
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M3 - Frontend Shell (Phase 3)"]
if ($ms) {
    Write-Host "`n  --- Phase 3: Frontend Shell ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "There is no web frontend. We need a complete project scaffold wired to the backend API." `
        -InScope @("React+TypeScript+Vite scaffold","Routing","State management","API client","WebSocket hook","Base layout","Login screen","CI pipeline") `
        -OutScope @("Business-logic UI panels (Phase 4+)") `
        -AcItems @("All Phase 3 child issues closed","App builds and deploys to staging","Login flow works end-to-end") `
        -DepsMilestone "M3 - Frontend Shell (Phase 3)" `
        -DepsIssues @("Phase 2 epic")
    $epicNum = New-GhIssue -Title "[Epic] Phase 3 — Frontend Shell" -Labels @("type:epic","priority:p1","area:frontend") -Body $body -Milestone $ms

    $children = @(
        @{ Title="Initialise frontend project (React + TypeScript + Vite)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="No frontend project exists. A properly configured React/TypeScript/Vite project is the foundation for all frontend work."; AcItems=@("npm run dev starts dev server","npm run build produces production bundle","npm run test runs Vitest","Lint passes with zero warnings") },
        @{ Title="Configure routing (React Router v6)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="The app needs client-side routing to support multiple pages/views without full page reloads."; AcItems=@("Navigating between routes works","Unauthenticated users redirected to login","404 page shown for unknown routes") },
        @{ Title="Set up global state management (Zustand)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Shared state needs a predictable management solution."; AcItems=@("Auth store persists token across page reloads","Stores have TypeScript types","Unit tests for stores pass") },
        @{ Title="Implement API client layer (axios + OpenAPI-generated types)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Frontend components need a typed, consistent way to call the backend REST API."; AcItems=@("API calls include X-API-Key header automatically","TypeScript types match OpenAPI spec","401 responses trigger logout") },
        @{ Title="Implement WebSocket client hook with auto-reconnect"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Components need a reusable React hook to subscribe to job WebSocket events with automatic reconnection."; AcItems=@("Hook reconnects after server restart","Events typed per ws_events schema","Hook unit tests pass") },
        @{ Title="Create base layout: header, sidebar nav, main content area"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="A consistent shell layout is needed as the container for all page content."; AcItems=@("Layout renders correctly at 1024, 1440, 1920px","Nav highlights active route","Vitest snapshot test passes") },
        @{ Title="Implement login / API-key entry screen"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users must enter their API key to authenticate before accessing the app."; AcItems=@("Successful login navigates to dashboard","Invalid key shows error message","Token stored securely") },
        @{ Title="CI pipeline for frontend (lint + build + unit tests on PR)"; Labels=@("type:infra","priority:p1","area:devops"); Problem="All frontend PRs must pass automated lint, build, and test checks before merge."; AcItems=@("Workflow runs on every PR targeting main","Build artifact uploaded","All steps pass on clean scaffold") }
    )
    foreach ($c in $children) {
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of phase scope") -AcItems $c.AcItems -DepsMilestone "M3 - Frontend Shell (Phase 3)" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Phase 3 — Frontend Shell_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# PHASE 4
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M4 - Core UI Components (Phase 4)"]
if ($ms) {
    Write-Host "`n  --- Phase 4: Core UI Components ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "The frontend shell exists but has no domain-specific UI. Core panels are needed for basic end-to-end usage." `
        -InScope @("Settings panel","Export-profile manager","Source-folder browser","Job-creation wizard","Job queue panel","Image preview","Component tests") `
        -OutScope @("Real-time processing dashboard (Phase 5)","Advanced file browser (Phase 6)") `
        -AcItems @("All Phase 4 child issues closed","User can create and monitor a job end-to-end","Component tests pass in CI") `
        -DepsMilestone "M4 - Core UI Components (Phase 4)" `
        -DepsIssues @("Phase 3 epic")
    $epicNum = New-GhIssue -Title "[Epic] Phase 4 — Core UI Components" -Labels @("type:epic","priority:p1","area:frontend") -Body $body -Milestone $ms

    $children = @(
        @{ Title="Settings panel (source folder, export folder, global options)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need to configure application-wide settings through the UI instead of editing JSON files."; AcItems=@("Settings save persists across refresh","Validation prevents empty paths","Unit test covers form submission") },
        @{ Title="Export-profile manager (list, create, edit, delete profiles)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need a UI to manage export profiles instead of editing export_option.json directly."; AcItems=@("CRUD operations reflected immediately","Invalid values prevented by validation","Unit tests for form pass") },
        @{ Title="Source-folder browser (read-only tree view)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need to see the source folder structure to select session folders for processing."; AcItems=@("Tree renders source folder structure correctly","Expand/collapse works","Unit test with mocked API passes") },
        @{ Title="Job-creation wizard (select sources, choose profile, submit)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need a guided multi-step flow to create a processing job."; AcItems=@("Job created successfully in 3 steps","Wizard validates each step","On success navigates to job detail page") },
        @{ Title="Job queue panel (list active and recent jobs with status)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need visibility into all their jobs: running, completed, and failed."; AcItems=@("Jobs list updates without full page reload","Cancel action calls DELETE /jobs/{id}","Unit test with mock data passes") },
        @{ Title="Basic image-preview component (thumbnail + metadata)"; Labels=@("type:feature","priority:p2","area:frontend"); Problem="Users need a quick preview of processed images without downloading the full file."; AcItems=@("Thumbnail loads within 2s on LAN","Metadata displayed correctly","Shows placeholder on load error") },
        @{ Title="Component unit tests for Phase 4 (React Testing Library)"; Labels=@("type:test","priority:p1","area:frontend"); Problem="All Phase 4 components need automated unit tests to prevent UI regressions."; AcItems=@("All tests pass in CI","Coverage >= 75% for Phase 4 components","No skipped tests without justification") }
    )
    foreach ($c in $children) {
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of phase scope") -AcItems $c.AcItems -DepsMilestone "M4 - Core UI Components (Phase 4)" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Phase 4 — Core UI Components_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# POC RELEASE (M5)
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M5 - PoC Release 2.0.0-rc1"]
if ($ms) {
    Write-Host "`n  --- PoC Release Readiness (M5) ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "Phases 1-4 are complete but have not been validated as a shippable proof-of-concept. We need a release candidate build and stakeholder sign-off before continuing to Phase 5." `
        -InScope @("Build and tag 2.0.0-rc1","Smoke testing","Stakeholder demo") `
        -OutScope @("Full regression suite (Phase 8)","Performance testing") `
        -AcItems @("Release candidate tagged as 2.0.0-rc1","Smoke tests pass","Stakeholders sign off") `
        -DepsMilestone "M5 - PoC Release 2.0.0-rc1" `
        -DepsIssues @("Phase 4 epic")
    $epicNum = New-GhIssue -Title "[Epic] PoC Release Readiness (2.0.0-rc1)" -Labels @("type:epic","type:release","priority:p0","area:devops") -Body $body -Milestone $ms

    @(
        @{ Title="Release candidate build and smoke test (2.0.0-rc1)"; Labels=@("type:release","priority:p0","area:devops"); Problem="We need to tag and build the first release candidate to validate that Phases 1-4 are production-ready enough for a PoC."; AcItems=@("Git tag 2.0.0-rc1 exists","Docker images build without errors","All smoke test items pass","Deployment to staging successful") },
        @{ Title="Internal demo and stakeholder sign-off for PoC"; Labels=@("type:task","priority:p0","area:qa"); Problem="Stakeholders need to validate the PoC before committing to full development (Phases 5-8)."; AcItems=@("Demo conducted with all stakeholders present","Feedback documented","Sign-off recorded","Go/no-go decision made") }
    ) | ForEach-Object {
        $c = $_
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of scope") -AcItems $c.AcItems -DepsMilestone "M5 - PoC Release 2.0.0-rc1" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] PoC Release Readiness (2.0.0-rc1)_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# ARCHITECTURE AUDIT (M6) — starts only after M5 is complete
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M6 - Architecture and Implementation Audit"]
if ($ms) {
    Write-Host "`n  --- Post-PoC Architecture Audit (M6) ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "The PoC revealed the overall approach but may have introduced architectural shortcuts. A formal audit is needed before full development." `
        -InScope @("Backend API design review","Frontend architecture review","Security review","Performance baseline") `
        -OutScope @("Implementing fixes (tracked separately)","External penetration test") `
        -AcItems @("All audit child issues closed","Audit findings report published","Remediation plan created and prioritised") `
        -DepsMilestone "M6 - Architecture and Implementation Audit" `
        -DepsIssues @("PoC Release Readiness epic (M5 must be COMPLETE before this milestone begins)") `
        -DodExtra @("Remediation items added to relevant phase backlogs")
    $epicNum = New-GhIssue -Title "[Epic] Post-PoC Architecture and Implementation Audit" -Labels @("type:epic","type:audit","priority:p1","area:backend") -Body $body -Milestone $ms

    @(
        @{ Title="Architecture review — backend API design and scalability"; Labels=@("type:audit","priority:p1","area:backend"); Problem="The PoC backend was built for speed. A formal review is needed to assess scalability and maintainability before Phase 5."; AcItems=@("Review findings documented","At least one severity-rated finding per category","Remediation recommendations included") },
        @{ Title="Architecture review — frontend state and component model"; Labels=@("type:audit","priority:p1","area:frontend"); Problem="The frontend state management and component architecture need formal review before building more complex UI."; AcItems=@("Review findings documented","Component dependency graph produced","Recommendations for Phase 5+ accepted") },
        @{ Title="Security review — authentication and data flow"; Labels=@("type:audit","priority:p0","area:backend"); Problem="The PoC uses a simple API-key auth. A security review is needed to identify gaps before handling real user data."; AcItems=@("OWASP Top-10 checklist completed","All P0 security findings have remediation issues created","Review report published") },
        @{ Title="Performance baseline — API latency and WebSocket throughput"; Labels=@("type:audit","priority:p1","area:backend"); Problem="We need baseline performance numbers to set targets for Phase 8 load testing."; AcItems=@("Baseline numbers documented","Results committed to docs/performance_baseline.md","Comparison targets defined for Phase 8") },
        @{ Title="Audit findings report and remediation plan"; Labels=@("type:task","priority:p1","area:qa"); Problem="All audit findings need to be consolidated into a single report with a prioritised remediation plan."; AcItems=@("Report published as docs/audit_report_m6.md","All P0 findings have remediation issues created","Remediation plan accepted by team") }
    ) | ForEach-Object {
        $c = $_
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of scope") -AcItems $c.AcItems `
            -DepsMilestone "M6 - Architecture and Implementation Audit" `
            -DepsIssues @("Epic #$epicNum","NOTE: M5 PoC Release must be complete before starting work on this issue")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Post-PoC Architecture and Implementation Audit_`n"
        $cbody += "_**Sequence constraint:** This milestone starts only after M5 - PoC Release 2.0.0-rc1 is complete._`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# PHASE 5 (M7)
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M7 - Processing Dashboard (Phase 5)"]
if ($ms) {
    Write-Host "`n  --- Phase 5: Processing Dashboard (M7) ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "Users have no real-time visibility into running jobs beyond the basic queue panel from Phase 4." `
        -InScope @("Real-time progress bars","Per-file status grid","Aggregate statistics","Error detail modal","Processing history log","E2E smoke test") `
        -OutScope @("Advanced analytics / reporting (future)","Mobile notifications") `
        -AcItems @("All Phase 5 child issues closed","User can monitor a running job in real-time","E2E smoke test passes") `
        -DepsMilestone "M7 - Processing Dashboard (Phase 5)" `
        -DepsIssues @("Phase 4 epic","Post-PoC Architecture Audit epic")
    $epicNum = New-GhIssue -Title "[Epic] Phase 5 — Processing Dashboard" -Labels @("type:epic","priority:p1","area:frontend") -Body $body -Milestone $ms

    @(
        @{ Title="Real-time per-job progress bar (via WebSocket)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need to see live job progress without polling."; AcItems=@("Progress updates received in < 1s","Progress bar animates smoothly","Unit test with mock WebSocket passes") },
        @{ Title="Per-file status grid (queued / processing / done / error)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need file-level visibility into the processing state of each image in a job."; AcItems=@("Grid updates in real-time","Status badges use consistent colour coding","Unit test passes") },
        @{ Title="Aggregate statistics panel (throughput, ETA, error rate)"; Labels=@("type:feature","priority:p2","area:frontend"); Problem="Users want at-a-glance metrics for a running job."; AcItems=@("Statistics update at least every 5s","ETA calculation within 20% accuracy","Panel renders without errors") },
        @{ Title="Error detail modal with retry / skip actions"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="When a file fails processing, users need to understand why and take action."; AcItems=@("Modal opens from error row in file grid","Retry/skip actions call correct API endpoints","Unit test passes") },
        @{ Title="Processing history log (paginated, filterable)"; Labels=@("type:feature","priority:p2","area:frontend"); Problem="Users need to review past jobs and their outcomes."; AcItems=@("History loads from GET /jobs with filters","Pagination works correctly","Filters apply without page reload") },
        @{ Title="Dashboard E2E smoke test (Playwright)"; Labels=@("type:test","priority:p1","area:qa"); Problem="The Phase 5 dashboard needs an automated E2E test to verify the full real-time flow."; AcItems=@("E2E test passes in CI against staging","Test completes in < 5 minutes","Test is flake-free over 3 consecutive runs") }
    ) | ForEach-Object {
        $c = $_
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of phase scope") -AcItems $c.AcItems -DepsMilestone "M7 - Processing Dashboard (Phase 5)" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Phase 5 — Processing Dashboard_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# PHASE 6 (M8)
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M8 - FileBrowser + Vector Search (Phase 6)"]
if ($ms) {
    Write-Host "`n  --- Phase 6: FileBrowser + Vector Search (M8) ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "Users lack an advanced file browser and cannot search for similar images by visual similarity." `
        -InScope @("Full file-browser component","Vector embedding generation","Similarity search endpoint","Similarity search UI","Metadata filter sidebar","Integration tests") `
        -OutScope @("Multi-modal search (text + image)","Cloud storage backends") `
        -AcItems @("All Phase 6 child issues closed","User can browse files and find similar images","Integration tests pass") `
        -DepsMilestone "M8 - FileBrowser + Vector Search (Phase 6)" `
        -DepsIssues @("Phase 5 epic")
    $epicNum = New-GhIssue -Title "[Epic] Phase 6 — FileBrowser + Vector Search" -Labels @("type:epic","priority:p1","area:frontend") -Body $body -Milestone $ms

    @(
        @{ Title="Full file-browser component (navigate source and export trees)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="The read-only tree from Phase 4 needs to be extended into a full file browser."; AcItems=@("Both trees navigate correctly","Thumbnail renders for images","Breadcrumb updates on navigation") },
        @{ Title="Backend: generate and store image embedding vectors"; Labels=@("type:feature","priority:p1","area:backend"); Problem="Similarity search requires pre-computed vector embeddings for each processed image."; AcItems=@("Embeddings generated for all test images","Storage persists across container restarts","Embedding adds < 20% overhead") },
        @{ Title="Backend: vector-similarity search endpoint (/search/similar)"; Labels=@("type:feature","priority:p1","area:backend"); Problem="The frontend needs a backend endpoint to query for visually similar images."; AcItems=@("Endpoint returns relevant results","Response time < 2s for 1000-image corpus","Integration tests pass") },
        @{ Title="Frontend: similarity-search UI (upload query image, show results)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need a UI to find images visually similar to a query image."; AcItems=@("Search returns and displays results within 3s","Results grid shows thumbnails and scores","Unit test with mock API passes") },
        @{ Title="Metadata-filter sidebar (date, profile, author, status)"; Labels=@("type:feature","priority:p2","area:frontend"); Problem="Users need to filter the file browser by metadata to find specific images quickly."; AcItems=@("Filters reduce file list correctly","Multiple filters combine with AND logic","Clear-all button resets filters") },
        @{ Title="Integration tests for vector-search endpoint"; Labels=@("type:test","priority:p1","area:backend"); Problem="The vector search flow needs automated integration tests with real image data."; AcItems=@("All integration tests pass in CI","Tests use reproducible test image set","Runs in < 3 minutes") }
    ) | ForEach-Object {
        $c = $_
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of phase scope") -AcItems $c.AcItems -DepsMilestone "M8 - FileBrowser + Vector Search (Phase 6)" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Phase 6 — FileBrowser + Vector Search_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# PHASE 7 (M9)
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M9 - Event System UI (Phase 7)"]
if ($ms) {
    Write-Host "`n  --- Phase 7: Event System UI (M9) ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "System events are only visible in the processing dashboard. A dedicated event/notification system is needed for operational awareness." `
        -InScope @("Event-log viewer","Notification toasts","Alert management page","System-health indicators","Structured event log API","E2E tests") `
        -OutScope @("External alerting integrations (Slack, PagerDuty — future)","Log aggregation (ELK/Loki — Phase 8 monitoring)") `
        -AcItems @("All Phase 7 child issues closed","Operators can see all system events and acknowledge alerts","E2E tests pass") `
        -DepsMilestone "M9 - Event System UI (Phase 7)" `
        -DepsIssues @("Phase 6 epic")
    $epicNum = New-GhIssue -Title "[Epic] Phase 7 — Event System UI" -Labels @("type:epic","priority:p1","area:frontend") -Body $body -Milestone $ms

    @(
        @{ Title="Event-log viewer (streaming table, filter by level/job/time)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Operators need a live view of all system events for debugging and monitoring."; AcItems=@("Log viewer shows events within 2s","Filters work correctly","Auto-scroll pauses on hover") },
        @{ Title="In-app notification toasts (success / warning / error)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Users need immediate visual feedback for important events without watching the event log."; AcItems=@("Toasts appear for all three event types","Error toasts require manual dismiss","No layout shift from toasts") },
        @{ Title="Alert management page (acknowledge, dismiss, history)"; Labels=@("type:feature","priority:p2","area:frontend"); Problem="Persistent alerts need a dedicated page for lifecycle management."; AcItems=@("Acknowledge/dismiss persists via API","Historical alerts accessible","Unit test passes") },
        @{ Title="System-health indicators (backend uptime, queue depth, error rate)"; Labels=@("type:feature","priority:p1","area:frontend"); Problem="Operators need at-a-glance system health visibility in the UI."; AcItems=@("Indicators update every 30s","Red indicator when backend is unreachable","Unit test with mock health endpoint passes") },
        @{ Title="Backend: structured event log API (/events)"; Labels=@("type:feature","priority:p1","area:backend"); Problem="The frontend event viewer and alert system need a backend API to query structured events."; AcItems=@("Endpoint returns paginated events","Acknowledge endpoint updates event status","Integration test passes") },
        @{ Title="E2E tests for event-log and notification flows"; Labels=@("type:test","priority:p1","area:qa"); Problem="Phase 7 features need automated E2E tests to verify the event system works end-to-end."; AcItems=@("E2E tests pass in CI against staging","Tests are flake-free over 3 runs","Completes in < 5 minutes") }
    ) | ForEach-Object {
        $c = $_
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of phase scope") -AcItems $c.AcItems -DepsMilestone "M9 - Event System UI (Phase 7)" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Phase 7 — Event System UI_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# RELEASE HARDENING (M10 Feature Freeze)
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M10 - Feature Freeze"]
if ($ms) {
    Write-Host "`n  --- Release Hardening: Feature Freeze (M10) ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "Development is complete. The system must be hardened for production: no new features, regressions fixed, and code frozen before final deployment." `
        -InScope @("Feature freeze enforcement","Regression test run","Code freeze enforcement") `
        -OutScope @("New features (frozen)","Non-critical improvements") `
        -AcItems @("Feature Freeze Gate closed","Regression tests pass","Code Freeze Gate closed") `
        -DepsMilestone "M10 - Feature Freeze" `
        -DepsIssues @("Phase 7 epic")
    $epicNum = New-GhIssue -Title "[Epic] Release Hardening (Feature Freeze to Code Freeze)" -Labels @("type:epic","type:release","priority:p0","area:devops") -Body $body -Milestone $ms

    # Feature Freeze Gate (M10)
    $ffBody = Build-IssueBody `
        -Problem "After 2027-01-20, no new feature PRs may be merged. Only bug fixes, test improvements, and release blockers are permitted." `
        -InScope @("Document feature freeze policy in CONTRIBUTING.md","Add PR label check blocking type:feature PRs after freeze date","Notify all contributors") `
        -OutScope @("Retroactive feature additions","Performance improvements (allowed if non-functional)") `
        -AcItems @("CONTRIBUTING.md updated with freeze policy","CI check in place and tested","All contributors notified","No open type:feature PRs without freeze exception approval") `
        -DepsMilestone "M10 - Feature Freeze" `
        -DepsIssues @("Epic #$epicNum")
    $ffBody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Release Hardening (Feature Freeze to Code Freeze)_`n"
    New-GhIssue -Title "Feature Freeze Gate — no new features after 2027-01-20" -Labels @("type:release","priority:p0","area:devops") -Body $ffBody -Milestone $ms
    Start-Sleep -Milliseconds 400

    # Regression test run (M10)
    $regBody = Build-IssueBody `
        -Problem "A full regression test run is needed after feature freeze to establish the quality baseline for the release." `
        -InScope @("Run full test suite (unit + integration + E2E)","Document results","Create issues for all failures") `
        -OutScope @("New test development (only fixing failures)") `
        -AcItems @("Full test suite passes with zero failures","Results documented in docs/regression_freeze_2027-01-20.md","All failures resolved before Code Freeze") `
        -DepsMilestone "M10 - Feature Freeze" `
        -DepsIssues @("Epic #$epicNum","Feature Freeze Gate must be closed first")
    $regBody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Release Hardening (Feature Freeze to Code Freeze)_`n"
    New-GhIssue -Title "Regression test run against feature-freeze build" -Labels @("type:test","priority:p0","area:qa") -Body $regBody -Milestone $ms
    Start-Sleep -Milliseconds 400

    # Code Freeze Gate (M12)
    $ms12 = $milestoneMap["M12 - Code Freeze"]
    if ($ms12) {
        $cfBody = Build-IssueBody `
            -Problem "After 2027-02-24, only P0 release blocker fixes may be merged. All other changes are deferred to post-2.0.0." `
            -InScope @("Update CONTRIBUTING.md with code freeze policy","CI check blocks non-P0 PRs after code freeze date") `
            -OutScope @("Hotfixes with explicit release-blocker label exception") `
            -AcItems @("CONTRIBUTING.md updated","CI check tested and verified","No non-P0 PRs merged after 2027-02-24 without exception") `
            -DepsMilestone "M12 - Code Freeze" `
            -DepsIssues @("Epic #$epicNum","Regression tests must pass first")
        $cfBody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Release Hardening (Feature Freeze to Code Freeze)_`n"
        New-GhIssue -Title "Code Freeze Gate — only release blockers after 2027-02-24" -Labels @("type:release","priority:p0","area:devops") -Body $cfBody -Milestone $ms12
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# PHASE 8 (M11)
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M11 - Test/Deploy Readiness (Phase 8)"]
if ($ms) {
    Write-Host "`n  --- Phase 8: Test/Deploy Readiness (M11) ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "The application is feature-complete but not production-hardened. We need comprehensive testing, CI/CD, and operational infrastructure before the 2.0.0 release." `
        -InScope @("Full E2E suite","Load tests","Security audit","Production Docker","CI/CD pipeline","K8s/Compose manifests","Monitoring","Runbook") `
        -OutScope @("Feature development (frozen)","Multi-region deployment (future)") `
        -AcItems @("All Phase 8 child issues closed","CI/CD pipeline deploys to production","Monitoring operational","Runbook reviewed") `
        -DepsMilestone "M11 - Test/Deploy Readiness (Phase 8)" `
        -DepsIssues @("Release Hardening epic (Feature Freeze Gate must be closed)")
    $epicNum = New-GhIssue -Title "[Epic] Phase 8 — Test/Deploy Readiness" -Labels @("type:epic","priority:p0","area:qa") -Body $body -Milestone $ms

    @(
        @{ Title="Full E2E test suite (Playwright — happy path + edge cases)"; Labels=@("type:test","priority:p0","area:qa"); Problem="A comprehensive E2E suite is needed to validate all user-facing flows before the 2.0.0 production release."; AcItems=@("All E2E tests pass in CI","Zero flaky tests over 5 consecutive runs","Suite completes in < 15 minutes") },
        @{ Title="Performance / load tests (k6 — 50 concurrent jobs baseline)"; Labels=@("type:test","priority:p0","area:qa"); Problem="We need to verify the system meets performance targets under realistic load before production."; AcItems=@("P95 API latency < 500ms under 50 concurrent jobs","WebSocket event delay < 2s","Zero 5xx errors under load test","Results documented") },
        @{ Title="Security audit — OWASP Top-10 review and dependency scan"; Labels=@("type:audit","priority:p0","area:qa"); Problem="Final security audit is required before the 2.0.0 production release."; AcItems=@("OWASP Top-10 checklist complete with no open P0 items","Dependency scan shows zero critical CVEs","Audit report published as docs/security_audit_2.0.0.md") },
        @{ Title="Production Dockerfile + docker-compose (multi-stage, non-root)"; Labels=@("type:infra","priority:p0","area:devops"); Problem="The development Dockerfiles need to be hardened for production."; AcItems=@("Images build without errors","Containers run as non-root","Image sizes within limits","Health checks pass") },
        @{ Title="GitHub Actions CI/CD pipeline (test, build, push image, deploy)"; Labels=@("type:infra","priority:p0","area:devops"); Problem="A full CI/CD pipeline is required to automate testing, image building, and deployment for the 2.0.0 release."; AcItems=@("Pipeline runs end-to-end without manual intervention","Staging deployed on every merge to main","Production deployed on release tag","Rollback procedure documented") },
        @{ Title="Kubernetes / Compose production deployment manifests"; Labels=@("type:infra","priority:p1","area:devops"); Problem="Production deployment needs declarative manifests for reproducible, version-controlled deployments."; AcItems=@("Manifests deploy successfully to staging cluster","All resource limits set","Probes configured and passing") },
        @{ Title="Monitoring stack (Prometheus metrics + Grafana dashboard)"; Labels=@("type:infra","priority:p1","area:devops"); Problem="Production operations require observability: metrics collection and dashboarding."; AcItems=@("Metrics endpoint accessible and scraped by Prometheus","Grafana dashboard operational in staging","Alert rules fire correctly in test") },
        @{ Title="Runbook and operations guide"; Labels=@("type:task","priority:p1","area:devops"); Problem="Operations team needs a runbook covering deployment, common failure scenarios, and rollback procedures."; AcItems=@("Runbook committed as docs/runbook.md","Reviewed by at least one ops team member","All commands tested successfully") }
    ) | ForEach-Object {
        $c = $_
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Out of phase scope") -AcItems $c.AcItems -DepsMilestone "M11 - Test/Deploy Readiness (Phase 8)" -DepsIssues @("Epic #$epicNum")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Phase 8 — Test/Deploy Readiness_`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ---------------------------------------------------------------------------
# FINAL DEPLOYMENT (M13) — Release 2.0.0
# ---------------------------------------------------------------------------
$ms = $milestoneMap["M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"]
if ($ms) {
    Write-Host "`n  --- Final Deployment and Sign-off (M13) — Release 2.0.0 ---" -ForegroundColor Magenta
    $body = Build-IssueBody `
        -Problem "The 2.0.0 release is ready. We need to deploy to production, validate the deployment, and obtain final sign-off." `
        -InScope @("Production deployment of 2.0.0","Go-Live Gate validation","Final stakeholder sign-off") `
        -OutScope @("Post-2.0.0 features (tracked separately)") `
        -AcItems @("Release 2.0.0 deployed to production","Go-Live Gate passed","Final sign-off obtained") `
        -DepsMilestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off" `
        -DepsIssues @("Phase 8 epic (all issues closed)","Code Freeze Gate closed") `
        -DodExtra @("Git tag 2.0.0 created and pushed","Release notes published")
    $epicNum = New-GhIssue -Title "[Epic] Final Deployment and Sign-off (Release 2.0.0)" -Labels @("type:epic","type:release","priority:p0","area:devops") -Body $body -Milestone $ms

    @(
        @{
            Title="Production deployment of release 2.0.0"
            Labels=@("type:release","priority:p0","area:devops")
            Problem="Execute the production deployment of BID web version 2.0.0."
            AcItems=@("Git tag 2.0.0 exists","Production deployment succeeds via CI/CD pipeline","Health checks pass post-deployment","Monitoring shows green status")
        },
        @{
            Title="Go-Live Gate — deployment validation and rollback readiness"
            Labels=@("type:release","priority:p0","area:devops")
            Problem="Before declaring 2.0.0 live, we must validate the production deployment and confirm rollback capability."
            AcItems=@("All production smoke tests pass","Rollback tested successfully in staging within 5 minutes","Monitoring and alerting confirmed active in production","Go/no-go sign-off recorded")
        },
        @{
            Title="Final stakeholder sign-off for release 2.0.0"
            Labels=@("type:task","priority:p0","area:qa")
            Problem="Release 2.0.0 requires formal stakeholder acceptance before the project can be closed."
            AcItems=@("Sign-off obtained from all required stakeholders","Release notes published on GitHub Releases","Project retrospective scheduled")
        }
    ) | ForEach-Object {
        $c = $_
        $cbody = Build-IssueBody -Problem $c.Problem -InScope @("Implement as described") -OutScope @("Post-2.0.0 scope") -AcItems $c.AcItems `
            -DepsMilestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off" `
            -DepsIssues @("Epic #$epicNum","Phase 8 epic must be complete","Code Freeze Gate must be closed")
        $cbody += "`n`n---`n_Part of epic #${epicNum}: [Epic] Final Deployment and Sign-off (Release 2.0.0)_`n"
        $cbody += "_**Version reference:** This issue is part of the **release 2.0.0** deployment and sign-off process._`n"
        New-GhIssue -Title $c.Title -Labels $c.Labels -Body $cbody -Milestone $ms
        Start-Sleep -Milliseconds 400
    }
}

# ===========================================================================
# VERIFICATION CHECKLIST
# ===========================================================================
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Setup complete! Verification checklist:" -ForegroundColor Cyan
Write-Host "  Milestones created: $($milestoneMap.Count) (expected 13)" -ForegroundColor $(if ($milestoneMap.Count -eq 13) { "Green" } else { "Red" })

$freezeMs = $milestoneMap.Keys | Where-Object { $_ -match "Freeze" }
Write-Host "  Freeze milestones: $($freezeMs -join ', ')" -ForegroundColor $(if ($freezeMs.Count -ge 2) { "Green" } else { "Red" })

$auditMs = $milestoneMap.Keys | Where-Object { $_ -match "Audit" }
$pocMs = $milestoneMap.Keys | Where-Object { $_ -match "PoC" }
Write-Host "  Audit milestone (M6) after PoC (M5): $($auditMs -join ',') > $($pocMs -join ',')" -ForegroundColor Green

$finalMs = $milestoneMap.Keys | Where-Object { $_ -match "2\.0\.0 Production" }
Write-Host "  Final milestone (2027-03-10): $($finalMs -join ', ')" -ForegroundColor $(if ($finalMs) { "Green" } else { "Red" })
Write-Host "============================================================" -ForegroundColor Cyan
