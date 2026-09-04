# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Build a Solution with Solution Builder
# MAGIC
# MAGIC By the end of this notebook you will have used the **Solution Builder** app to
# MAGIC generate a complete Databricks solution and produced a **Databricks Asset
# MAGIC Bundle (DAB)** you can deploy in your own workspace.
# MAGIC
# MAGIC ### Learning objectives
# MAGIC - Describe a business outcome and have Solution Builder generate a solution.
# MAGIC - Explore the generated assets (data, transformations, an AI/BI dashboard).
# MAGIC - Produce a DAB and understand how to deploy it elsewhere.
# MAGIC
# MAGIC > The app is **already running** (one shared app per workspace). Keep this
# MAGIC > notebook open alongside the app in another browser tab.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — Open the app
# MAGIC
# MAGIC Left sidebar → **Compute** → **Apps** → **solution-builder** → **Open**
# MAGIC (or use the URL printed in **`00 - Start Here`**).
# MAGIC
# MAGIC Accept the one-time **authorization** prompt if you're shown one.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Describe your solution
# MAGIC
# MAGIC On the home page choose **"Describe your story"** and enter a business outcome.
# MAGIC Aim it at a common industry use case, for example:
# MAGIC
# MAGIC - *"A retail demand-forecasting solution: daily store-item sales, a forecast, and
# MAGIC   an AI/BI dashboard showing predicted vs. actual by region."*
# MAGIC - *"A financial-services fraud-monitoring solution: streaming transactions, a
# MAGIC   risk score, and a dashboard of flagged activity by segment."*
# MAGIC - *"A manufacturing predictive-maintenance solution: sensor readings, an anomaly
# MAGIC   signal, and a dashboard of at-risk machines."*
# MAGIC
# MAGIC Be specific about the **industry**, the **data**, and the **decision** the
# MAGIC solution should support. Then let Solution Builder plan and generate.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Review what it built
# MAGIC
# MAGIC As the app builds, it creates real assets in this workspace. Explore them:
# MAGIC
# MAGIC - **Catalog Explorer** → your new catalog/schema and generated tables.
# MAGIC - **Dashboards** → the generated **AI/BI dashboard** (open it and ask Genie a
# MAGIC   question in natural language).
# MAGIC - **Workflows / Jobs** → any pipeline the solution created.
# MAGIC
# MAGIC New projects land in the lab catalog **`solution_builder_lab`** by default.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — Produce and download the DAB
# MAGIC
# MAGIC In the app, export the solution as a **Databricks Asset Bundle**. The DAB is a
# MAGIC portable definition of everything the solution created — you can version it and
# MAGIC deploy it repeatably.
# MAGIC
# MAGIC **Download / save the DAB before the session ends** — this lab workspace is
# MAGIC time-boxed and its assets are cleared afterward.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 — Deploy the DAB in your own workspace (take-home)
# MAGIC
# MAGIC You don't have to deploy here. Take the DAB back to your **own** long-lasting
# MAGIC workspace and deploy it with the Databricks CLI:
# MAGIC
# MAGIC ```bash
# MAGIC databricks bundle validate
# MAGIC databricks bundle deploy -t dev
# MAGIC databricks bundle run <resource_name> -t dev
# MAGIC ```
# MAGIC
# MAGIC That's the payoff of this lab: a solution you designed by describing it, now a
# MAGIC repeatable bundle you own.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎉 You're done
# MAGIC
# MAGIC You used Solution Builder to turn a description into a working Databricks
# MAGIC solution and produced a deployable DAB.
# MAGIC
# MAGIC - Explore the open-source project: [github.com/databricks-solutions/solution-builder](https://github.com/databricks-solutions/solution-builder)
# MAGIC - Try a different industry story and compare what it generates.
