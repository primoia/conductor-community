# Git Workflow for Conductor Monorepo

This repository is a monorepo with submodules:

- `src/conductor` (CLI + FastAPI)
- `src/conductor-gateway` (Backend API)
- `src/conductor-web` (Angular Frontend)
- `conductor-community` (this repo, monorepo root)

## Commit Order (STRICT)
Always commit and push in this exact sequence:

1. `src/conductor`
2. `src/conductor-gateway`
3. `src/conductor-web`
4. `conductor-community` (root)

## Conventional Commits
Use English messages with Conventional Commits format:

- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`
- Subject: `type(scope): description` (≤72 chars)
- Body: optional details on the “why” over “what”

Examples:
- `feat(api): add new endpoint for user metrics`
- `fix(auth): resolve token expiration bug`
- `docs(readme): update installation instructions`

## Standard Procedure

For each repo (replace `<path>`):

```bash
# Inspect
cd <path>
git status
git diff --stat

# Stage & commit
git add -A .
git commit -m "type(scope): concise description"

# Push
git push origin HEAD
```

Recommended order with absolute paths:

```bash
# 1) Conductor
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor
git add -A .
git commit -m "type(scope): description"
git push origin HEAD

# 2) Conductor Gateway
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor-gateway
git add -A .
git commit -m "type(scope): description"
git push origin HEAD

# 3) Conductor Web
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor-web
git add -A .
git commit -m "type(scope): description"
git push origin HEAD

# 4) Monorepo Root
cd /mnt/ramdisk/primoia-main/conductor-community
git add -A .
git commit -m "type(scope): description"
git push origin HEAD
```

## Error Handling

- Commit fails: read the error, fix or stage missing files, and commit again.
- Push fails (non-fast-forward):
  - Pull latest: `git pull --rebase` (or resolve conflicts)
  - Push again: `git push origin HEAD`
- Pre-commit hooks modify files:
  - Re-run `git status`
  - `git add -A .` and `git commit --amend --no-edit`
  - Push with `--force-with-lease` only if amending already-pushed commits and you know it’s safe.

## Notes

- Do not skip submodules in the sequence.
- Keep messages short and focused on intent.
- Root repo should include submodule pointer updates and documentation changes.
