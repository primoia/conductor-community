# 📖 Documentation Cleanup Guide - Conductor Community

> **Purpose:** This guide establishes documentation standards and periodic cleanup procedures for the Conductor Community monorepo and its submodules to prevent documentation debt and maintain repository hygiene.

---

## 1. Philosophy

Documentation should be:
- **Current**: Reflects the actual state of the code
- **Organized**: Easy to find and navigate
- **Purposeful**: Every document has a clear reason to exist
- **Maintainable**: Reviewed and cleaned regularly

**Anti-patterns to avoid:**
- ❌ Timestamped files (e.g., `plan-2025-10-21T11-40-38.md`)
- ❌ Duplicate content across monorepo and submodules
- ❌ Completed planning artifacts left in active directories
- ❌ Bug tracking in markdown files instead of GitHub Issues
- ❌ Historical content cluttering active documentation

---

## 2. Documentation Structure

### Monorepo Root (`/`)

```
conductor-community/
├── README.md                    # Main entry point, project overview
├── CONTRIBUTING.md              # How to contribute to the monorepo
├── CODE_OF_CONDUCT.md           # Community guidelines
├── SUBMODULES.md                # Git submodules reference
├── QUICK_COMMANDS.md            # Quick reference for common commands
├── SCRIPTS_GUIA.md              # Scripts usage guide
├── VOLUMES_GUIDE.md             # Docker volumes guide
├── security-recommendations.md  # Security best practices
│
├── docs/                        # Permanent technical documentation
│   ├── DOCUMENTATION_CLEANUP_GUIDE.md  # This document
│   ├── COMMIT_WORKFLOW.md
│   ├── AI_AGENT_CONCEPTS.md
│   ├── GIT.md
│   ├── api/                     # API documentation
│   ├── sagas/                   # Active saga documentation (see guidelines below)
│   └── archived/                # Historical documentation (when needed)
│
├── playbook/                    # Implementation playbooks (active projects)
│
└── conductor/                   # Submodules directory
    ├── conductor/
    ├── conductor-gateway/
    └── conductor-web/
```

### Submodules Documentation

Each submodule maintains its own documentation:
- `conductor/conductor/docs/` - API framework documentation
- `conductor/conductor-gateway/docs/` - Gateway documentation
- `conductor/conductor-web/docs/` - Frontend documentation

**Important:** Avoid duplicating content between monorepo root and submodules. Establish single source of truth.

---

## 3. Periodic Cleanup Checklist

Run this cleanup procedure **monthly** or when documentation feels cluttered:

### 🔍 Step 1: Identify Cleanup Targets

Use these commands to find potentially obsolete files:

```bash
# Find timestamped files (contains dates like 2025-10-21 or T11-40-38)
find . -name "*.md" | grep -E "[0-9]{4}-[0-9]{2}-[0-9]{2}|T[0-9]{2}-[0-9]{2}-[0-9]{2}"

# Find planning artifacts that may be complete
find docs/ -name "PLANO_*.md" -o -name "IMPLEMENTACAO_*.md" -o -name "plan.md" -o -name "fase-*.md"

# Find potential bug tracking files
find . -name "PROBLEMA_*.md" -o -name "BUG_*.md" -o -name "ISSUE_*.md"

# Find duplicate files between root and submodules
find docs/ -name "*.md" -type f -exec basename {} \; | sort | uniq -d
```

### 📝 Step 2: Review Each Category

#### Category A: Timestamped/Temporary Files
**Pattern:** Files with dates in names (`2025-10-21`, `T11-40-38`, etc.)

**Action:**
- ✅ Delete if created during development sessions
- ✅ Delete if content is rough notes or unstructured

**Example:**
```bash
# Review before deleting
cat docs/novo-roteiro-2025-10-21T11-40-38.md

# Delete if confirmed
rm docs/novo-roteiro-2025-10-21T11-40-38.md
```

#### Category B: Completed Planning Artifacts
**Pattern:** `PLANO_*.md`, `IMPLEMENTACAO_*.md`, `RESUMO_*.md`, `CHECKLIST_*.md`

**Action:**
- ✅ Delete if feature is 100% implemented
- ✅ Delete if plan is obsolete or superseded
- 📦 Archive if historical value exists

**Example:**
```bash
# Delete completed implementation tracking
rm docs/IMPLEMENTACAO_CONVERSATION_ID.md
rm docs/RESUMO_IMPLEMENTACAO_FINAL.md
```

#### Category C: Duplicate Documentation
**Pattern:** Same content in multiple locations

**Action:**
- ✅ Keep in submodule if submodule-specific
- ✅ Keep in monorepo root if cross-cutting concern
- ✅ Delete the duplicate copy

**Example:**
```bash
# Delete duplicate from root (keep in submodule)
rm docs/001-frontend-gerenciamento-roteiros.md
```

#### Category D: Bug Tracking Files
**Pattern:** `PROBLEMA_*.md`, `BUG_*.md`, `ISSUE_*.md`

**Action:**
- ✅ Convert to GitHub Issue
- ✅ Delete markdown file after issue created
- ✅ Link to GitHub Issue in commit message

**Example:**
```bash
# Create GitHub Issue first, then delete
gh issue create --title "Drag & Drop persistence bug" --body-file conductor/PROBLEMA_DRAG_DROP_AGENTES.md
rm conductor/PROBLEMA_DRAG_DROP_AGENTES.md
```

#### Category E: Saga Documentation
**Pattern:** `docs/sagas/saga-*/`

**Guidelines:**
- ✅ Keep active sagas with ongoing work
- ✅ Delete phase files after saga completion (keep only summary)
- 📦 Move completed sagas to `docs/archived/sagas/` if historical value
- ✅ Delete timestamped saga files immediately

**Active saga structure (acceptable):**
```
docs/sagas/saga-XXX/
├── README.md           # Saga overview and current status
├── plan.md             # Current implementation plan
└── notes/              # Working notes (clean after completion)
```

**Completed saga (should be archived or deleted):**
```
docs/archived/sagas/saga-XXX/
└── SUMMARY.md          # Brief summary of what was implemented
```

#### Category F: Historical/Archived Content
**Pattern:** Large directories with old content (e.g., `history/sagas/`)

**Action:**
- 📦 Move to `docs/archived/` if has historical value
- ✅ Delete if redundant with git history
- ✅ Delete if content is more than 6 months old and unused

**Example:**
```bash
# Archive historical sagas
mkdir -p docs/archived
mv conductor/conductor/docs/history/sagas docs/archived/old-conductor-sagas

# Or delete if truly obsolete
rm -rf conductor/conductor/docs/history/sagas
```

### 🎯 Step 3: Execute Cleanup

After reviewing and confirming:

```bash
# 1. Delete confirmed files in monorepo
git rm docs/file1.md docs/file2.md
git commit -m "docs: remove obsolete documentation files"

# 2. Clean submodules
cd conductor/conductor-web
git rm docs/obsolete-file.md
git commit -m "docs: remove obsolete documentation"
git push origin main

cd ../conductor-gateway
# Repeat for each submodule with changes

cd ../..

# 3. Update submodule pointers in monorepo
git add conductor/
git commit -m "chore: update submodule references after doc cleanup"
git push origin <your-branch>
```

---

## 4. Documentation Quality Standards

### File Naming Conventions

✅ **Good:**
- `README.md` - Standard entry point
- `API_DOCUMENTATION.md` - Descriptive, permanent
- `multi-provider-setup.md` - Kebab-case for features
- `CONTRIBUTING.md` - Standard community file

❌ **Bad:**
- `novo-roteiro-2025-10-21T11-40-38.md` - Timestamped
- `plan.md` - Too generic
- `PLANO_FEATURE_X.md` - Planning artifact
- `notes.md` - Too vague

### Content Standards

Every documentation file should have:

1. **Clear Title**: What is this document about?
2. **Purpose Statement**: Why does this document exist?
3. **Last Updated**: Date of last significant update
4. **Status** (for planning docs): Draft, In Progress, Complete, Obsolete

### Example Document Header

```markdown
# Feature X Implementation Guide

> **Purpose:** This guide documents how to implement and use Feature X in the Conductor framework.
>
> **Status:** Active
> **Last Updated:** 2025-11-05

---
```

---

## 5. Maintenance Schedule

### Monthly (First Monday)
- [ ] Run cleanup commands to identify candidates
- [ ] Review timestamped files (should be 0)
- [ ] Check for completed planning artifacts
- [ ] Verify no duplicate content

### Quarterly
- [ ] Review all saga documentation
- [ ] Archive completed sagas
- [ ] Update this cleanup guide if needed
- [ ] Review and update main README.md

### Before Each Release
- [ ] Ensure all documentation reflects current state
- [ ] Remove all WIP/draft documents
- [ ] Verify all links work
- [ ] Update version references

---

## 6. Quick Commands Reference

### Find all markdown files
```bash
find . -name "*.md" -type f | grep -v node_modules | grep -v .git
```

### Count documentation files by directory
```bash
find docs/ -name "*.md" -type f | wc -l
find conductor/conductor/docs/ -name "*.md" -type f | wc -l
find conductor/conductor-gateway/docs/ -name "*.md" -type f | wc -l
find conductor/conductor-web/docs/ -name "*.md" -type f | wc -l
```

### Find large documentation files (>10KB)
```bash
find . -name "*.md" -type f -size +10k -exec ls -lh {} \;
```

### Search for specific patterns
```bash
# Find files mentioning "TODO" or "FIXME"
grep -r "TODO\|FIXME" --include="*.md" docs/

# Find files with implementation status
grep -r "100%\|COMPLETE\|DONE" --include="*.md" docs/
```

---

## 7. Submodule-Specific Guidelines

### conductor/conductor
- Keep architecture and framework documentation
- Remove agent-specific planning after implementation
- Archive old SAGA documentation to separate repo or delete

### conductor/conductor-gateway
- Keep API endpoint documentation
- Remove implementation planning artifacts
- Keep integration guides

### conductor/conductor-web
- Keep component documentation
- Remove UI/UX planning after implementation
- Keep user guides and tutorials

---

## 8. Decision Matrix

When in doubt, ask:

| Question | Keep | Archive | Delete |
|----------|------|---------|--------|
| Is this actively referenced? | ✅ | | |
| Does git history preserve this info? | | | ✅ |
| Is this a temporary planning doc? | | | ✅ |
| Does this have historical value? | | ✅ | |
| Is the content duplicated elsewhere? | | | ✅ |
| Is this older than 6 months and unused? | | | ✅ |
| Is this timestamped or dated? | | | ✅ |
| Would a new contributor need this? | ✅ | | |

---

## 9. Commit Message Standards for Cleanup

Use these commit message prefixes:

```bash
docs: remove obsolete documentation files
docs: archive completed saga documentation
docs: fix duplicate documentation
chore: cleanup temporary markdown files
chore: update submodule references after doc cleanup
```

---

## 10. Automation Opportunities

Consider creating scripts for:

1. **Timestamped file detector**: Alert on any file with date in name
2. **Duplicate file finder**: Compare checksums across dirs
3. **Stale documentation report**: Files not modified in 6+ months
4. **Broken link checker**: Verify all internal links work

---

## Need Help?

If unsure whether to delete a file:
1. Check git history: `git log --follow <file>`
2. Search for references: `grep -r "filename" .`
3. Ask in GitHub Discussions
4. When in doubt, archive instead of delete

---

**Last Updated:** 2025-11-05
**Maintained by:** Conductor Community Contributors
