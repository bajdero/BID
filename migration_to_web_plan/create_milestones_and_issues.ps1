$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw "GitHub CLI (gh) is not installed."
}

gh auth status | Out-Null

$repo = gh repo view --json nameWithOwner --jq ".nameWithOwner"
if (-not $repo) {
  throw "Cannot resolve repository from current folder. Run this script from repo root."
}

$owner, $name = $repo -split "/"
Write-Host "Repository: $owner/$name"

$labels = @(
  @{ n = "type:epic"; c = "5319E7"; d = "Epic level planning item" },
  @{ n = "type:feature"; c = "1D76DB"; d = "Feature implementation" },
  @{ n = "type:task"; c = "0E8A16"; d = "General task" },
  @{ n = "type:test"; c = "FBCA04"; d = "Testing work item" },
  @{ n = "type:infra"; c = "0052CC"; d = "Infrastructure or DevOps" },
  @{ n = "type:audit"; c = "B60205"; d = "Architecture or implementation audit" },
  @{ n = "type:release"; c = "D93F0B"; d = "Release governance item" },
  @{ n = "priority:p0"; c = "B60205"; d = "Critical priority" },
  @{ n = "priority:p1"; c = "D93F0B"; d = "High priority" },
  @{ n = "priority:p2"; c = "FBCA04"; d = "Normal priority" },
  @{ n = "area:backend"; c = "0366D6"; d = "Backend area" },
  @{ n = "area:frontend"; c = "1D76DB"; d = "Frontend area" },
  @{ n = "area:devops"; c = "0052CC"; d = "DevOps area" },
  @{ n = "area:qa"; c = "0E8A16"; d = "Quality assurance area" }
)

foreach ($l in $labels) {
  & gh label create $l.n --color $l.c --description $l.d --force | Out-Null
}
Write-Host "Labels synced."

$milestones = @(
  @{ t = "M1 - Backend API Extraction (Phase 1)"; d = "2026-05-31"; desc = "FastAPI layer, models, routers, auth baseline, API tests start" },
  @{ t = "M2 - WebSocket Real-Time Layer (Phase 2)"; d = "2026-06-21"; desc = "WS manager, channels, processing and monitor broadcasts" },
  @{ t = "M3 - Frontend Shell (Phase 3)"; d = "2026-07-19"; desc = "Next.js scaffold, auth flow, dashboard shell, API client" },
  @{ t = "M4 - Core UI Components (Phase 4)"; d = "2026-09-06"; desc = "Source tree, details panel, preview integration" },
  @{ t = "M5 - PoC Release 2.0.0-rc1"; d = "2026-09-20"; desc = "PoC release candidate for first web release line 2.0.0" },
  @{ t = "M6 - Architecture and Implementation Audit"; d = "2026-10-04"; desc = "Post-PoC architecture and implementation audit" },
  @{ t = "M7 - Processing Dashboard (Phase 5)"; d = "2026-11-08"; desc = "Processing dashboard and profile editor" },
  @{ t = "M8 - FileBrowser + Vector Search (Phase 6)"; d = "2026-12-06"; desc = "FileBrowser auth proxy and vector index integration" },
  @{ t = "M9 - Event System UI (Phase 7)"; d = "2027-01-10"; desc = "Event source management, timelines, assignments" },
  @{ t = "M10 - Feature Freeze"; d = "2027-01-20"; desc = "No new features after this point" },
  @{ t = "M11 - Test/Deploy Readiness (Phase 8)"; d = "2027-02-20"; desc = "Coverage, CI/CD, production deployment readiness" },
  @{ t = "M12 - Code Freeze"; d = "2027-02-24"; desc = "Only release-blocker fixes allowed" },
  @{ t = "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"; d = "2027-03-10"; desc = "Production deployment and final sign-off for 2.0.0" }
)

$existingMilestones = gh api "repos/$owner/$name/milestones?state=all&per_page=100" | ConvertFrom-Json
foreach ($m in $milestones) {
  $exists = $existingMilestones | Where-Object { $_.title -eq $m.t }
  if (-not $exists) {
    & gh api -X POST "repos/$owner/$name/milestones" `
      -f title="$($m.t)" `
      -f state="open" `
      -f due_on="$($m.d)T23:59:59Z" `
      -f description="$($m.desc)" | Out-Null
    Write-Host "Created milestone: $($m.t)"
  }
  else {
    Write-Host "Milestone exists: $($m.t)"
  }
}

$script:allIssues = gh issue list --state all --limit 1000 --json number,title | ConvertFrom-Json

function New-StandardBody {
  param(
    [string]$Problem,
    [string]$ScopeIn,
    [string]$ScopeOut,
    [string]$Dependencies
  )

@"
Problem statement
$Problem

Scope in
- $ScopeIn

Scope out
- $ScopeOut

Acceptance criteria
- [ ] Requirements implemented
- [ ] Tests added or updated
- [ ] Documentation updated
- [ ] Risks and assumptions recorded

Dependencies
- $Dependencies

Definition of done
- [ ] Merged to main branch
- [ ] CI green
- [ ] Milestone target met
"@
}

function New-IssueIfMissing {
  param(
    [string]$Title,
    [string]$Milestone,
    [string[]]$Labels,
    [string]$Body
  )

  $exists = $script:allIssues | Where-Object { $_.title -eq $Title }
  if ($exists) {
    Write-Host "Issue exists: $Title"
    return
  }

  $args = @("issue", "create", "--title", $Title, "--body", $Body, "--milestone", $Milestone)
  foreach ($label in $Labels) {
    $args += @("--label", $label)
  }

  & gh @args | Out-Null
  Write-Host "Created issue: $Title"

  $script:allIssues = gh issue list --state all --limit 1000 --json number,title | ConvertFrom-Json
}

New-IssueIfMissing `
  -Title "Epic: Phase 1 - Backend API Extraction" `
  -Milestone "M1 - Backend API Extraction (Phase 1)" `
  -Labels @("type:epic", "priority:p1", "area:backend") `
  -Body (New-StandardBody -Problem "Expose existing BID logic via FastAPI without modifying core bid package." -ScopeIn "API app, models, routers, deps, auth baseline." -ScopeOut "Core business logic rewrite." -Dependencies "Milestone M1")

New-IssueIfMissing `
  -Title "Epic: Phase 2 - WebSocket Real-Time Layer" `
  -Milestone "M2 - WebSocket Real-Time Layer (Phase 2)" `
  -Labels @("type:epic", "priority:p1", "area:backend") `
  -Body (New-StandardBody -Problem "Replace polling behavior with WebSocket real-time push updates." -ScopeIn "WS manager, route, processing and monitor broadcasts." -ScopeOut "Frontend redesign." -Dependencies "Milestone M2; depends on Phase 1")

New-IssueIfMissing `
  -Title "Epic: Phase 3 - Frontend Shell" `
  -Milestone "M3 - Frontend Shell (Phase 3)" `
  -Labels @("type:epic", "priority:p1", "area:frontend") `
  -Body (New-StandardBody -Problem "Create Next.js shell with auth and project navigation." -ScopeIn "App router shell, login, middleware, dashboard layout." -ScopeOut "Full business UI features." -Dependencies "Milestone M3")

New-IssueIfMissing `
  -Title "Epic: Phase 4 - Core UI Components" `
  -Milestone "M4 - Core UI Components (Phase 4)" `
  -Labels @("type:epic", "priority:p1", "area:frontend") `
  -Body (New-StandardBody -Problem "Implement source tree, details panel, and image preview." -ScopeIn "Core components and source page integration." -ScopeOut "Processing dashboard and events UI." -Dependencies "Milestone M4; depends on Phase 3")

New-IssueIfMissing `
  -Title "Epic: PoC Release Readiness (2.0.0-rc1)" `
  -Milestone "M5 - PoC Release 2.0.0-rc1" `
  -Labels @("type:epic", "type:release", "priority:p0", "area:qa") `
  -Body (New-StandardBody -Problem "Deliver first web PoC release candidate for 2.0.0 line." -ScopeIn "End-to-end demo path and PoC quality gates." -ScopeOut "Production hardening." -Dependencies "Milestone M5; depends on M1-M4")

New-IssueIfMissing `
  -Title "Epic: Post-PoC Architecture and Implementation Audit" `
  -Milestone "M6 - Architecture and Implementation Audit" `
  -Labels @("type:epic", "type:audit", "priority:p0", "area:backend", "area:frontend") `
  -Body (New-StandardBody -Problem "Run architecture and implementation audit after PoC completion." -ScopeIn "Architecture, implementation quality, risks, remediation backlog." -ScopeOut "New feature development." -Dependencies "Milestone M6; starts only after M5 completion")

New-IssueIfMissing `
  -Title "Epic: Phase 5 - Processing Dashboard" `
  -Milestone "M7 - Processing Dashboard (Phase 5)" `
  -Labels @("type:epic", "priority:p1", "area:frontend") `
  -Body (New-StandardBody -Problem "Build processing dashboard with real-time progress." -ScopeIn "Processing controls, progress state, result list." -ScopeOut "Event management and file browser." -Dependencies "Milestone M7; depends on M2 and M4")

New-IssueIfMissing `
  -Title "Epic: Phase 6 - FileBrowser + Vector Search Integration" `
  -Milestone "M8 - FileBrowser + Vector Search (Phase 6)" `
  -Labels @("type:epic", "priority:p1", "area:devops", "area:backend", "area:frontend") `
  -Body (New-StandardBody -Problem "Integrate FileBrowser and vector index service with shared auth." -ScopeIn "Docker compose services, proxy auth, files page embed, vector wiring." -ScopeOut "Advanced search UX." -Dependencies "Milestone M8")

New-IssueIfMissing `
  -Title "Epic: Phase 7 - Event System UI" `
  -Milestone "M9 - Event System UI (Phase 7)" `
  -Labels @("type:epic", "priority:p1", "area:frontend") `
  -Body (New-StandardBody -Problem "Implement event source management, schedule timeline, and assignments." -ScopeIn "Events page and components." -ScopeOut "Release operations." -Dependencies "Milestone M9; depends on Phase 4")

New-IssueIfMissing `
  -Title "Epic: Phase 8 - Testing and Deployment" `
  -Milestone "M11 - Test/Deploy Readiness (Phase 8)" `
  -Labels @("type:epic", "priority:p0", "area:qa", "area:devops") `
  -Body (New-StandardBody -Problem "Complete API and E2E testing and deployment readiness for release 2.0.0." -ScopeIn "Tests, CI/CD, Docker production config, docs." -ScopeOut "Net-new product features." -Dependencies "Milestone M11; depends on M1-M9")

New-IssueIfMissing `
  -Title "Epic: Release Hardening (Feature Freeze to Code Freeze)" `
  -Milestone "M10 - Feature Freeze" `
  -Labels @("type:epic", "type:release", "priority:p0", "area:qa") `
  -Body (New-StandardBody -Problem "Govern release hardening between feature freeze and code freeze." -ScopeIn "Defect burn-down, regression stabilization, release governance." -ScopeOut "Feature expansion." -Dependencies "Milestones M10-M12")

New-IssueIfMissing `
  -Title "Feature Freeze Gate - Enforce no new features after 2027-01-20" `
  -Milestone "M10 - Feature Freeze" `
  -Labels @("type:task", "type:release", "priority:p0", "area:qa") `
  -Body (New-StandardBody -Problem "Enforce feature freeze policy for release 2.0.0." -ScopeIn "Waiver process and freeze compliance checks." -ScopeOut "Normal feature intake." -Dependencies "Milestone M10")

New-IssueIfMissing `
  -Title "Code Freeze Gate - Allow only release blockers after 2027-02-24" `
  -Milestone "M12 - Code Freeze" `
  -Labels @("type:task", "type:release", "priority:p0", "area:qa") `
  -Body (New-StandardBody -Problem "Enforce code freeze policy before production release 2.0.0." -ScopeIn "Exception handling, rollback plan, targeted regressions." -ScopeOut "Routine code changes." -Dependencies "Milestone M12")

New-IssueIfMissing `
  -Title "Go-Live Gate - Production deployment validation and rollback readiness" `
  -Milestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off" `
  -Labels @("type:task", "type:release", "priority:p0", "area:devops", "area:qa") `
  -Body (New-StandardBody -Problem "Ensure final production go-live readiness for release 2.0.0 by 2027-03-10." -ScopeIn "Deployment validation, rollback rehearsal, stakeholder sign-off." -ScopeOut "Post-release enhancement backlog." -Dependencies "Milestone M13; depends on M11 and M12")

New-IssueIfMissing `
  -Title "Epic: Final Deployment and Sign-off (Release 2.0.0)" `
  -Milestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off" `
  -Labels @("type:epic", "type:release", "priority:p0", "area:devops", "area:qa") `
  -Body (New-StandardBody -Problem "Deliver and sign off first web production release 2.0.0." -ScopeIn "Final release execution and closure activities." -ScopeOut "Future release planning." -Dependencies "Milestone M13; audit and freeze gates complete")

$msCount = (gh api "repos/$owner/$name/milestones?state=all&per_page=100" | ConvertFrom-Json).Count

Write-Host ""
Write-Host "Verification"
Write-Host "Milestone count (expected 13): $msCount"
Write-Host "Freeze milestones: M10 and M12"
Write-Host "Audit after PoC: M5 due 2026-09-20, M6 due 2026-10-04"
Write-Host "Final due date: M13 due 2027-03-10"
