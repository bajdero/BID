#!/usr/bin/env bash
# 03_epics.sh — Create 12 epic issues and 3 freeze gate issues for BID web migration
# Run after 01_labels.sh and 02_milestones.sh.
# NOTE: Record the issue numbers printed here; you will need them for 04_child_issues.sh.
set -euo pipefail
REPO="bajdero/BID"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BODIES="${DIR}/bodies"

echo "=== Creating epic issues for ${REPO} ==="

# ─────────── E1 — Phase 1 ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Phase 1 — Backend API Extraction" \
  --body-file "${BODIES}/epic_phase1.md" \
  --label "type:epic,area:backend,priority:p0" \
  --milestone "M1 - Backend API Extraction (Phase 1)"
echo "  Created E1"

# ─────────── E2 — Phase 2 ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Phase 2 — WebSocket Real-Time Layer" \
  --body-file "${BODIES}/epic_phase2.md" \
  --label "type:epic,area:backend,priority:p0" \
  --milestone "M2 - WebSocket Real-Time Layer (Phase 2)"
echo "  Created E2"

# ─────────── E3 — Phase 3 ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Phase 3 — Frontend Shell" \
  --body-file "${BODIES}/epic_phase3.md" \
  --label "type:epic,area:frontend,priority:p0" \
  --milestone "M3 - Frontend Shell (Phase 3)"
echo "  Created E3"

# ─────────── E4 — Phase 4 ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Phase 4 — Core UI Components" \
  --body-file "${BODIES}/epic_phase4.md" \
  --label "type:epic,area:frontend,priority:p0" \
  --milestone "M4 - Core UI Components (Phase 4)"
echo "  Created E4"

# ─────────── E5 — PoC ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] PoC Release Readiness (2.0.0-rc1)" \
  --body-file "${BODIES}/epic_poc.md" \
  --label "type:epic,type:release,priority:p0" \
  --milestone "M5 - PoC Release 2.0.0-rc1"
echo "  Created E5"

# ─────────── E6 — Audit ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Post-PoC Architecture and Implementation Audit" \
  --body-file "${BODIES}/epic_audit.md" \
  --label "type:epic,type:audit,priority:p0" \
  --milestone "M6 - Architecture and Implementation Audit"
echo "  Created E6"

# ─────────── E7 — Phase 5 ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Phase 5 — Processing Dashboard" \
  --body-file "${BODIES}/epic_phase5.md" \
  --label "type:epic,area:frontend,priority:p0" \
  --milestone "M7 - Processing Dashboard (Phase 5)"
echo "  Created E7"

# ─────────── E8 — Phase 6 ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Phase 6 — FileBrowser + Vector Search" \
  --body-file "${BODIES}/epic_phase6.md" \
  --label "type:epic,area:frontend,priority:p0" \
  --milestone "M8 - FileBrowser + Vector Search (Phase 6)"
echo "  Created E8"

# ─────────── E9 — Phase 7 ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Phase 7 — Event System UI" \
  --body-file "${BODIES}/epic_phase7.md" \
  --label "type:epic,area:frontend,priority:p0" \
  --milestone "M9 - Event System UI (Phase 7)"
echo "  Created E9"

# ─────────── E10 — Release Hardening ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Release Hardening (Feature Freeze to Code Freeze)" \
  --body-file "${BODIES}/epic_hardening.md" \
  --label "type:epic,type:release,priority:p0" \
  --milestone "M10 - Feature Freeze"
echo "  Created E10"

# ─────────── E11 — Phase 8 ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Phase 8 — Test/Deploy Readiness" \
  --body-file "${BODIES}/epic_phase8.md" \
  --label "type:epic,area:qa,priority:p0" \
  --milestone "M11 - Test/Deploy Readiness (Phase 8)"
echo "  Created E11"

# ─────────── E12 — Final Release ───────────
gh issue create \
  --repo "${REPO}" \
  --title "[Epic] Final Deployment and Sign-off (Release 2.0.0)" \
  --body-file "${BODIES}/epic_final_release.md" \
  --label "type:epic,type:release,priority:p0" \
  --milestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"
echo "  Created E12"

echo ""
echo "=== Creating freeze gate issues ==="

# ─────────── G1 — Feature Freeze Gate ───────────
gh issue create \
  --repo "${REPO}" \
  --title "Feature Freeze Gate — no new features after 2027-01-20" \
  --body-file "${BODIES}/gate_feature_freeze.md" \
  --label "type:release,priority:p0" \
  --milestone "M10 - Feature Freeze"
echo "  Created G1 (Feature Freeze Gate)"

# ─────────── G2 — Code Freeze Gate ───────────
gh issue create \
  --repo "${REPO}" \
  --title "Code Freeze Gate — only release blockers after 2027-02-24" \
  --body-file "${BODIES}/gate_code_freeze.md" \
  --label "type:release,priority:p0" \
  --milestone "M12 - Code Freeze"
echo "  Created G2 (Code Freeze Gate)"

# ─────────── G3 — Go-Live Gate ───────────
gh issue create \
  --repo "${REPO}" \
  --title "Go-Live Gate — deployment validation and rollback readiness" \
  --body-file "${BODIES}/gate_go_live.md" \
  --label "type:release,priority:p0" \
  --milestone "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off"
echo "  Created G3 (Go-Live Gate)"

echo ""
echo "=== Epics (12) and Gates (3) created — 15 issues total ==="
echo ""
echo "NEXT: Open https://github.com/${REPO}/issues and note the issue numbers"
echo "      for each epic, then update 04_child_issues.sh if you wish to add"
echo "      explicit parent-epic references in child issue bodies."
