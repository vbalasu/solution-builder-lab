# DESIGN — Solution Builder Lab: automated workspace setup

## Goal

Turn a **brand-new Databricks workspace** into one where the **Solution Builder**
app is already **running** when lab participants log in — **unattended** and
**entirely in-workspace** (no laptop, no local CLI, no build toolchain). In a
Vocareum classroom this runs automatically on workspace spin-up.

## Components

Everything lives under [`Includes/`](Includes/):

| Path | Role |
|---|---|
| `Includes/Workspace-Setup.py` | **Admin bootstrap notebook** (Run all / Vocareum auto-run). Locates the installer, resolves workspace-specific values, runs the install, prints the App URL. Not for participants. |
| `Includes/installer/workspace-setup.py` | The **pure-Python installer** (`run()` entrypoint). Provisions Lakebase, the deployer SP, deploys the prebuilt app with the exact OBO scopes, wires the SP, and starts the app. |
| `Includes/installer/config.yaml` | **Lab-tuned config.** Workspace-specific values left blank/`auto` for the notebook to fill; `default_catalog` pinned to `solution_builder_lab`. |
| `Includes/installer/artifact/solution-builder-build.zip` | The **prebuilt app** (pinned snapshot) — why there is no build step. |
| `Includes/installer/references/` | `scopes.md`, `superpowers.md`, `troubleshooting.md`. |
| `00 - Start Here …`, `01 - Build a Solution.py` | **Participant** notebooks (used after the app is up). |

## Flow

```
Vocareum (or a workspace admin) runs Includes/Workspace-Setup.py  ── Run all
        │
        ▼
Workspace-Setup.py  (notebook, ambient auth)
  1. %pip install "databricks-sdk>=0.100" pyyaml; restartPython   (one-time)
  2. locate Includes/installer/ relative to the notebook (any sync layout)
  3. importlib-load workspace-setup.py as a module (reuse its helpers + run())
  4. detect the current workspace host; connect with ambient credentials
  5. for any endpoint == "auto": ws._discover_callable() → pick a CALLABLE one
  6. write a resolved config to a temp path (host + resolved endpoints filled)
  7. ws.run(resolved_config)
        │
        ▼
workspace-setup.py :: run()
  auth → log → stage prebuilt artifact → verify endpoints callable →
  provision Lakebase → deployer SP (added to `admins`) → generate app.yml env →
  upload source → create app with the EXACT 13 user_api_scopes (never all-apis) →
  wire SP ↔ Lakebase → deploy (auto-starts) → confirm RUNNING → print App URL
        │
        ▼
Manual, once per workspace: open the App URL, accept the OAuth consent prompt
```

## Key decisions

| Topic | Choice | Why |
|---|---|---|
| Bundle location | Vendor the installer into this repo (`Includes/installer/`) | Self-contained; clones anywhere the lab is synced (Vocareum, a Repo, a workspace folder). |
| Install vehicle | **In-notebook** `%pip` + `restartPython`, then `importlib`-load + `ws.run()` | One notebook, run directly by Vocareum; the SDK is pinned by the `%pip` step so the Apps/Lakebase APIs work. The restart is a single one-time cell. |
| Endpoints | `auto` in `config.yaml`; the notebook discovers a **callable** endpoint per kind | Workspaces list endpoints that are disabled (rate-limit 0); discovery picks one that actually responds, preferring `claude-opus` → `claude-sonnet` for the agent model + primary gateway (falling back to Sonnet when Opus is disabled), a cheap/fast model for the `mini` slot, and an embedding model for embeddings. |
| Default catalog | **Fixed** `solution_builder_lab` | A named, predictable lab catalog for all participants. Created at app boot; the admin deployer SP can create it. |
| Deployer SP | Added to the `admins` group | The OBO token can't carry the `dashboards` scope, so a broadly-privileged build identity is needed for every `initial_templates/*` demo to build. Acceptable for a disposable lab workspace. |
| Artifact | Vendor a **prebuilt** `solution-builder-build.zip` | No build toolchain (`uv`/`bun`/CLI) in the workspace; clone → run. |
| Scopes | Exactly **13** explicit `user_api_scopes`; never `all-apis` | Least-privilege OBO; covers every template capability. |

## Alternatives considered

- **Serverless one-shot Job (`jobs.submit`) with `databricks-sdk` pinned as a task
  dependency.** This avoids the `%pip`/`restartPython` step by installing the SDK
  into the task environment before the process starts. The lab uses the
  in-notebook vehicle instead because Vocareum runs a single notebook directly and
  keeping the whole flow in one notebook is simpler to operate; the restart is a
  one-time cell. The installer's `run()` is vehicle-agnostic, so switching to a job
  later is a bootstrap-only change.

## Residual risks / assumptions

1. **OBO re-authorization is manual** — expanding scopes only changes what the app
   may *request*; an admin must open the app once and consent. The single
   post-install manual step.
2. **Admin identity required** — creating the app + SP and adding the SP to
   `admins` need workspace-admin. True on a fresh lab workspace.
3. **Frozen artifact** — the vendored zip is a pinned snapshot; its gallery
   templates are fixed until it's rebuilt on a toolchain host.
4. **One app per workspace** — up to ~50 participants share the single running
   app; each builds their own solution/DAB.

## Teardown / start over

`Includes/installer/teardown.py` (config-driven, pure Python) reverses the
install, and `Includes/Teardown.py` is its in-workspace "Run all" notebook. It
reuses the installer's config loader and helpers (no duplication) and deletes, in
reverse order: the app (its managed SP + deployments go with it), the Lakebase
project, the deployer SP (removed from `admins` first), the deployer secret scope,
and the uploaded source. It **keeps** the `solution_builder_lab` catalog and its
data; participant-built assets that live outside the catalog are not swept. Both
paths are **dry-run by default** — the CLI needs `--confirm`, the notebook needs
`CONFIRM = True` — and every delete is idempotent/tolerant of already-gone
resources.

## Refreshing the prebuilt artifact

`Includes/installer/artifact/solution-builder-build.zip` is a pinned snapshot. To
pick up newer upstream code, on a host with `git`+`uv`+`bun`+Databricks CLI: clone
upstream [`solution-builder`](https://github.com/databricks-solutions/solution-builder),
run `app/scripts/build.sh --target prod`, zip the resulting `.build` contents, and
replace the vendored zip.
