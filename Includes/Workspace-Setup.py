# Databricks notebook source
# MAGIC %md
# MAGIC # Workspace Setup — Solution Builder Lab (ADMIN / automated)
# MAGIC
# MAGIC **This notebook is not for lab participants.** It is the admin setup step that
# MAGIC provisions the lab workspace so the **Solution Builder** app is already
# MAGIC **running** when partners log in. In a Vocareum lab it is run automatically
# MAGIC (e.g. by a Lakeflow job when the workspace spins up); it can also be run by
# MAGIC hand by a workspace admin.
# MAGIC
# MAGIC It runs the deterministic, **pure-Python** Solution Builder installer bundled at
# MAGIC `Includes/installer/` against a **prebuilt app artifact** that ships in this
# MAGIC repo — so there is no build toolchain and no bash. It:
# MAGIC
# MAGIC 1. Detects the **current workspace host** and uses the notebook's **ambient
# MAGIC    credentials** (no login).
# MAGIC 2. Discovers **callable serving endpoints** in this workspace (any `auto`
# MAGIC    endpoint in `config.yaml` is filled in with a real, reachable model).
# MAGIC 3. Provisions **Lakebase**, creates the **deployer service principal**,
# MAGIC    deploys the app with the **exact explicit OBO scopes** (never `all-apis`),
# MAGIC    wires the app's SP to Lakebase, and **starts the app**.
# MAGIC
# MAGIC Every step is idempotent — safe to re-run.
# MAGIC
# MAGIC > **One app per workspace.** Up to ~50 participants share the single running
# MAGIC > app; each builds their own solution and their own DAB.
# MAGIC
# MAGIC > **Authorization prompt (first launch).** After this notebook finishes, an
# MAGIC > admin should open the printed **App URL** once and accept the consent
# MAGIC > prompt so the app's token carries the granted build scopes. See the last
# MAGIC > cell.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 — Pin a recent SDK and restart Python
# MAGIC The runtime's bundled `databricks-sdk` can be too old for the Apps / Lakebase
# MAGIC APIs the installer uses, so we pin a recent one and restart.

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.100" pyyaml
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 — Locate the bundled installer
# MAGIC Find `Includes/installer/` relative to this notebook, wherever the repo was
# MAGIC synced (Vocareum, a Databricks Repo, or a workspace folder).

# COMMAND ----------

import os
from pathlib import Path

def _notebook_dir() -> str:
    """Filesystem directory that holds THIS notebook, across sync layouts."""
    try:
        ctx = (
            dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        )
        nb_path = ctx.notebookPath().get()  # e.g. /Repos/u/solution-builder-lab/Includes/Workspace-Setup
        # Workspace files are FUSE-mounted under /Workspace.
        return "/Workspace" + os.path.dirname(nb_path)
    except Exception:
        return os.getcwd()

def _find_installer_dir() -> Path:
    candidates = [
        Path(_notebook_dir()) / "installer",
        Path(os.getcwd()) / "installer",
        Path(os.getcwd()) / "Includes" / "installer",
    ]
    for c in candidates:
        if (c / "workspace-setup.py").exists():
            return c.resolve()
    raise FileNotFoundError(
        "Could not locate Includes/installer/workspace-setup.py near this notebook. "
        f"Tried: {[str(c) for c in candidates]}"
    )

INSTALLER_DIR = _find_installer_dir()
CONFIG_TEMPLATE = INSTALLER_DIR / "config.yaml"
ARTIFACT_ZIP = INSTALLER_DIR / "artifact" / "solution-builder-build.zip"
print(f"Installer dir : {INSTALLER_DIR}")
print(f"Config template: {CONFIG_TEMPLATE}")
print(f"Artifact       : {ARTIFACT_ZIP}  ({'found' if ARTIFACT_ZIP.exists() else 'MISSING'})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3 — Import the installer module
# MAGIC Load `workspace-setup.py` as a module so we can reuse its endpoint-discovery
# MAGIC helpers and its `run()` entrypoint.

# COMMAND ----------

import importlib.util

spec = importlib.util.spec_from_file_location("ws_installer", str(INSTALLER_DIR / "workspace-setup.py"))
ws = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ws)
print("Loaded installer module. Canonical scopes:", ", ".join(ws.ALL_SCOPES))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 4 — Resolve workspace host + callable endpoints
# MAGIC Connect with ambient auth, read the template config, substitute the current
# MAGIC host, and replace any `auto` endpoint with a **callable** endpoint discovered
# MAGIC in this workspace.

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()  # ambient notebook auth
host = (w.config.host or "").rstrip("/")
me = w.current_user.me().user_name
print(f"Signed in as {me} on {host}")

cfg_data = ws.load_yaml(CONFIG_TEMPLATE)
cfg_data.setdefault("databricks", {})["workspace_url"] = host
cfg_data["databricks"]["profile"] = ""

# Discover callable endpoints only if any endpoint is set to "auto".
ep = cfg_data.setdefault("endpoints", {})
needs_auto = any(str(ep.get(k, "")).lower() == "auto"
                 for k in ("anthropic_llm_endpoint", "ai_gateway", "ai_gateway_mini", "ai_gateway_embedding"))

if needs_auto:
    print("Resolving `auto` endpoints — probing this workspace for callable models…")
    chat_ok, embed_ok = ws._discover_callable(w)
    print("  callable chat      :", ", ".join(chat_ok) or "(none)")
    print("  callable embedding :", ", ".join(embed_ok) or "(none)")

    def _pick(cands, needles, fallback):
        for nd in needles:
            for c in cands:
                if nd in c.lower():
                    return c
        return cands[0] if cands else fallback

    resolved = {
        "anthropic_llm_endpoint": _pick(chat_ok, ["claude-sonnet", "claude"], ""),
        "ai_gateway":             _pick(chat_ok, ["claude-sonnet", "claude", "gpt"], ""),
        "ai_gateway_mini":        _pick(chat_ok, ["mini", "nano", "flash", "haiku", "gpt"], ""),
        "ai_gateway_embedding":   _pick(embed_ok, ["embedding", "embed", "bge", "gte", "qwen"], ""),
    }
    for k, v in resolved.items():
        if str(ep.get(k, "")).lower() == "auto":
            if not v:
                raise RuntimeError(
                    f"No callable endpoint found for '{k}'. Enable model serving in this "
                    "workspace or pin an exact endpoint name in Includes/installer/config.yaml."
                )
            ep[k] = v

# Make the artifact path absolute so it resolves regardless of where we write the config.
cfg_data.setdefault("artifact", {})["path"] = str(ARTIFACT_ZIP)

print("\nResolved endpoints:")
for k in ("anthropic_llm_endpoint", "ai_gateway", "ai_gateway_mini", "ai_gateway_embedding"):
    print(f"  {k}: {ep.get(k)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 5 — Write the resolved config and run the installer
# MAGIC The installer prints a plan, verifies endpoints, provisions Lakebase, deploys
# MAGIC the app, wires the SP, and starts the app. This can take several minutes.

# COMMAND ----------

import tempfile, yaml

resolved_path = Path(tempfile.gettempdir()) / "solution-builder-lab.config.resolved.yaml"
resolved_path.write_text(yaml.safe_dump(cfg_data, sort_keys=False))
print(f"Wrote resolved config → {resolved_path}\n")

# ws.run() reads the config, does the full install, and prints the App URL.
ws.run(str(resolved_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 6 — First-launch authorization (manual, one time per workspace)
# MAGIC The **App URL** was printed above. A workspace admin should:
# MAGIC
# MAGIC 1. Open the App URL once (a fresh/incognito window is most reliable).
# MAGIC 2. Accept the authorization/consent prompt so the app's token carries the
# MAGIC    granted build scopes.
# MAGIC 3. If no prompt appears, stop then start the app compute for
# MAGIC    **`solution-builder`** and reopen.
# MAGIC
# MAGIC After that, participants can open the app (it's shared, one per workspace) and
# MAGIC start building. Troubleshooting notes: `Includes/installer/references/`.
