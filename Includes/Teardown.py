# Databricks notebook source
# MAGIC %md
# MAGIC # Teardown — Solution Builder Lab (ADMIN / destructive)
# MAGIC
# MAGIC **Reverses the install so you can start over.** Deletes the app, the
# MAGIC Lakebase project, the deployer service principal (removing it from
# MAGIC `admins`), the deployer secret scope, and the uploaded app source.
# MAGIC
# MAGIC **Kept:** the Unity Catalog data (`solution_builder_lab`) and any
# MAGIC participant-built demo assets. Some demo assets (pipelines, dashboards,
# MAGIC Genie spaces, jobs) live outside the catalog and are **not** removed —
# MAGIC delete those by hand if you need a truly empty workspace.
# MAGIC
# MAGIC > **Safe by default.** With `CONFIRM = False` this only prints a plan and
# MAGIC > changes nothing. Set `CONFIRM = True` in the next cell to actually delete.
# MAGIC >
# MAGIC > After teardown, run **`Includes/Workspace-Setup.py`** to reinstall.

# COMMAND ----------

# Set to True to actually delete. Leave False for a dry run (plan only).
CONFIRM = False

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.100" pyyaml
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# CONFIRM is reset by restartPython above — set it again here to the same value.
CONFIRM = False

import os
from pathlib import Path


def _notebook_dir() -> str:
    try:
        ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()  # noqa: F821
        return "/Workspace" + os.path.dirname(ctx.notebookPath().get())
    except Exception:
        return os.getcwd()


def _find_installer_dir() -> Path:
    for c in (Path(_notebook_dir()) / "installer",
              Path(os.getcwd()) / "installer",
              Path(os.getcwd()) / "Includes" / "installer"):
        if (c / "teardown.py").exists():
            return c.resolve()
    raise FileNotFoundError("Could not locate Includes/installer/teardown.py near this notebook.")


INSTALLER_DIR = _find_installer_dir()
CONFIG = INSTALLER_DIR / "config.yaml"
print(f"Installer dir: {INSTALLER_DIR}")
print(f"Config       : {CONFIG}")

# COMMAND ----------

import importlib.util

spec = importlib.util.spec_from_file_location("sb_teardown", str(INSTALLER_DIR / "teardown.py"))
teardown = importlib.util.module_from_spec(spec)
spec.loader.exec_module(teardown)

# Dry run when CONFIRM is False (prints the plan). Set CONFIRM = True to delete.
teardown.run(str(CONFIG), confirm=CONFIRM)

# COMMAND ----------

# MAGIC %md
# MAGIC ### After teardown
# MAGIC Run **`Includes/Workspace-Setup.py`** (Run all) to reinstall Solution
# MAGIC Builder from scratch. Then do the one-time first-launch authorization
# MAGIC (open the App URL, accept the consent prompt).
