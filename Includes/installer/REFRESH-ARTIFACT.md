# Refreshing `solution-builder-build.zip`

`Includes/installer/artifact/solution-builder-build.zip` is a **prebuilt,
pinned snapshot** of the Solution Builder app. It's what lets the installer
deploy with no build toolchain in the workspace. When the upstream source
([`databricks-solutions/solution-builder`](https://github.com/databricks-solutions/solution-builder))
changes and you want those changes in the lab, rebuild this zip on a toolchain
host and replace the file.

You do **not** own the upstream repo — you only rebuild from it and vendor the
result here.

## When to do this

- Upstream shipped app fixes/features you want in the lab.
- The **gallery templates** changed (new/updated `initial_templates/*`).
- A dependency bump you need. Otherwise, leave the pinned snapshot alone.

## What's inside the zip (reference)

The zip is the **contents** of the upstream `app/.build/` directory (not the
directory itself — `app.yml` must sit at the zip root):

| Entry | What it is |
|---|---|
| `demo_prompt_generator-*.whl` | The compiled app — FastAPI backend + built React frontend + `.claude/skills` + `initial_templates`, all inside the wheel |
| `pyproject.toml`, `uv.lock` | Dependency manifest + lockfile the app installs from at boot |
| `app.yml` | Databricks Apps config (run command + env). **The installer regenerates this per-workspace at deploy time.** |
| `start.sh` | App entrypoint (unzips the per-template zips on boot) |
| `initial_templates_zips/<slug>.zip` | The starter gallery, one zip per template |

## Prerequisites (on the build host — a laptop/CI, NOT the workspace)

- `git`, `uv`, `bun`, and the **Databricks CLI** on `PATH`.
- Network access to GitHub and the Databricks pip/bundle proxies.
- ~1 GB free disk for the clone + build.

## Steps

```bash
# 1. Clone the upstream source (fresh, so the build is reproducible)
git clone https://github.com/databricks-solutions/solution-builder.git
cd solution-builder/app

# 2. Build the prod artifact → creates ./.build/ (app.yml, *.whl, templates, …)
./scripts/build.sh --target prod

# 3. Package .build/'s CONTENTS into the vendored zip (note: zip the contents,
#    not the .build folder — app.yml must be at the zip root).
#    Point the path at YOUR clone of THIS lab repo:
LAB_REPO=/path/to/solution-builder-lab
( cd .build && zip -qr - . ) > "$LAB_REPO/Includes/installer/artifact/solution-builder-build.zip"
```

## Verify before committing

```bash
cd "$LAB_REPO"
# app.yml must be at the root, and there must be a wheel:
unzip -l Includes/installer/artifact/solution-builder-build.zip | grep -E ' app.yml$| .*\.whl$'
# list the gallery templates that shipped:
unzip -l Includes/installer/artifact/solution-builder-build.zip | grep initial_templates_zips/
```

You should see `app.yml` at the top level and exactly one `*.whl`. If `app.yml`
is nested under a subfolder, you zipped the `.build` directory instead of its
contents — redo step 3.

> **Optional full check:** run a real install into a throwaway workspace with
> `Includes/Workspace-Setup.py` (Run all), confirm the app reaches RUNNING and
> the gallery loads, then `Includes/Teardown.py` to clean up.

## ⚠️ Never commit secrets

`build.sh --target prod` writes `app.yml` from the bundle's `env:` block. Before
committing, make sure the `app.yml` inside the zip carries **no real
`DEPLOYER_SP_CLIENT_SECRET`** (or any other secret). The installer rewrites the
`app.yml` `env:` per workspace at deploy time, so a minimal/empty `env:` in the
snapshot is fine and preferred. To inspect it:

```bash
unzip -p Includes/installer/artifact/solution-builder-build.zip app.yml
```

If it contains a secret, rebuild from a clean clone (no local
`databricks.prod.yml` with secrets) and repackage.

## Commit & push

```bash
cd "$LAB_REPO"
git add Includes/installer/artifact/solution-builder-build.zip
git commit -m "Refresh solution-builder-build.zip (upstream <short-sha>, <date>)"
git push origin main
```

Record the upstream commit SHA in the message so the snapshot is traceable
(`git -C solution-builder rev-parse --short HEAD` on the build host).

## Rollback

The zip is version-controlled, so a bad refresh is one revert away:

```bash
git revert <refresh-commit>        # or: git checkout <good-sha> -- Includes/installer/artifact/solution-builder-build.zip
git push origin main
```
