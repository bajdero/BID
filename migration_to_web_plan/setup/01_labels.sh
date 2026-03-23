#!/usr/bin/env bash
# 01_labels.sh — Create all required labels for BID web migration
# Safe to re-run: existing labels are updated (--force).
set -euo pipefail
REPO="bajdero/BID"

echo "=== Creating labels for ${REPO} ==="

# type labels
gh label create "type:epic"    --repo "${REPO}" --color "0052CC" --description "Epic — parent issue tracking a full phase or feature area" --force
gh label create "type:feature" --repo "${REPO}" --color "0075CA" --description "New user-facing functionality" --force
gh label create "type:task"    --repo "${REPO}" --color "E4E669" --description "Non-coding task: docs, planning, coordination" --force
gh label create "type:test"    --repo "${REPO}" --color "0E8A16" --description "Test implementation or test infrastructure" --force
gh label create "type:infra"   --repo "${REPO}" --color "F9D0C4" --description "Infrastructure, CI/CD, DevOps configuration" --force
gh label create "type:audit"   --repo "${REPO}" --color "D93F0B" --description "Code review, security or quality audit" --force
gh label create "type:release" --repo "${REPO}" --color "6F42C1" --description "Release preparation, tagging, deployment" --force

# priority labels
gh label create "priority:p0" --repo "${REPO}" --color "B60205" --description "Critical — blocks release" --force
gh label create "priority:p1" --repo "${REPO}" --color "E4E669" --description "High — required for milestone" --force
gh label create "priority:p2" --repo "${REPO}" --color "0075CA" --description "Medium — nice to have" --force

# area labels
gh label create "area:backend"  --repo "${REPO}" --color "1D76DB" --description "Backend API and server-side code" --force
gh label create "area:frontend" --repo "${REPO}" --color "0075CA" --description "React/TypeScript frontend code" --force
gh label create "area:devops"   --repo "${REPO}" --color "F9D0C4" --description "Infrastructure, containers, pipelines" --force
gh label create "area:qa"       --repo "${REPO}" --color "0E8A16" --description "Quality assurance and testing" --force

echo "=== Labels created (14 total) ==="
