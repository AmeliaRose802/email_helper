# Task Tracking Guide for Orchestrator

## Overview

The orchestrator uses `tasklist/plan/parallel_execution_plan.json` to track task completion status. This ensures you always know which tasks are done, which were incidentally completed, and what remains.

## Quick Reference

### After Each PR Merge

```bash
# 1. Get modified files from the PR
FILES=$(gh pr view 123 --json files --jq '.files[].path' | tr '\n' ' ')

# 2. Update task status (marks primary task + checks for incidental completions)
cd .github/dev/dev_scripts
python update_task_status.py check-incidental T1.1 \
  --pr 123 \
  --url "https://github.com/AmeliaRose802/email_helper/pull/123" \
  --files $FILES

# 3. Commit the update
cd ../../..
git add tasklist/plan/parallel_execution_plan.json
git commit -m "chore: mark task T1.1 as completed (PR #123)"
git push
```

### Get Progress Report

```bash
python .github/dev/dev_scripts/update_task_status.py report
```

### Mark Task Complete (Manual)

```bash
python .github/dev/dev_scripts/update_task_status.py mark-complete T1.1 \
  --pr 123 \
  --url "https://github.com/AmeliaRose802/email_helper/pull/123" \
  --runtime 35 \
  --files backend/services/com_email_provider.py
```

## Task Status Schema

When a task is marked complete, it gets these additional fields:

```json
{
  "task_id": "T1.1",
  "summary": "Create COM Email Provider Adapter",
  "status": "completed",
  "completed_at": "2025-10-14T15:30:00Z",
  "pr_number": 123,
  "pr_url": "https://github.com/AmeliaRose802/email_helper/pull/123",
  "completion_type": "direct",
  "actual_runtime_min": 35,
  "files_modified": [
    "backend/services/com_email_provider.py",
    "backend/services/email_provider.py"
  ]
}
```

For incidentally completed tasks:

```json
{
  "task_id": "T2.4",
  "summary": "Create Configuration Templates",
  "status": "completed",
  "completed_at": "2025-10-14T15:30:00Z",
  "pr_number": 123,
  "pr_url": "https://github.com/AmeliaRose802/email_helper/pull/123",
  "completion_type": "incidental",
  "completed_by": "T1.1",
  "files_modified": [
    "backend/.env.localhost.example"
  ]
}
```

## Incidental Completion Detection

The script automatically detects incidental completions by:

1. Comparing modified files in the PR with files required by other tasks
2. If ≥50% of a task's files are modified, it's considered incidentally completed
3. These are marked with `completion_type: "incidental"` and `completed_by` field

## Progress Reporting

The progress report shows:

- **Total tasks**: Total number of tasks in the plan
- **Completed tasks**: Number completed (direct + incidental)
- **Completed direct**: Tasks completed by their own PR
- **Completed incidental**: Tasks completed by other PRs
- **Pending tasks**: Tasks still to do
- **Percentage**: Overall completion percentage

Example output:

```
================================================================================
📊 TASK COMPLETION REPORT
================================================================================

📈 Overall Progress: 8/21 tasks (38.1%)
   ✅ Direct completions: 7
   🔄 Incidental completions: 1
   ⏳ Pending: 13

✅ Completed Tasks (8):
   ✅ T1.1: Create COM Email Provider Adapter
      PR #123
   ✅ T1.2: Create AI Service Adapter
      PR #124
   🔄 T2.4: Create Configuration Templates
      PR #123

⏳ Pending Tasks (13):
   ⏳ T1.3: Update API Dependencies (Wave 2)
   ⏳ T1.4: Localhost Authentication (Wave 2)
   ...
```

## Workflow Integration

### In Orchestrator Autonomous Loop

```
1. Create PRs with task IDs in titles: "[T1.1] Create COM Email Provider"
2. Wait for PRs to be ready (blocking script)
3. Merge each PR
4. IMMEDIATELY after merge:
   - Update task status with check-incidental
   - Commit and push the updated plan
5. After all PRs in block merged:
   - Run progress report
   - Show user the completion status
   - Continue to next block
```

### Benefits

- ✅ **No more guessing**: Always know exact progress
- ✅ **Automatic detection**: Finds tasks completed by accident
- ✅ **Audit trail**: PR number and URL for each task
- ✅ **Easy debugging**: See what was done and when
- ✅ **Progress tracking**: Clear metrics for how far along you are

## Troubleshooting

### Task not found error

Make sure the task ID exactly matches what's in `parallel_execution_plan.json`. Task IDs are case-sensitive (e.g., `T1.1` not `t1.1`).

### Incidental completions not detected

The script requires ≥50% file overlap. If a PR only touched 1 out of 3 files for a task, it won't be marked as incidentally completed. You can manually mark it if needed:

```bash
python update_task_status.py mark-complete T2.4 \
  --pr 123 \
  --url "..." \
  --files backend/.env.localhost.example
```

### Multiple tasks with same files

If multiple tasks touch the same files, the script will mark all of them as incidentally completed when any one completes. This is intentional - if the files are done, the task is effectively done.

## Best Practices

1. **Always include task ID in PR title**: `[T1.1] Description`
2. **Update after EACH merge**: Don't batch updates
3. **Check the report**: Review progress after each block
4. **Commit the updates**: The JSON file should be version-controlled
5. **Use check-incidental**: It's more thorough than mark-complete alone
