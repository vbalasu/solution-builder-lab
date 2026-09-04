# Databricks notebook source
# MAGIC %md
# MAGIC # 👋 Welcome to the Solution Builder Lab
# MAGIC
# MAGIC In this hands-on lab you'll use **Databricks Solution Builder** — an AI app that
# MAGIC turns a plain-language description of a business problem into a working,
# MAGIC deployable Databricks solution (data, notebooks, jobs, an AI/BI dashboard, and
# MAGIC more), packaged as a **Databricks Asset Bundle (DAB)** you can take anywhere.
# MAGIC
# MAGIC The app is **already installed and running in this workspace** — you don't need
# MAGIC to deploy anything. You'll open it, describe a solution, let it build, and walk
# MAGIC away with a DAB you can deploy in your own workspace.
# MAGIC
# MAGIC | Field | Details |
# MAGIC |---|---|
# MAGIC | Duration | ~60 minutes |
# MAGIC | Level | 200 (intermediate) |
# MAGIC | Audience | Partners & field practitioners |
# MAGIC | What you build | A Databricks solution + a deployable DAB |
# MAGIC | Prerequisites | Basic Databricks workspace navigation; a browser |
# MAGIC
# MAGIC > This is a **shared, time-boxed lab workspace** (Vocareum). Assets are cleared
# MAGIC > after the session — export or deploy your DAB before you finish.

# COMMAND ----------

# MAGIC %md
# MAGIC ## What is Solution Builder?
# MAGIC
# MAGIC Solution Builder (internally **go/solution-builder**) is an open-source app
# MAGIC ([github.com/databricks-solutions/solution-builder](https://github.com/databricks-solutions/solution-builder))
# MAGIC that acts as an AI solutions architect. You describe the outcome you want; it
# MAGIC generates a complete, runnable solution against Databricks — synthetic data,
# MAGIC transformations, an AI/BI dashboard, and the glue to run it — and packages the
# MAGIC whole thing as a **DAB** for repeatable deployment.
# MAGIC
# MAGIC In this lab you'll use it to build a solution aligned to a common industry use
# MAGIC case, then produce a DAB you can deploy in your **own** long-lasting workspace.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Find the running app
# MAGIC
# MAGIC The app is named **`solution-builder`**. You can reach it two ways:
# MAGIC
# MAGIC 1. Left sidebar → **Compute** → **Apps** → **solution-builder** → **Open**, or
# MAGIC 2. Click the URL printed by the cell below.
# MAGIC
# MAGIC If the very first person to open it sees an **authorization/consent** screen,
# MAGIC accept it — that one-time step lets the app act on your behalf.

# COMMAND ----------

# Print this workspace's Solution Builder app URL (best-effort).
try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    app = w.apps.get("solution-builder")
    state = getattr(getattr(app, "app_status", None), "state", "") or "unknown"
    print(f"App    : solution-builder")
    print(f"State  : {state}")
    print(f"Open it: {getattr(app, 'url', '(open via Compute → Apps)')}")
except Exception as e:
    print("Could not read the app automatically — open it via Compute → Apps → solution-builder.")
    print(f"(detail: {e})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next
# MAGIC
# MAGIC Open **`01 - Build a Solution`** to run the workshop step by step.
