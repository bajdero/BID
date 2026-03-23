# GitHub Setup Scripts — BID Web Migration

This directory contains the scripts to create all GitHub labels, milestones, epics, and
child issues for the BID web migration project.

## Prerequisites

- [GitHub CLI](https://cli.github.com/) `gh` ≥ 2.40.0
- Authenticated to GitHub: `gh auth login`
- Repository: `bajdero/BID`

## Execution Order

Run scripts in numbered order. Each script is **idempotent** — re-running will skip items that
already exist where possible.

```bash
# 1. Create labels
bash 01_labels.sh

# 2. Create milestones
bash 02_milestones.sh

# 3. Create epic issues (run first to get epic issue numbers)
bash 03_epics.sh

# 4. Create child issues (update parent epic numbers in 04_child_issues.sh first)
bash 04_child_issues.sh
```

### PowerShell equivalent

```powershell
# Replace `bash` with direct execution:
./01_labels.sh          # if Git Bash is on PATH, or:
gh label create ...     # copy individual commands from scripts
```

## After Running

1. Open <https://github.com/bajdero/BID/milestones> and verify 13 milestones exist.
2. Open <https://github.com/bajdero/BID/issues> and verify epics, gates, and child issues.
3. Assign child issues to their parent epics using the "Development" or project board links.
4. Tick all items in the verification checklist in
   `../github_milestones_and_issues_plan.md`.

## Notes

- Issue body files are in `bodies/`. Each `.md` file corresponds to one issue.
- The `--body-file` flag is used in scripts to keep commands short and cross-platform safe.
- After `03_epics.sh` runs, note the epic issue numbers printed by `gh issue create` and
  update the `--body-file` bodies or add sub-issue references manually.
