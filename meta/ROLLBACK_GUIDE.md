# Rollback Guide for E1 V2

## CRITICAL: Platform Rollback vs Git Operations

### ❌ NEVER DO THESE:
- `git reset --hard`
- `git revert`
- `git checkout <old-commit>`
- `rm -rf .git`
- Manual file restoration from git history

### ✅ ALWAYS USE PLATFORM ROLLBACK:

The Emergent platform provides a **rollback feature** that:
- Restores the entire codebase to any previous checkpoint
- Is free of cost
- Preserves git history correctly
- Ensures environment consistency

## When User Requests Rollback

### Trigger Phrases:
- "revert everything"
- "go back to previous version"
- "undo all changes"
- "restore last working state"
- "rollback to checkpoint X"
- "go back to before [feature/bug]"

### Agent Response:
**DO NOT** attempt git operations. Instead, respond:

```
I cannot perform git-based rollbacks as they may cause environment issues.

The Emergent platform provides a **Rollback** feature that safely restores 
your codebase to any previous checkpoint.

**To rollback:**
1. Click the "Rollback" button in the UI
2. Select the checkpoint you want to restore
3. Confirm the rollback

This is free and preserves your git history correctly.

Would you like me to continue with current work, or would you prefer 
to use the platform rollback first?
```

## Exception: Safe Git Operations

### Allowed:
- `git status` (checking state)
- `git log` (viewing history)
- `git diff` (viewing changes)
- `git commit` (committing work)
- `git branch` (listing branches)

### Forbidden:
- Any destructive git operation
- Anything that modifies git history
- Anything that deletes commits or files from git

## Implementation

### In Coordinator Logic:
Before any git operation:
1. Check if operation is in forbidden list
2. If yes, block and suggest platform rollback
3. If no, allow operation

### In Policy Checker:
```python
ROLLBACK_TRIGGER_PHRASES = [
    "revert", "rollback", "go back", "undo",
    "restore", "previous version", "last working"
]

FORBIDDEN_GIT_OPS = [
    "git reset", "git revert", "git checkout",
    "rm -rf .git", "git clean -fd"
]
```

## For Support Questions

If user asks about:
- How rollback works
- Cost of rollback
- How to save checkpoints
- Git vs platform differences

**Call the `support_agent` tool** with the question.

---

**Last Updated:** 2025-11-23  
**Policy Version:** 1.0
