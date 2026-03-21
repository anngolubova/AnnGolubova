# GitHub Upload Guide

Use this guide to publish the project into a new GitHub repository.

## 1) Pre-upload safety checks

From project root:

```bash
git status
git ls-files .env "*.db" "*.sqlite*" data
```

Expected:
- `git status` is clean
- `.env` is **not** tracked
- database files are **not** tracked
- only `data/.gitkeep` is tracked from `data/`

## 2) Create target repository on GitHub

Create an empty repo in GitHub UI (no README/license/gitignore auto-init recommended).

Example:
- `https://github.com/<username>/telegram-feedbackbot-anngolubova`

## 3) Point local repo to new remote

If you want to keep current `origin`, add a second remote:

```bash
git remote add target https://github.com/<username>/<repo>.git
```

Or replace `origin`:

```bash
git remote set-url origin https://github.com/<username>/<repo>.git
```

## 4) Push branch

```bash
git push -u target <your-branch>
```

or, if `origin` was replaced:

```bash
git push -u origin <your-branch>
```

## 5) Optional: push main branch

If you need `main` in target repository:

```bash
git checkout main
git push -u target main
```

## 6) Final GitHub setup checklist

- [ ] Actions tab shows CI workflow (`.github/workflows/ci.yml`)
- [ ] Issue templates are available
- [ ] PR template is applied
- [ ] CODEOWNERS file is loaded
- [ ] Secrets are configured in repo settings (if needed for deployment)
- [ ] Repository visibility and collaborators are configured

## 7) Security reminders

- Never upload real `.env` values.
- Rotate tokens if they were ever exposed.
- Prefer GitHub Actions Secrets or deployment platform secret storage.
