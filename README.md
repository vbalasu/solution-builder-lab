# Solution Builder Lab

| Field | Details | Description |
|---|---|---|
| Duration | 60 minutes | Estimated duration to complete the lab. |
| Level | 200 | Target difficulty (100 = beginner, 200 = intermediate, 300 = advanced). |
| Lab Status | Active | See descriptions in the main repo README. |
| Course Location | N/A | Lab is available in this repo. |
| Developer | Vijay Balasubramaniam | Primary developer(s). |
| Reviewer | N/A | Subject matter expert reviewer(s). |
| Product Version | Public Preview | Solution Builder (go/solution-builder). |
| Created Date | 09/04/2026 | MM/DD/YYYY. |

---

## Description

This lab gives partners and field practitioners hands-on access to **Databricks
Solution Builder** — an AI app that turns a plain-language description of a
business outcome into a complete, runnable Databricks solution (synthetic data,
transformations, an AI/BI dashboard, and the glue to run it), packaged as a
**Databricks Asset Bundle (DAB)** you can deploy anywhere.

The app is **installed and running before participants log in**. Participants do
**not** install anything: they open the shared app, describe a solution, let it
build, explore the generated assets, and leave with a DAB they can deploy in
their own workspace.

Solution Builder is open source:
[github.com/databricks-solutions/solution-builder](https://github.com/databricks-solutions/solution-builder).

## Learning Objectives

- Describe a business outcome and have Solution Builder generate a solution.
- Explore the generated data, transformations, and AI/BI dashboard.
- Produce a DAB and understand how to deploy it in your own workspace.

## Requirements & Prerequisites

- Basic Databricks workspace navigation (finding notebooks, Catalog Explorer,
  Dashboards, Apps).
- A browser. No prior Solution Builder experience needed.

## Contents

- **00 - Start Here - Workspace Information** — overview + how to open the app.
- **01 - Build a Solution** — the hands-on workshop.
- **Includes/** — the admin **Workspace-Setup** notebook and the bundled,
  deterministic Solution Builder installer (see below).

## Getting Started (participants)

1. Open **00 - Start Here - Workspace Information** to see how to reach the app.
2. Open **01 - Build a Solution** and follow the steps.

---

## For instructors / workspace admins

The lab workspace is prepared by **`Includes/Workspace-Setup.py`**. In a Vocareum
lab this runs automatically when the workspace spins up (e.g. via a Lakeflow job);
it can also be run by hand by a workspace admin. It:

- runs on the workspace's **ambient credentials** (no login) and auto-detects the
  workspace host;
- discovers **callable serving endpoints** in the workspace (any `auto` endpoint
  in `Includes/installer/config.yaml` is filled in with a reachable model);
- provisions **Lakebase**, creates a **deployer service principal**, deploys the
  app with the **exact explicit OBO build scopes** (never `all-apis`), wires the
  app's SP to Lakebase, and **starts the app**.

It is deterministic and idempotent — the same code produces the same result each
time, and it is safe to re-run.

### Install in a new workspace (step by step)

For a fresh workspace outside Vocareum (or to run the setup by hand):

1. **Get this repo into the workspace.** In a Vocareum lab it's already synced.
   Otherwise, add it as a **Git folder**: Workspace ▸ your user folder ▸
   **Create ▸ Git folder** → `https://github.com/databricks-learning/solution-builder-lab.git`
   (branch `main`). Private-repo clones need your GitHub credentials linked under
   Settings ▸ Linked accounts.
2. **Open `Includes/Workspace-Setup.py`** and attach it to compute (serverless or
   any cluster). You must be a **workspace admin** — setup creates the app and a
   service principal and adds the SP to `admins`.
3. Click **Run all**. It pins the SDK, discovers callable endpoints, provisions
   Lakebase, deploys the app, wires it, and starts it. This takes several minutes;
   nothing to fill in.
4. When it finishes it prints the **App URL** — note it.
5. Do the **one-time first-launch authorization** below (open the URL, accept the
   consent prompt). The app is then ready for participants.

Nothing in `Includes/installer/config.yaml` needs editing for a standard run.

### The bundled installer

`Includes/installer/` is a **pure-Python** installer (no bash, no git, no build
toolchain) that deploys a **prebuilt app artifact shipped in this repo**
(`Includes/installer/artifact/solution-builder-build.zip`). Configuration lives in
`Includes/installer/config.yaml`; for a normal lab run nothing there needs
editing — the setup notebook fills in the workspace-specific values at runtime.
Reference notes are under `Includes/installer/references/`.

Upstream installer source:
[github.com/vbalasu/solution-builder-installer](https://github.com/vbalasu/solution-builder-installer).

### One-time first-launch authorization

After setup finishes, an admin should open the printed **App URL** once and accept
the authorization prompt so the app's token carries the granted build scopes. If
no prompt appears, stop then start the `solution-builder` app compute and reopen.

### Notes

- **One app per workspace**, shared by up to ~50 participants; each builds their
  own solution and DAB.
- Vocareum clears assets after the session — participants should download or
  deploy their DAB before finishing.
