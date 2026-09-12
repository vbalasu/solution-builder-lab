#!/usr/bin/env python3
# ============================================================================
# teardown.py — reverse a Solution Builder install (config-driven, PURE PYTHON).
#
# Deletes exactly what workspace-setup.py creates, in reverse order:
#   • the Databricks App          (its managed SP + deployments go with it)
#   • the Lakebase project        (branch, database, and the app-SP role)
#   • the deployer service principal (removed from `admins`, then deleted)
#   • the deployer secret scope   (and the minted OAuth secret in it)
#   • the uploaded app source folder
#
# It DOES NOT touch the Unity Catalog data (default: `solution_builder_lab`) or
# any participant-generated demo assets — those are KEPT. Re-run Workspace-Setup
# afterwards to reinstall from scratch.
#
# SAFE BY DEFAULT: prints a plan and changes nothing unless you pass --confirm.
#
#   ./teardown.py                    # DRY RUN — print the plan, delete nothing
#   ./teardown.py --confirm          # actually delete (uses ./config.yaml)
#   ./teardown.py --config x.yaml --confirm
#
# Notebook (see Includes/Teardown.py): importlib-load this and call
#   teardown.run(CONFIG_PATH, confirm=True)
# ============================================================================
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path

# Reuse the installer's config loader, Config, and pretty-print helpers so names
# and parsing stay identical and nothing is duplicated.
_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ws_installer", str(_HERE / "workspace-setup.py"))
ws = importlib.util.module_from_spec(_spec)          # type: ignore[arg-type]
assert _spec and _spec.loader
_spec.loader.exec_module(ws)                          # importing does not run main()


def _source_path(w, cfg) -> str:
    if cfg.ws_source_path:
        return cfg.ws_source_path.rstrip("/")
    user = w.current_user.me().user_name
    return f"/Workspace/Users/{user}/solution-builder-src/{cfg.app_name}"


def _del_app(w, name: str) -> None:
    from databricks.sdk.errors.base import DatabricksError
    ws.step("Delete the app (its service principal + deployments go with it)")
    try:
        w.apps.get(name)
    except DatabricksError:
        ws.info(f"App '{name}' not found — skipping.")
        return
    try:
        w.apps.stop_and_wait(name)   # a running app can block delete
    except Exception:
        pass
    try:
        w.apps.delete(name)
        ws.ok(f"Deleted app '{name}'.")
    except Exception as e:
        ws.warn(f"App delete error: {e}")


def _del_lakebase(w, pid: str) -> None:
    from databricks.sdk.errors.base import DatabricksError
    ws.step("Delete the Lakebase project (branch, database, app-SP role)")
    try:
        w.api_client.do("GET", f"/api/2.0/postgres/projects/{pid}")
    except DatabricksError:
        ws.info(f"Lakebase project '{pid}' not found — skipping.")
        return
    try:
        w.api_client.do("DELETE", f"/api/2.0/postgres/projects/{pid}")
    except DatabricksError as e:
        ws.warn(f"Lakebase delete error (check the Lakebase UI): {e}")
        return
    # Deletion is ASYNC. Wait for it to fully clear so an immediate reinstall
    # doesn't hit a mid-delete project (a bare GET can still return during it).
    import time
    for _ in range(60):  # up to ~6 min
        try:
            w.api_client.do("GET", f"/api/2.0/postgres/projects/{pid}")
        except DatabricksError:
            ws.ok(f"Deleted Lakebase project '{pid}' (fully cleared).")
            return
        time.sleep(6)
    ws.warn(f"Lakebase project '{pid}' delete issued but still visible after ~6 min; "
            "wait before reinstalling (the installer also handles mid-delete).")


def _del_deployer_sp(w, cfg) -> None:
    from databricks.sdk.service import iam
    ws.step("Delete the deployer service principal (remove from admins first)")
    sp = next((s for s in w.service_principals.list(filter=f'displayName eq "{cfg.sp_name}"')), None)
    if sp is None:
        ws.info(f"Deployer SP '{cfg.sp_name}' not found — skipping.")
        return
    sp_id = str(sp.id)
    admins = next((g for g in w.groups.list(filter='displayName eq "admins"')), None)
    if admins:
        try:
            w.groups.patch(
                admins.id,
                operations=[iam.Patch(op=iam.PatchOp.REMOVE, path=f'members[value eq "{sp_id}"]')],
                schemas=[iam.PatchSchema.URN_IETF_PARAMS_SCIM_API_MESSAGES_2_0_PATCH_OP])
            ws.ok("Removed deployer SP from the 'admins' group.")
        except Exception as e:
            ws.warn(f"Remove-from-admins error (continuing): {e}")
    try:
        w.service_principals.delete(sp_id)
        ws.ok(f"Deleted deployer SP '{cfg.sp_name}' (id={sp_id}); its OAuth secret is invalidated.")
    except Exception as e:
        ws.warn(f"SP delete error: {e}")


def _del_secret_scope(w, scope: str) -> None:
    ws.step("Delete the deployer secret scope")
    try:
        w.secrets.delete_scope(scope)
        ws.ok(f"Deleted secret scope '{scope}'.")
    except Exception as e:
        ws.warn(f"Secret scope delete (may not exist): {e}")


def _del_source(w, path: str) -> None:
    from databricks.sdk.errors.base import DatabricksError
    ws.step("Delete the uploaded app source folder")
    try:
        w.workspace.delete(path, recursive=True)
        ws.ok(f"Deleted uploaded source at {path}.")
    except DatabricksError as e:
        ws.warn(f"Source delete (may not exist): {e}")


def run(config_path: str | os.PathLike | None = None, confirm: bool = False) -> None:
    """Programmatic entrypoint (use this from the Teardown notebook)."""
    cfg_path = Path(config_path or (_HERE / "config.yaml")).resolve()
    if not cfg_path.exists():
        ws.die(f"Config file not found: {cfg_path}")
    cfg = ws.Config(ws.load_yaml(cfg_path), cfg_path)   # no validate(): teardown needs no artifact
    w = ws.make_client(cfg)
    host = (w.config.host or cfg.workspace_url).rstrip("/")
    source_path = _source_path(w, cfg)

    ws.banner("Solution Builder — teardown plan (full install, KEEPS data)")
    for k, v in [
        ("Workspace", host),
        ("App (delete)", cfg.app_name),
        ("Lakebase project (delete)", cfg.lb_project),
        ("Deployer SP (delete)", f"{cfg.sp_name} (also removed from 'admins')"),
        ("Secret scope (delete)", cfg.sp_scope),
        ("App source (delete)", source_path),
        ("KEPT — catalog + data", cfg.default_catalog or "(none configured)"),
    ]:
        print(f"  {ws.BOLD}{k:<26}{ws.RESET} {v}")
    ws.hr()
    ws.warn("Participant-built demo assets (pipelines, dashboards, Genie spaces, "
            "jobs, models) are NOT deleted — some live outside the catalog. Remove "
            "those by hand if needed.")

    if not confirm:
        print()
        ws.warn("DRY RUN — nothing was deleted.")
        ws.info("Re-run with --confirm (CLI) or CONFIRM=True (notebook) to delete.")
        return

    ws.banner(f"Tearing down Solution Builder in {host}")
    _del_app(w, cfg.app_name)
    _del_lakebase(w, cfg.lb_project)
    _del_deployer_sp(w, cfg)
    _del_secret_scope(w, cfg.sp_scope)
    _del_source(w, source_path)

    ws.banner("🧹 Teardown complete")
    ws.hr()
    print(f"Kept: catalog '{cfg.default_catalog}' and all data in it.")
    print("Re-run Includes/Workspace-Setup.py to reinstall from scratch.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Reverse a Solution Builder install "
                                             "(full install teardown; keeps UC data).")
    ap.add_argument("--config", default=None, help="Path to config.yaml (default: alongside this script).")
    ap.add_argument("--confirm", action="store_true", help="Actually delete (default is a dry run).")
    args = ap.parse_args()
    run(args.config, confirm=args.confirm)


if __name__ == "__main__":
    main()
