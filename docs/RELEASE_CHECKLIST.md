# Release Checklist

Use this checklist before publishing a release.

## 1) Scope and freeze

- [ ] Confirm release scope (features/fixes included).
- [ ] Ensure no unfinished migrations or breaking changes without notes.
- [ ] Freeze direct pushes to the release branch during final validation.

## 2) Quality gates

- [ ] CI is green for the release commit.
- [ ] Local compile check passed:
  ```bash
  python3 -m compileall app.py bot handlers services database keyboards utils
  ```
- [ ] Manual smoke tests completed:
  - [ ] `/start` and cabinet opening
  - [ ] add bot by token
  - [ ] user -> admin forwarding
  - [ ] admin reply routing
  - [ ] `/broadcast` flow
  - [ ] `/setwelcome` / welcome text update

## 3) Configuration and secrets

- [ ] `.env.example` reflects all current required variables.
- [ ] Production secrets are present and valid:
  - [ ] `CONSTRUCTOR_BOT_TOKEN`
  - [ ] `REDIS_URL`
  - [ ] `DATABASE_URL`
  - [ ] `SERVICE_OWNER_TELEGRAM_IDS` (if used)
- [ ] No secrets or tokens are present in commits, logs, or PR text.

## 4) Database and migrations

- [ ] Migration compatibility path verified (`run_sqlite_compat_migrations`).
- [ ] Backup of production DB completed before deploy.
- [ ] Rollback plan for schema/data is documented.

## 5) Deployment

- [ ] Build artifacts/images created successfully.
- [ ] Deployment executed (local/docker/server).
- [ ] Only one app instance is active (single-instance lock respected).
- [ ] Bot polling started for constructor and managed runtimes.

## 6) Post-release verification

- [ ] Check application logs for errors/warnings spikes.
- [ ] Verify Telegram command menus are updated.
- [ ] Verify one real end-to-end dialog in production.
- [ ] Monitor for at least 15-30 minutes after deploy.

## 7) Communication and versioning

- [ ] Update release notes/changelog.
- [ ] Tag release in Git (`vX.Y.Z` if using semver).
- [ ] Share release summary with stakeholders.
