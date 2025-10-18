# Commit Workflow Guide

This guide explains how to properly commit changes in this monorepo project that uses Git submodules.

## Understanding the Structure

The `conductor-community` repository is a **monorepo** that includes three submodules:

```
conductor-community/           (Main repository)
└── src/
    ├── conductor/             (Submodule)
    ├── conductor-gateway/     (Submodule)
    └── conductor-web/         (Submodule)
```

Each submodule is an independent Git repository. This means you need to commit changes in **two places**:
1. First in the **submodule** repository
2. Then in the **main repository** (to update the submodule reference)

## Commit Workflow

### Step 1: Make Changes in a Submodule

```bash
# Navigate to the submodule directory
cd src/conductor

# Check the status
git status

# Create a branch (recommended)
git checkout -b feature/my-new-feature
```

### Step 2: Commit and Push the Submodule

```bash
# Still inside src/conductor/
git add .
git commit -m "feat: add new feature"
git push origin feature/my-new-feature

# Or push to main if you have permissions
git push origin main
```

### Step 3: Return to Main Repository

```bash
# Go back to the main repository root
cd ../..  # Now you're back in conductor-community/
```

### Step 4: Commit the Submodule Reference Update

```bash
# Check the status - you'll see the submodule has changed
git status

# Add the submodule reference
git add src/conductor

# Commit the update
git commit -m "chore: update conductor submodule"

# Push to main repository
git push origin main
```

## Complete Example

Here's a complete workflow example:

```bash
# 1. Make changes in conductor submodule
cd src/conductor
git checkout -b feature/add-validation
# ... make your code changes ...
git add src/core/validation.py
git commit -m "feat: add input validation for workflows"
git push origin feature/add-validation

# 2. Return to main repo and update submodule reference
cd ../..
git add src/conductor
git commit -m "chore: update conductor submodule with validation feature"
git push origin main
```

## Working on Multiple Submodules

If you need to change multiple submodules:

```bash
# 1. Commit changes in first submodule
cd src/conductor
git add .
git commit -m "feat: add new API endpoint"
git push origin main

# 2. Commit changes in second submodule
cd ../conductor-gateway
git add .
git commit -m "feat: add gateway route for new endpoint"
git push origin main

# 3. Go back to main repo
cd ../..

# 4. Update ALL submodule references at once
git add src/conductor src/conductor-gateway
git commit -m "chore: update conductor and gateway submodules"
git push origin main
```

## Important Notes

### ⚠️ Always Commit Submodules First

**NEVER** commit the main repository before committing the submodule changes. This is the correct order:

1. ✅ **CORRECT**: Submodule → Main Repository
2. ❌ **WRONG**: Main Repository → Submodule

If you commit the main repo first, it will reference a commit SHA that doesn't exist in the submodule repository yet, causing issues for other developers.

### Checking Submodule Status

```bash
# From the main repository root
git submodule status

# See all submodule changes
git submodule foreach git status

# See what commit each submodule is on
git submodule foreach git log --oneline -1
```

### Updating Submodules to Latest

```bash
# Pull latest changes from all submodules
git submodule update --remote

# Update a specific submodule
git submodule update --remote src/conductor

# Then commit the reference update
git add src/conductor
git commit -m "chore: update conductor to latest version"
```

### Pulling Changes from Main Repository

When you pull changes from the main repository, you need to update submodules:

```bash
# Pull main repository changes
git pull origin main

# Update submodules to match the references
git submodule update --init --recursive
```

## Common Scenarios

### Scenario 1: Quick Bug Fix

```bash
cd src/conductor
git checkout -b fix/critical-bug
# ... fix the bug ...
git add .
git commit -m "fix: resolve critical authentication bug"
git push origin fix/critical-bug
cd ../..
git add src/conductor
git commit -m "chore: update conductor with critical bug fix"
git push origin main
```

### Scenario 2: Feature Development

```bash
cd src/conductor-web
git checkout -b feature/new-dashboard
# ... develop the feature over multiple commits ...
git add .
git commit -m "feat: add new dashboard component"
git add .
git commit -m "feat: add dashboard API integration"
git add .
git commit -m "test: add dashboard tests"
git push origin feature/new-dashboard
cd ../..
git add src/conductor-web
git commit -m "chore: update conductor-web with new dashboard feature"
git push origin main
```

### Scenario 3: Syncing with Team Changes

```bash
# Get latest from main repo
git pull origin main

# Update all submodules
git submodule update --init --recursive

# Or use the shorthand
git pull --recurse-submodules
```

## Troubleshooting

### "Detached HEAD" in Submodule

Submodules are often in detached HEAD state. To fix:

```bash
cd src/conductor
git checkout main
git pull origin main
cd ../..
```

### Uncommitted Changes in Submodule

```bash
# See what's uncommitted
cd src/conductor
git status

# Either commit them
git add .
git commit -m "fix: uncommitted changes"
git push origin main

# Or discard them
git checkout .
cd ../..
```

### Submodule Reference Not Updated

```bash
# Check if submodule needs updating
git status

# You'll see something like:
# modified:   src/conductor (new commits)

# Add and commit the reference
git add src/conductor
git commit -m "chore: update conductor submodule"
```

## Best Practices

1. **Always work on branches** in submodules, especially for features
2. **Write clear commit messages** following [Conventional Commits](https://www.conventionalcommits.org/)
3. **Test before committing** - run tests in the submodule before pushing
4. **Document breaking changes** in commit messages
5. **Keep submodules in sync** - regularly update to avoid conflicts
6. **Never force push** to main/master branches
7. **Commit often** in submodules, but be strategic about when you update the main repo reference

## Quick Reference

```bash
# Most common workflow
cd src/[submodule-name]
git checkout -b [branch-name]
# ... make changes ...
git add .
git commit -m "[type]: [description]"
git push origin [branch-name]
cd ../..
git add src/[submodule-name]
git commit -m "chore: update [submodule-name] submodule"
git push origin main
```

## Additional Resources

- [SUBMODULES.md](../SUBMODULES.md) - Detailed submodule reference
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)

---

**Remember**: Submodule commits → Main repository commit. Always in this order! 🚀

