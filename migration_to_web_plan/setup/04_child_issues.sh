#!/usr/bin/env bash
# 04_child_issues.sh — Create all child issues for BID web migration
# Run after 03_epics.sh.
set -euo pipefail
REPO="bajdero/BID"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BODIES="${DIR}/bodies"

echo "=== Creating child issues for ${REPO} ==="

# ════════════════════════════════════════════════════════
# PHASE 1 — Backend API Extraction  (M1)
# ════════════════════════════════════════════════════════
echo "--- Phase 1 ---"

gh issue create --repo "${REPO}" \
  --title "P1-01: Design REST API specification (OpenAPI 3.0) for BID operations" \
  --body-file "${BODIES}/p1_01_api_spec.md" \
  --label "type:task,area:backend,priority:p1" \
  --milestone "M1 - Backend API Extraction (Phase 1)"

gh issue create --repo "${REPO}" \
  --title "P1-02: Extract image processing pipeline to FastAPI service" \
  --body-file "${BODIES}/p1_02_fastapi_service.md" \
  --label "type:feature,area:backend,priority:p0" \
  --milestone "M1 - Backend API Extraction (Phase 1)"

gh issue create --repo "${REPO}" \
  --title "P1-03: Implement project and session management API endpoints" \
  --body-file "${BODIES}/p1_03_project_api.md" \
  --label "type:feature,area:backend,priority:p0" \
  --milestone "M1 - Backend API Extraction (Phase 1)"

gh issue create --repo "${REPO}" \
  --title "P1-04: Add JWT authentication and authorisation middleware" \
  --body-file "${BODIES}/p1_04_auth.md" \
  --label "type:feature,area:backend,priority:p1" \
  --milestone "M1 - Backend API Extraction (Phase 1)"

gh issue create --repo "${REPO}" \
  --title "P1-05: Create database abstraction layer (SQLite to PostgreSQL)" \
  --body-file "${BODIES}/p1_05_db_layer.md" \
  --label "type:infra,area:backend,priority:p1" \
  --milestone "M1 - Backend API Extraction (Phase 1)"

gh issue create --repo "${REPO}" \
  --title "P1-06: Write unit tests for all API endpoints (80% coverage)" \
  --body-file "${BODIES}/p1_06_api_tests.md" \
  --label "type:test,area:backend,priority:p1" \
  --milestone "M1 - Backend API Extraction (Phase 1)"

echo "  Phase 1: 6 issues created"

# ════════════════════════════════════════════════════════
# PHASE 2 — WebSocket Real-Time Layer  (M2)
# ════════════════════════════════════════════════════════
echo "--- Phase 2 ---"

gh issue create --repo "${REPO}" \
  --title "P2-01: Implement WebSocket server (FastAPI + asyncio)" \
  --body-file "${BODIES}/p2_01_ws_server.md" \
  --label "type:feature,area:backend,priority:p0" \
  --milestone "M2 - WebSocket Real-Time Layer (Phase 2)"

gh issue create --repo "${REPO}" \
  --title "P2-02: Adapt bid/events system to broadcast over WebSocket" \
  --body-file "${BODIES}/p2_02_event_broadcast.md" \
  --label "type:feature,area:backend,priority:p0" \
  --milestone "M2 - WebSocket Real-Time Layer (Phase 2)"

gh issue create --repo "${REPO}" \
  --title "P2-03: Stream per-file and batch processing progress to clients" \
  --body-file "${BODIES}/p2_03_progress_stream.md" \
  --label "type:feature,area:backend,priority:p1" \
  --milestone "M2 - WebSocket Real-Time Layer (Phase 2)"

gh issue create --repo "${REPO}" \
  --title "P2-04: Add heartbeat and automatic client reconnect mechanism" \
  --body-file "${BODIES}/p2_04_heartbeat.md" \
  --label "type:feature,area:backend,priority:p1" \
  --milestone "M2 - WebSocket Real-Time Layer (Phase 2)"

gh issue create --repo "${REPO}" \
  --title "P2-05: Write WebSocket integration tests" \
  --body-file "${BODIES}/p2_05_ws_tests.md" \
  --label "type:test,area:backend,priority:p1" \
  --milestone "M2 - WebSocket Real-Time Layer (Phase 2)"

echo "  Phase 2: 5 issues created"

# ════════════════════════════════════════════════════════
# PHASE 3 — Frontend Shell  (M3)
# ════════════════════════════════════════════════════════
echo "--- Phase 3 ---"

gh issue create --repo "${REPO}" \
  --title "P3-01: Bootstrap React TypeScript Vite project" \
  --body-file "${BODIES}/p3_01_react_bootstrap.md" \
  --label "type:infra,area:frontend,priority:p0" \
  --milestone "M3 - Frontend Shell (Phase 3)"

gh issue create --repo "${REPO}" \
  --title "P3-02: Configure client-side routing (React Router v6)" \
  --body-file "${BODIES}/p3_02_routing.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M3 - Frontend Shell (Phase 3)"

gh issue create --repo "${REPO}" \
  --title "P3-03: Implement authentication flow (login, session, logout)" \
  --body-file "${BODIES}/p3_03_auth_ui.md" \
  --label "type:feature,area:frontend,priority:p0" \
  --milestone "M3 - Frontend Shell (Phase 3)"

gh issue create --repo "${REPO}" \
  --title "P3-04: Create base layout components (AppShell, Sidebar, Header)" \
  --body-file "${BODIES}/p3_04_layout.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M3 - Frontend Shell (Phase 3)"

gh issue create --repo "${REPO}" \
  --title "P3-05: Set up state management (Zustand) and API client" \
  --body-file "${BODIES}/p3_05_state_api_client.md" \
  --label "type:infra,area:frontend,priority:p1" \
  --milestone "M3 - Frontend Shell (Phase 3)"

gh issue create --repo "${REPO}" \
  --title "P3-06: Configure GitHub Actions CI/CD pipeline for frontend" \
  --body-file "${BODIES}/p3_06_cicd.md" \
  --label "type:infra,area:devops,priority:p1" \
  --milestone "M3 - Frontend Shell (Phase 3)"

echo "  Phase 3: 6 issues created"

# ════════════════════════════════════════════════════════
# PHASE 4 — Core UI Components  (M4)
# ════════════════════════════════════════════════════════
echo "--- Phase 4 ---"

gh issue create --repo "${REPO}" \
  --title "P4-01: Project/session selector component" \
  --body-file "${BODIES}/p4_001_project_session_selector_compo.md" \
  --label "type:feature,area:frontend,priority:p0" \
  --milestone "M4 - Core UI Components (Phase 4)"

gh issue create --repo "${REPO}" \
  --title "P4-02: Export profile configuration wizard" \
  --body-file "${BODIES}/p4_002_export_profile_configuration_w.md" \
  --label "type:feature,area:frontend,priority:p0" \
  --milestone "M4 - Core UI Components (Phase 4)"

gh issue create --repo "${REPO}" \
  --title "P4-03: Image processing queue display with live status" \
  --body-file "${BODIES}/p4_003_image_processing_queue_display.md" \
  --label "type:feature,area:frontend,priority:p0" \
  --milestone "M4 - Core UI Components (Phase 4)"

gh issue create --repo "${REPO}" \
  --title "P4-04: Settings and preferences panel" \
  --body-file "${BODIES}/p4_004_settings_and_preferences_panel.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M4 - Core UI Components (Phase 4)"

gh issue create --repo "${REPO}" \
  --title "P4-05: Toast notification system" \
  --body-file "${BODIES}/p4_005_toast_notification_system.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M4 - Core UI Components (Phase 4)"

gh issue create --repo "${REPO}" \
  --title "P4-06: Theme provider — dark and light mode" \
  --body-file "${BODIES}/p4_006_theme_provider_dark_light.md" \
  --label "type:feature,area:frontend,priority:p2" \
  --milestone "M4 - Core UI Components (Phase 4)"

echo "  Phase 4: 6 issues created"

# ════════════════════════════════════════════════════════
# PoC Release  (M5)
# ════════════════════════════════════════════════════════
echo "--- PoC Release ---"

gh issue create --repo "${REPO}" \
  --title "POC-01: End-to-end integration — connect frontend to backend API" \
  --body-file "${BODIES}/poc_01_integration.md" \
  --label "type:task,area:backend,priority:p0" \
  --milestone "M5 - PoC Release 2.0.0-rc1"

gh issue create --repo "${REPO}" \
  --title "POC-02: PoC smoke test suite — critical user journey" \
  --body-file "${BODIES}/poc_02_smoke_test.md" \
  --label "type:test,area:qa,priority:p0" \
  --milestone "M5 - PoC Release 2.0.0-rc1"

gh issue create --repo "${REPO}" \
  --title "POC-03: Tag and publish release package 2.0.0-rc1" \
  --body-file "${BODIES}/poc_03_rc1_tag.md" \
  --label "type:release,priority:p0" \
  --milestone "M5 - PoC Release 2.0.0-rc1"

gh issue create --repo "${REPO}" \
  --title "POC-04: Deploy 2.0.0-rc1 to staging environment" \
  --body-file "${BODIES}/poc_04_staging_deploy.md" \
  --label "type:infra,area:devops,priority:p0" \
  --milestone "M5 - PoC Release 2.0.0-rc1"

gh issue create --repo "${REPO}" \
  --title "POC-05: Conduct PoC stakeholder demo and collect feedback" \
  --body-file "${BODIES}/poc_05_demo.md" \
  --label "type:task,priority:p1" \
  --milestone "M5 - PoC Release 2.0.0-rc1"

echo "  PoC: 5 issues created"

# ════════════════════════════════════════════════════════
# Audit  (M6)
# ════════════════════════════════════════════════════════
echo "--- Audit ---"

gh issue create --repo "${REPO}" \
  --title "AUD-01: Backend API code-quality and architecture review" \
  --body-file "${BODIES}/aud_01_backend_audit.md" \
  --label "type:audit,area:backend,priority:p0" \
  --milestone "M6 - Architecture and Implementation Audit"

gh issue create --repo "${REPO}" \
  --title "AUD-02: Frontend architecture and component-design review" \
  --body-file "${BODIES}/aud_02_frontend_audit.md" \
  --label "type:audit,area:frontend,priority:p0" \
  --milestone "M6 - Architecture and Implementation Audit"

gh issue create --repo "${REPO}" \
  --title "AUD-03: Security audit — OWASP Top 10 analysis" \
  --body-file "${BODIES}/aud_03_security.md" \
  --label "type:audit,area:backend,priority:p0" \
  --milestone "M6 - Architecture and Implementation Audit"

gh issue create --repo "${REPO}" \
  --title "AUD-04: Performance baseline measurement and bottleneck report" \
  --body-file "${BODIES}/aud_04_performance.md" \
  --label "type:audit,priority:p1" \
  --milestone "M6 - Architecture and Implementation Audit"

gh issue create --repo "${REPO}" \
  --title "AUD-05: Document audit findings and publish remediation plan" \
  --body-file "${BODIES}/aud_05_remediation_plan.md" \
  --label "type:audit,priority:p0" \
  --milestone "M6 - Architecture and Implementation Audit"

echo "  Audit: 5 issues created"

# ════════════════════════════════════════════════════════
# PHASE 5 — Processing Dashboard  (M7)
# ════════════════════════════════════════════════════════
echo "--- Phase 5 ---"

gh issue create --repo "${REPO}" \
  --title "P5-01: Batch processing status view (start, pause, cancel)" \
  --body-file "${BODIES}/p5_01_batch_view.md" \
  --label "type:feature,area:frontend,priority:p0" \
  --milestone "M7 - Processing Dashboard (Phase 5)"

gh issue create --repo "${REPO}" \
  --title "P5-02: Real-time progress visualisation via WebSocket" \
  --body-file "${BODIES}/p5_02_realtime_viz.md" \
  --label "type:feature,area:frontend,priority:p0" \
  --milestone "M7 - Processing Dashboard (Phase 5)"

gh issue create --repo "${REPO}" \
  --title "P5-03: Processing history log viewer with search and filter" \
  --body-file "${BODIES}/p5_03_history_log.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M7 - Processing Dashboard (Phase 5)"

gh issue create --repo "${REPO}" \
  --title "P5-04: Metrics and statistics dashboard" \
  --body-file "${BODIES}/p5_04_metrics.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M7 - Processing Dashboard (Phase 5)"

gh issue create --repo "${REPO}" \
  --title "P5-05: Error details panel with retry action" \
  --body-file "${BODIES}/p5_05_error_retry.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M7 - Processing Dashboard (Phase 5)"

echo "  Phase 5: 5 issues created"

# ════════════════════════════════════════════════════════
# PHASE 6 — FileBrowser + Vector Search  (M8)
# ════════════════════════════════════════════════════════
echo "--- Phase 6 ---"

gh issue create --repo "${REPO}" \
  --title "P6-01: File browser component with lazy-loaded directory tree" \
  --body-file "${BODIES}/p6_01_filebrowser.md" \
  --label "type:feature,area:frontend,priority:p0" \
  --milestone "M8 - FileBrowser + Vector Search (Phase 6)"

gh issue create --repo "${REPO}" \
  --title "P6-02: Image preview panel with EXIF metadata display" \
  --body-file "${BODIES}/p6_02_preview.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M8 - FileBrowser + Vector Search (Phase 6)"

gh issue create --repo "${REPO}" \
  --title "P6-03: Backend vector search API endpoint (image embeddings)" \
  --body-file "${BODIES}/p6_03_vector_search_api.md" \
  --label "type:feature,area:backend,priority:p1" \
  --milestone "M8 - FileBrowser + Vector Search (Phase 6)"

gh issue create --repo "${REPO}" \
  --title "P6-04: Search results grid with similarity score" \
  --body-file "${BODIES}/p6_04_search_results.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M8 - FileBrowser + Vector Search (Phase 6)"

gh issue create --repo "${REPO}" \
  --title "P6-05: Inline metadata editor (author, date, custom EXIF fields)" \
  --body-file "${BODIES}/p6_05_metadata_editor.md" \
  --label "type:feature,area:frontend,priority:p2" \
  --milestone "M8 - FileBrowser + Vector Search (Phase 6)"

echo "  Phase 6: 5 issues created"

# ════════════════════════════════════════════════════════
# PHASE 7 — Event System UI  (M9)
# ════════════════════════════════════════════════════════
echo "--- Phase 7 ---"

gh issue create --repo "${REPO}" \
  --title "P7-01: Real-time event log viewer (WebSocket-powered)" \
  --body-file "${BODIES}/p7_01_event_log.md" \
  --label "type:feature,area:frontend,priority:p0" \
  --milestone "M9 - Event System UI (Phase 7)"

gh issue create --repo "${REPO}" \
  --title "P7-02: Event filtering by type, severity, and date range" \
  --body-file "${BODIES}/p7_02_event_filter.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M9 - Event System UI (Phase 7)"

gh issue create --repo "${REPO}" \
  --title "P7-03: Event notification preferences (in-app and email)" \
  --body-file "${BODIES}/p7_03_notification_prefs.md" \
  --label "type:feature,area:frontend,priority:p2" \
  --milestone "M9 - Event System UI (Phase 7)"

gh issue create --repo "${REPO}" \
  --title "P7-04: Audit trail and activity timeline display" \
  --body-file "${BODIES}/p7_04_audit_trail.md" \
  --label "type:feature,area:frontend,priority:p1" \
  --milestone "M9 - Event System UI (Phase 7)"

echo "  Phase 7: 4 issues created"

# ════════════════════════════════════════════════════════
# PHASE 8 — Test/Deploy Readiness  (M11)
# ════════════════════════════════════════════════════════
echo "--- Phase 8 ---"

gh issue create --repo "${REPO}" \
  --title "P8-01: End-to-end test suite (Playwright) — all critical paths" \
  --body-file "${BODIES}/p8_01_e2e_tests.md" \
  --label "type:test,area:qa,priority:p0" \
  --milestone "M11 - Test/Deploy Readiness (Phase 8)"

gh issue create --repo "${REPO}" \
  --title "P8-02: Load and performance testing (k6) against baseline" \
  --body-file "${BODIES}/p8_02_load_tests.md" \
  --label "type:test,area:qa,priority:p0" \
  --milestone "M11 - Test/Deploy Readiness (Phase 8)"

gh issue create --repo "${REPO}" \
  --title "P8-03: Docker containerisation and docker-compose for dev" \
  --body-file "${BODIES}/p8_03_docker.md" \
  --label "type:infra,area:devops,priority:p0" \
  --milestone "M11 - Test/Deploy Readiness (Phase 8)"

gh issue create --repo "${REPO}" \
  --title "P8-04: Kubernetes / production infrastructure configuration" \
  --body-file "${BODIES}/p8_04_k8s_infra.md" \
  --label "type:infra,area:devops,priority:p0" \
  --milestone "M11 - Test/Deploy Readiness (Phase 8)"

gh issue create --repo "${REPO}" \
  --title "P8-05: Health check endpoints and observability (metrics + tracing)" \
  --body-file "${BODIES}/p8_05_monitoring.md" \
  --label "type:infra,area:devops,priority:p1" \
  --milestone "M11 - Test/Deploy Readiness (Phase 8)"

gh issue create --repo "${REPO}" \
  --title "P8-06: Rollback procedures and operations runbook" \
  --body-file "${BODIES}/p8_06_runbook.md" \
  --label "type:task,area:devops,priority:p0" \
  --milestone "M11 - Test/Deploy Readiness (Phase 8)"

echo "  Phase 8: 6 issues created"

# ════════════════════════════════════════════════════════
# Final Release  (M13)
# ════════════════════════════════════════════════════════
echo "--- Final Release (2.0.0) ---"

gh issue create --repo "${REPO}" \
  --title "REL-01: Execute production deployment of release 2.0.0" \
  --body-file "${BODIES}/rel_01_prod_deploy.md" \
  --label "type:release,area:devops,priority:p0" \
  --milestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"

gh issue create --repo "${REPO}" \
  --title "REL-03: Post-deployment smoke testing in production (release 2.0.0)" \
  --body-file "${BODIES}/rel_03_smoke_prod.md" \
  --label "type:test,area:qa,priority:p0" \
  --milestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"

gh issue create --repo "${REPO}" \
  --title "REL-04: Final stakeholder sign-off for release 2.0.0" \
  --body-file "${BODIES}/rel_04_signoff.md" \
  --label "type:task,priority:p0" \
  --milestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"

gh issue create --repo "${REPO}" \
  --title "REL-05: Create and publish GitHub release 2.0.0 with full changelog" \
  --body-file "${BODIES}/rel_05_github_release.md" \
  --label "type:release,priority:p0" \
  --milestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"

echo "  Final Release: 4 issues created"

echo ""
echo "=== Child issues created ==="
echo "  Phase 1:  6"
echo "  Phase 2:  5"
echo "  Phase 3:  6"
echo "  Phase 4:  6"
echo "  PoC:      5"
echo "  Audit:    5"
echo "  Phase 5:  5"
echo "  Phase 6:  5"
echo "  Phase 7:  4"
echo "  Phase 8:  6"
echo "  Release:  4"
echo "  ─────────"
echo "  TOTAL:   57 child issues"
echo ""
echo "Verify at: https://github.com/${REPO}/issues"
