#!/usr/bin/env bash
# 02_milestones.sh — Create all 13 milestones for BID web migration
# Uses gh api because gh milestone create is not available in all gh versions.
set -euo pipefail
REPO="bajdero/BID"

echo "=== Creating milestones for ${REPO} ==="

create_milestone() {
  local title="$1"
  local due="$2"
  local desc="$3"
  gh api "repos/${REPO}/milestones" \
    --method POST \
    --field "title=${title}" \
    --field "due_on=${due}T23:59:59Z" \
    --field "description=${desc}" \
    --silent && echo "  Created: ${title}" || echo "  Already exists (or error): ${title}"
}

create_milestone \
  "M1 - Backend API Extraction (Phase 1)" \
  "2026-05-31" \
  "REST API extraction from Python desktop core. Deliverables: FastAPI service, DB abstraction, auth, OpenAPI docs, unit tests."

create_milestone \
  "M2 - WebSocket Real-Time Layer (Phase 2)" \
  "2026-06-21" \
  "Real-time event streaming over WebSocket. Deliverables: WS server, event broadcast, progress streaming, reconnect, integration tests."

create_milestone \
  "M3 - Frontend Shell (Phase 3)" \
  "2026-07-19" \
  "React/TS scaffold with routing, auth, and layout. Deliverables: Vite project, routing, auth flow, AppShell, Zustand, CI/CD."

create_milestone \
  "M4 - Core UI Components (Phase 4)" \
  "2026-09-06" \
  "Primary interactive panels and wizards. Deliverables: project selector, export wizard, queue display, settings, toast, themes."

create_milestone \
  "M5 - PoC Release 2.0.0-rc1" \
  "2026-09-20" \
  "End-to-end PoC for stakeholder validation. Deliverables: integration, smoke tests, rc1 tag, staging deploy, demo."

create_milestone \
  "M6 - Architecture and Implementation Audit" \
  "2026-10-04" \
  "Post-PoC audit — starts only after M5 is complete. Covers backend, frontend, OWASP security, performance baseline, remediation plan."

create_milestone \
  "M7 - Processing Dashboard (Phase 5)" \
  "2026-11-08" \
  "Batch processing control centre. Deliverables: status view, real-time visualisation, history log, metrics, error/retry panel."

create_milestone \
  "M8 - FileBrowser + Vector Search (Phase 6)" \
  "2026-12-06" \
  "Web file browser and vector image search. Deliverables: directory tree, image preview, vector search API, results grid, metadata editor."

create_milestone \
  "M9 - Event System UI (Phase 7)" \
  "2027-01-10" \
  "Web UI for the BID event subsystem. Deliverables: real-time event log, filtering, notification prefs, audit trail."

create_milestone \
  "M10 - Feature Freeze" \
  "2027-01-20" \
  "GATE: No new features may be merged after 2027-01-20."

create_milestone \
  "M11 - Test/Deploy Readiness (Phase 8)" \
  "2027-02-20" \
  "E2E tests, containerisation, production infrastructure. Deliverables: Playwright suite, k6 load tests, Docker, k8s config, health checks, runbook."

create_milestone \
  "M12 - Code Freeze" \
  "2027-02-24" \
  "GATE: Only release-blocker fixes may be merged after 2027-02-24."

create_milestone \
  "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off" \
  "2027-03-10" \
  "Production go-live and formal release 2.0.0 sign-off. Hard deadline: 2027-03-10."

echo "=== Milestones created (13 total) ==="
echo ""
echo "Verify at: https://github.com/${REPO}/milestones"
