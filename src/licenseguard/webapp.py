"""Local FastAPI UI for LicenseGuard scan results (MVP)."""

from __future__ import annotations

import csv
import json
import socket
from io import StringIO
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from licenseguard.policy import PolicyConfig, load_policy_file, policy_from_mapping
from licenseguard.scan import scan_requirements_file


def _rows_for_csv(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Same order as dashboard: direct, then transitive."""
    direct: List[Dict[str, Any]] = []
    trans: List[Dict[str, Any]] = []
    for r in rows:
        if r.get("direct"):
            direct.append(r)
        else:
            trans.append(r)
    return direct + trans

# In-memory session state (single-user local server).
_state: Dict[str, Any] = {
    "requirements_path": None,
    "policy_path": None,
    "policy_config": None,
    "check_latest": False,
    "no_cache": False,
    "pypi_cache_file": None,
    "last_result": None,
}


def _pick_port(host: str = "127.0.0.1", start: int = 8000, attempts: int = 10) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    raise OSError(f"no free port in {start}..{start + attempts - 1}")


def _parse_bool_q(raw: Optional[str], default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _resolve_policy(
    policy_query: Optional[str],
    policy_config: Optional[PolicyConfig],
    policy_path_stored: Optional[str],
) -> Optional[PolicyConfig]:
    if policy_query:
        p = Path(policy_query)
        if not p.is_file():
            raise HTTPException(status_code=400, detail=f"policy file not found: {policy_query}")
        return load_policy_file(p)
    if policy_config is not None:
        return policy_config
    if policy_path_stored:
        pp = Path(policy_path_stored)
        if pp.is_file():
            return load_policy_file(pp)
    return None


def create_app() -> FastAPI:
    app = FastAPI(title="LicenseGuard", version="0.3.0")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return _INDEX_HTML

    @app.get("/scan")
    async def scan(
        check_latest: Optional[str] = Query(None),
        no_cache: Optional[str] = Query(None),
        policy: Optional[str] = Query(None, description="Optional path to policy file"),
    ) -> JSONResponse:
        req = _state.get("requirements_path")
        if not req:
            raise HTTPException(status_code=400, detail="requirements path not set")
        path = Path(req)
        if not path.is_file():
            raise HTTPException(status_code=400, detail=f"requirements file not found: {path}")

        cl = _parse_bool_q(check_latest, bool(_state.get("check_latest")))
        nc = _parse_bool_q(no_cache, bool(_state.get("no_cache")))
        pcache = _state.get("pypi_cache_file")
        pcache_path = Path(pcache) if pcache and cl and not nc else None

        try:
            pol = _resolve_policy(policy, _state.get("policy_config"), _state.get("policy_path"))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        result = scan_requirements_file(
            path,
            policy=pol,
            check_latest=cl,
            pypi_cache_file=pcache_path,
            pypi_no_cache=nc,
        )
        _state["last_result"] = result
        return JSONResponse(content=result)

    @app.post("/policy")
    async def set_policy(body: Dict[str, Any]) -> JSONResponse:
        try:
            cfg = policy_from_mapping(body)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        _state["policy_config"] = cfg
        _state["policy_path"] = None
        return JSONResponse({"ok": True, "message": "policy updated in memory"})

    @app.get("/download")
    async def download() -> StreamingResponse:
        data = _state.get("last_result")
        if not data:
            raise HTTPException(status_code=404, detail="no scan result yet; run GET /scan first")
        payload = json.dumps(data, indent=2, sort_keys=True)
        return StreamingResponse(
            iter([payload + "\n"]),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="licenseguard-report.json"'},
        )

    @app.get("/download/csv")
    async def download_csv() -> StreamingResponse:
        data = _state.get("last_result")
        if not data:
            raise HTTPException(status_code=404, detail="no scan result yet; run GET /scan first")
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "package",
                "version",
                "license_spdx",
                "status",
                "direct",
                "reason",
                "change_type",
            ]
        )
        for row in _rows_for_csv(list(data.get("rows") or [])):
            ver = row.get("version_installed") or row.get("version") or ""
            writer.writerow(
                [
                    row.get("package", ""),
                    ver,
                    row.get("license_spdx", ""),
                    row.get("status", ""),
                    "yes" if row.get("direct") else "no",
                    row.get("reason", ""),
                    row.get("change_type", "") or "",
                ]
            )
        out = buf.getvalue()
        return StreamingResponse(
            iter([out]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="licenseguard-report.csv"'},
        )

    return app


def configure_state(
    *,
    requirements_path: Path,
    policy_path: Optional[Path],
    policy_config: Optional[PolicyConfig],
    check_latest: bool,
    no_cache: bool,
    pypi_cache_file: Optional[Path],
) -> None:
    _state["requirements_path"] = str(requirements_path.resolve())
    _state["policy_path"] = str(policy_path.resolve()) if policy_path else None
    _state["policy_config"] = policy_config
    _state["check_latest"] = check_latest
    _state["no_cache"] = no_cache
    _state["pypi_cache_file"] = str(pypi_cache_file.resolve()) if pypi_cache_file else None
    _state["last_result"] = None


def run_web_ui(
    *,
    requirements_path: Path,
    policy_path: Optional[Path],
    policy_config: Optional[PolicyConfig],
    check_latest: bool,
    no_cache: bool,
    pypi_cache_file: Optional[Path],
    host: str = "127.0.0.1",
    port: int = 8000,
) -> int:
    configure_state(
        requirements_path=requirements_path,
        policy_path=policy_path,
        policy_config=policy_config,
        check_latest=check_latest,
        no_cache=no_cache,
        pypi_cache_file=pypi_cache_file,
    )
    actual = _pick_port(host, start=port)
    url = f"http://{host}:{actual}"
    app = create_app()

    def open_browser() -> None:
        time.sleep(0.5)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn

    print(f"LicenseGuard web UI: {url}", flush=True)
    print(f"Requirements: {requirements_path.resolve()}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    uvicorn.run(app, host=host, port=actual, log_level="info")
    return 0


_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>LicenseGuard</title>
  <style>
    :root {
      --bg-page: #f5f7fa;
      --bg-card: #ffffff;
      --border: #e2e6ec;
      --text: #1a1d21;
      --text-muted: #5c6570;
      --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04);
      --table-head: #f0f3f7;
      --table-row-alt: #fafbfc;
      --table-hover: #eef6ff;
      --input-bg: #fff;
      --input-border: #cfd4dc;
      --badge-yes: #e8f5e9;
      --badge-yes-text: #1b5e20;
      --badge-no: #f5f5f5;
      --badge-no-text: #616161;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 15px;
      line-height: 1.5;
      color: var(--text);
      background: var(--bg-page);
    }
    html {
      transition: background-color 0.3s ease, color 0.3s ease;
    }
    body.dark {
      --bg-page: #1e1e1e;
      --bg-card: #2c2c2c;
      --border: #404040;
      --text: #e8eaed;
      --text-muted: #9aa0a6;
      --shadow: 0 2px 8px rgba(0,0,0,0.35);
      --table-head: #383838;
      --table-row-alt: #333333;
      --table-hover: #3d4f5c;
      --input-bg: #363636;
      --input-border: #555;
      --badge-yes: #1e3a24;
      --badge-yes-text: #a5d6a7;
      --badge-no: #3a3a3a;
      --badge-no-text: #bdbdbd;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      transition: background-color 0.3s ease, color 0.3s ease;
    }
    .page {
      max-width: 1100px;
      margin: 0 auto;
      padding: 1.25rem 1rem 2.5rem;
    }
    .site-header {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }
    .site-header h1 {
      font-size: 1.5rem;
      font-weight: 600;
      margin: 0 0 0.25rem;
      letter-spacing: -0.02em;
    }
    .subtitle { margin: 0; font-size: 0.9rem; color: var(--text-muted); max-width: 28rem; }
    .btn-theme {
      font: inherit;
      padding: 0.5rem 0.85rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg-card);
      color: var(--text);
      cursor: pointer;
      box-shadow: var(--shadow);
      white-space: nowrap;
      transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, filter 0.2s ease;
    }
    .btn-theme:hover { filter: brightness(0.97); }
    body.dark .btn-theme:hover { filter: brightness(1.08); }
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.1rem 1.15rem;
      margin-bottom: 1rem;
      box-shadow: var(--shadow);
      transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .card-title {
      font-size: 0.95rem;
      font-weight: 600;
      margin: 0 0 0.75rem;
      color: var(--text);
    }
    .muted { font-size: 0.85rem; color: var(--text-muted); margin: 0 0 0.75rem; }
    .label-hint { font-weight: 400; color: var(--text-muted); margin: 0; display: inline; }
    .chart-panel {
      margin-bottom: 1rem;
      padding: 1rem;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: rgba(0, 0, 0, 0.02);
      transition: background-color 0.3s ease, border-color 0.3s ease;
    }
    body.dark .chart-panel { background: rgba(255, 255, 255, 0.04); }
    .chart-panel .card-title { margin-bottom: 0.5rem; }
    .row { display: flex; flex-wrap: wrap; gap: 0.65rem 1rem; align-items: center; margin-bottom: 0.7rem; }
    .row:last-child { margin-bottom: 0; }
    .row-stretch { align-items: stretch; }
    label.field {
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
      font-size: 0.85rem;
      color: var(--text-muted);
      flex: 1 1 220px;
      min-width: 0;
    }
    .scan-toolbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.75rem 1rem;
    }
    .scan-toolbar .primary-scan {
      padding: 0.65rem 1.35rem;
      font-size: 1rem;
      font-weight: 600;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(13, 110, 253, 0.35);
    }
    body.dark .scan-toolbar .primary-scan {
      box-shadow: 0 2px 10px rgba(13, 110, 253, 0.25);
    }
    .scan-toolbar-downloads {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
    }
    .scan-meta {
      margin-top: 0.65rem;
      padding-top: 0.5rem;
      border-top: 1px solid var(--border);
    }
    .scan-status-line {
      margin: 0 0 0.35rem;
      font-size: 0.8rem;
      color: var(--text-muted);
      min-height: 1.25em;
      transition: opacity 0.2s ease;
    }
    .scan-cli-hint {
      margin: 0;
      font-size: 0.72rem;
      color: var(--text-muted);
      opacity: 0.88;
    }
    .empty-state {
      text-align: center;
      padding: 2.25rem 1.25rem;
      min-height: 11rem;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);
      font-size: 1.05rem;
      line-height: 1.45;
      transition: opacity 0.25s ease;
    }
    .empty-state.hidden { display: none; }
    .empty-state p { margin: 0; max-width: 22rem; }
    .results-panel {
      transition: opacity 0.2s ease;
    }
    .results-panel.results-panel--hidden {
      display: none;
    }
    input[type="text"], select {
      padding: 0.5rem 0.65rem;
      border: 1px solid var(--input-border);
      border-radius: 8px;
      font: inherit;
      width: 100%;
      background: var(--input-bg);
      color: var(--text);
    }
    select { cursor: pointer; max-width: 100%; }
    button.primary {
      padding: 0.5rem 1.1rem;
      border-radius: 8px;
      font: inherit;
      font-weight: 500;
      cursor: pointer;
      border: none;
      background: #0d6efd;
      color: #fff;
    }
    button.primary:disabled { opacity: 0.55; cursor: not-allowed; }
    button.secondary {
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font: inherit;
      cursor: pointer;
      border: 1px solid var(--input-border);
      background: var(--bg-card);
      color: var(--text);
      transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }
    button.btn-download {
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font: inherit;
      cursor: pointer;
      border: none;
      background: #198754;
      color: #fff;
    }
    button.btn-download:disabled { opacity: 0.45; cursor: not-allowed; }
    .loading-overlay {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 100;
      background: rgba(0,0,0,0.25);
      align-items: center;
      justify-content: center;
      backdrop-filter: blur(2px);
    }
    body.dark .loading-overlay { background: rgba(0,0,0,0.5); }
    .loading-overlay.visible { display: flex; }
    .loading-box {
      background: var(--bg-card);
      color: var(--text);
      padding: 1.5rem 2rem;
      border-radius: 12px;
      box-shadow: var(--shadow);
      font-weight: 500;
      border: 1px solid var(--border);
      transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }
    .banner-error, .banner-warn {
      border-radius: 10px;
      padding: 0.75rem 1rem;
      font-size: 0.9rem;
      white-space: pre-wrap;
      margin-bottom: 1rem;
      display: none;
    }
    .banner-error.visible, .banner-warn.visible { display: block; }
    .banner-error {
      background: #fde8e8;
      color: #8b1a1a;
      border: 1px solid #f5b5b5;
    }
    body.dark .banner-error {
      background: #3d2020;
      color: #ffcdd2;
      border-color: #6b3030;
    }
    .banner-warn {
      background: #fff8e1;
      color: #6d5a00;
      border: 1px solid #ffe082;
    }
    body.dark .banner-warn {
      background: #3d3520;
      color: #ffe082;
      border-color: #6d5a30;
    }
    .policy-confirm {
      margin-top: 0.65rem;
      font-size: 0.88rem;
      color: #198754;
      font-weight: 500;
      min-height: 1.25em;
    }
    body.dark .policy-confirm { color: #81c784; }
    .summary-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 0.65rem;
      margin-bottom: 1rem;
    }
    .stat-badge {
      flex: 1 1 120px;
      min-width: 100px;
      padding: 0.65rem 0.85rem;
      border-radius: 10px;
      font-size: 0.88rem;
      font-weight: 600;
      text-align: center;
      border: 1px solid transparent;
      transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }
    .stat-badge .stat-label { display: block; font-size: 0.72rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.15rem; }
    .stat-approved { background: #e8f5e9; color: #1b5e20; border-color: #a5d6a7; }
    .stat-restricted { background: #fff3e0; color: #e65100; border-color: #ffcc80; }
    .stat-denied { background: #ffebee; color: #b71c1c; border-color: #ef9a9a; }
    .stat-unknown { background: #eceff1; color: #455a64; border-color: #b0bec5; }
    body.dark .stat-approved { background: #1e3a24; color: #a5d6a7; border-color: #2e7d32; }
    body.dark .stat-restricted { background: #3d2e1a; color: #ffb74d; border-color: #ef6c00; }
    body.dark .stat-denied { background: #3d1a1a; color: #ef9a9a; border-color: #c62828; }
    body.dark .stat-unknown { background: #37474f; color: #cfd8dc; border-color: #546e7a; }
    .chart-wrap { overflow-x: auto; padding: 0.25rem 0; }
    .chart-wrap canvas {
      display: block;
      margin: 0 auto;
      max-width: 100%;
      height: auto;
      cursor: default;
    }
    .chart-wrap canvas.can-click { cursor: pointer; }
    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: flex-end;
      margin-bottom: 0.75rem;
    }
    .filters .field-filter { flex: 1 1 200px; min-width: 140px; margin: 0; }
    .filters .field-filter-narrow { flex: 0 1 180px; min-width: 140px; }
    .filters-actions { display: flex; align-items: flex-end; gap: 0.5rem; flex-wrap: wrap; }
    .result-count {
      width: 100%;
      flex-basis: 100%;
      font-size: 0.88rem;
      color: var(--text-muted);
      margin: 0 0 0.35rem;
      min-height: 1.35em;
      transition: color 0.3s ease;
    }
    .table-scroll {
      max-height: min(55vh, 520px);
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: 10px;
      -webkit-overflow-scrolling: touch;
      transition: border-color 0.3s ease;
    }
    .table-scroll table { width: 100%; min-width: 640px; border-collapse: collapse; font-size: 0.86rem; }
    .table-scroll th, .table-scroll td {
      text-align: left;
      padding: 0.5rem 0.6rem;
      border-bottom: 1px solid var(--border);
      transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }
    .table-scroll th {
      position: sticky;
      top: 0;
      background: var(--table-head);
      font-weight: 600;
      z-index: 2;
      color: var(--text);
    }
    .th-sortable {
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }
    .th-sortable:hover { filter: brightness(0.97); }
    body.dark .th-sortable:hover { filter: brightness(1.12); }
    .sort-ind {
      font-size: 0.75em;
      opacity: 0.65;
      margin-left: 0.15rem;
    }
    mark {
      background: #fff3cd;
      color: inherit;
      padding: 0 0.06em;
      border-radius: 2px;
    }
    body.dark mark {
      background: #6d5c20;
      color: #fff8e1;
    }
    .table-scroll tbody tr:nth-child(even) { background: var(--table-row-alt); }
    .table-scroll tbody tr:hover { background: var(--table-hover); }
    .table-scroll tbody tr.hidden { display: none; }
    .pill {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.02em;
      transition: background-color 0.3s ease, color 0.3s ease;
    }
    .pill-approved { background: #e8f5e9; color: #1b5e20; }
    .pill-restricted { background: #fff3e0; color: #e65100; }
    .pill-denied { background: #ffebee; color: #b71c1c; }
    .pill-unknown { background: #eceff1; color: #455a64; }
    body.dark .pill-approved { background: #1e3a24; color: #a5d6a7; }
    body.dark .pill-restricted { background: #3d2e1a; color: #ffb74d; }
    body.dark .pill-denied { background: #3d1a1a; color: #ef9a9a; }
    body.dark .pill-unknown { background: #37474f; color: #cfd8dc; }
    .pill-yes { background: var(--badge-yes); color: var(--badge-yes-text); }
    .pill-no { background: var(--badge-no); color: var(--badge-no-text); }
    .unknown-hint {
      cursor: help;
      font-size: 0.85em;
      opacity: 0.75;
      margin-left: 0.2rem;
      vertical-align: middle;
    }
    .status-sub {
      font-size: 0.72em;
      font-weight: 500;
      opacity: 0.82;
      margin-left: 0.28em;
      white-space: nowrap;
    }
    .lg-load-more-tr { background: transparent !important; }
    .lg-load-more-tr td { text-align: center; padding: 0.45rem; border-bottom: 1px solid var(--border); }
    .dep-section { margin-bottom: 0.9rem; }
    .dep-toggle {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      width: 100%;
      text-align: left;
      padding: 0.55rem 0.75rem;
      font: inherit;
      font-weight: 600;
      font-size: 0.92rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--table-head);
      color: var(--text);
      cursor: pointer;
      margin-bottom: 0.4rem;
      transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
    }
    .dep-chevron {
      display: inline-block;
      transition: transform 0.2s ease;
      font-size: 0.7rem;
      opacity: 0.8;
    }
    .dep-toggle[aria-expanded="false"] .dep-chevron { transform: rotate(-90deg); }
    .dep-panel { margin-bottom: 0.25rem; }
    .dep-panel.collapsed { display: none; }
    .dep-table { width: 100%; min-width: 520px; border-collapse: collapse; font-size: 0.86rem; }
    .sr-hint { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
  </style>
</head>
<body>
  <div id="loading_overlay" class="loading-overlay" aria-hidden="true">
    <div class="loading-box">Scanning dependencies…</div>
  </div>

  <div class="page">
    <header class="site-header">
      <div>
        <h1>LicenseGuard Dashboard</h1>
        <p class="subtitle">Dependency license compliance &amp; drift detection</p>
      </div>
      <button type="button" class="btn-theme" id="btn_theme" aria-pressed="false">🌙 Dark Mode</button>
    </header>

    <div id="banner_error" class="banner-error" role="alert"></div>
    <div id="banner_warn" class="banner-warn"></div>

    <section class="card" aria-labelledby="scan-actions-heading">
      <h2 class="card-title" id="scan-actions-heading">Scan</h2>
      <div class="scan-toolbar">
        <button type="button" class="primary primary-scan" id="btn_run">Run scan</button>
        <div class="scan-toolbar-downloads">
          <button type="button" class="btn-download" id="btn_download" disabled>Download JSON</button>
          <button type="button" class="btn-download" id="btn_download_csv" disabled>Download CSV</button>
        </div>
      </div>
      <div class="scan-meta">
        <p id="scan_status" class="scan-status-line" aria-live="polite"></p>
        <p class="scan-cli-hint">Advanced options available via CLI</p>
      </div>
    </section>

    <section class="card" aria-labelledby="policy-inline">
      <h2 class="card-title" id="policy-inline">Policy (in memory)</h2>
      <p class="muted">Comma-separated license tokens. Used on the next scan; overrides file policy when applied.</p>
      <div class="row row-stretch">
        <label class="field">Approved licenses
          <input type="text" id="pol_approved" placeholder="MIT, BSD, Apache"/>
        </label>
      </div>
      <div class="row row-stretch">
        <label class="field">Restricted licenses
          <input type="text" id="pol_restricted" placeholder="LGPL, MPL"/>
        </label>
      </div>
      <div class="row row-stretch">
        <label class="field">Denied licenses
          <input type="text" id="pol_denied" placeholder="GPL"/>
        </label>
      </div>
      <div class="row">
        <button type="button" class="secondary" id="btn_apply_policy">Apply policy</button>
      </div>
      <div id="pol_confirm" class="policy-confirm" aria-live="polite"></div>
    </section>

    <section class="card" aria-labelledby="results-heading">
      <h2 class="card-title" id="results-heading">Scan results</h2>
      <div id="empty_state" class="empty-state" role="status">
        <p>Click &quot;Run scan&quot; to analyze your dependencies</p>
      </div>
      <div id="results_panel" class="results-panel results-panel--hidden">
      <div id="summary_bar" class="summary-bar"></div>
      <div class="chart-panel">
        <div class="card-title">License distribution</div>
        <div class="chart-wrap">
          <canvas id="dist_chart" width="560" height="200" tabindex="0" role="img" aria-label="Bar chart of license status counts; click a bar to filter by status"></canvas>
        </div>
      </div>
      <div class="filters">
        <label class="field field-filter">
          Search
          <input type="text" id="filter_search" placeholder="Search packages..." autocomplete="off"/>
        </label>
        <label class="field field-filter field-filter-narrow">
          Status
          <select id="filter_status" aria-label="Filter by status">
            <option value="">All</option>
            <option value="APPROVED">Approved</option>
            <option value="RESTRICTED">Restricted</option>
            <option value="DENIED">Denied</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
        </label>
        <div class="filters-actions">
          <button type="button" class="secondary" id="btn_clear_filters">Clear filters</button>
        </div>
      </div>
      <p class="result-count" id="result_count" aria-live="polite"></p>
      <div id="dep_tables">
        <div class="dep-section">
          <button type="button" class="dep-toggle" id="toggle_direct" aria-expanded="true">
            <span class="dep-chevron" aria-hidden="true">▼</span>
            Direct Dependencies (<span id="cnt_direct">0</span>)
          </button>
          <div class="dep-panel" id="panel_direct">
            <div class="table-scroll">
              <table class="dep-table" id="tbl_direct" aria-label="Direct dependencies">
                <thead>
                  <tr>
                    <th class="th-sortable" data-sort="package" scope="col">Package<span class="sort-ind" aria-hidden="true"></span></th>
                    <th scope="col">Version</th>
                    <th class="th-sortable" data-sort="license" scope="col">License<span class="sort-ind" aria-hidden="true"></span></th>
                    <th class="th-sortable" data-sort="status" scope="col">Status<span class="sort-ind" aria-hidden="true"></span></th>
                    <th scope="col">Direct</th>
                  </tr>
                </thead>
                <tbody id="tbody_direct"></tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="dep-section">
          <button type="button" class="dep-toggle" id="toggle_transitive" aria-expanded="true">
            <span class="dep-chevron" aria-hidden="true">▼</span>
            Transitive Dependencies (<span id="cnt_transitive">0</span>)
          </button>
          <div class="dep-panel" id="panel_transitive">
            <div class="table-scroll">
              <table class="dep-table" id="tbl_transitive" aria-label="Transitive dependencies">
                <thead>
                  <tr>
                    <th class="th-sortable" data-sort="package" scope="col">Package<span class="sort-ind" aria-hidden="true"></span></th>
                    <th scope="col">Version</th>
                    <th class="th-sortable" data-sort="license" scope="col">License<span class="sort-ind" aria-hidden="true"></span></th>
                    <th class="th-sortable" data-sort="status" scope="col">Status<span class="sort-ind" aria-hidden="true"></span></th>
                    <th scope="col">Direct</th>
                  </tr>
                </thead>
                <tbody id="tbody_transitive"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      </div>
    </section>
  </div>

  <script>
    const $ = (id) => document.getElementById(id);
    const THEME_KEY = "licenseguard-theme";
    const LG_STATE_KEY = "licenseguard_state";
    const ROW_PAGE = 100;
    const CHART_STATUSES = ["APPROVED", "RESTRICTED", "DENIED", "UNKNOWN"];

    let scanRows = [];
    let sortKey = null;
    let sortDir = "asc";
    let lastPartition = { direct: [], transitive: [] };
    let limits = { direct: ROW_PAGE, transitive: ROW_PAGE };
    let renderedLazyTrans = false;
    let searchDebounce = null;

    function splitCsv(s) {
      return String(s || "").split(",").map(function (x) { return x.trim(); }).filter(Boolean);
    }

    function escapeHtml(s) {
      return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
    }

    function highlightPlain(text, qLower) {
      var s = String(text);
      if (!qLower) return escapeHtml(s);
      var lower = s.toLowerCase();
      var qlen = qLower.length;
      var out = "";
      var i = 0;
      while (i < s.length) {
        var idx = lower.indexOf(qLower, i);
        if (idx === -1) {
          out += escapeHtml(s.slice(i));
          break;
        }
        out += escapeHtml(s.slice(i, idx));
        out += "<mark>" + escapeHtml(s.slice(idx, idx + qlen)) + "</mark>";
        i = idx + qlen;
      }
      return out;
    }

    function statusPillClass(st) {
      var u = String(st || "").toUpperCase();
      if (u === "APPROVED") return "pill pill-approved";
      if (u === "RESTRICTED") return "pill pill-restricted";
      if (u === "DENIED") return "pill pill-denied";
      return "pill pill-unknown";
    }

    function rowVersion(r) {
      if (r.version_installed != null && r.version_installed !== "") return r.version_installed;
      if (r.version != null && r.version !== "") return r.version;
      return "-";
    }

    function licenseText(r) {
      var spdx = r.license_spdx;
      if (spdx != null && spdx !== "") return spdx;
      if (r.license_detected != null && r.license_detected !== "") return r.license_detected;
      return "-";
    }

    function attrEscape(s) {
      return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    function unknownSuffix(ut) {
      if (ut === "no_metadata") return '<span class="status-sub">(no metadata)</span>';
      if (ut === "unrecognized") return '<span class="status-sub">(unrecognized)</span>';
      return "";
    }

    function statusCellHtml(st, qLower, reason, unknownType) {
      var u = String(st || "").toUpperCase();
      var inner = highlightPlain(String(st), qLower);
      var sub = u === "UNKNOWN" ? unknownSuffix(unknownType) : "";
      var pill = '<span class="' + statusPillClass(st) + '">' + inner + sub + "</span>";
      if (u === "UNKNOWN") {
        var t = attrEscape(reason || "");
        pill += ' <span class="unknown-hint" title="' + t + '" aria-label="' + t + '">ℹ</span>';
      }
      return pill;
    }

    function partitionRows(rows) {
      var direct = [];
      var trans = [];
      (rows || []).forEach(function (r) {
        if (r.direct) direct.push(r);
        else trans.push(r);
      });
      return { direct: direct, transitive: trans };
    }

    function bindDepToggle(btnId, panelId, lazyKind) {
      $(btnId).addEventListener("click", function () {
        var panel = $(panelId);
        var wasCollapsed = panel.classList.contains("collapsed");
        panel.classList.toggle("collapsed");
        var hidden = panel.classList.contains("collapsed");
        this.setAttribute("aria-expanded", hidden ? "false" : "true");
        if (lazyKind && wasCollapsed && !hidden) {
          if (lazyKind === "transitive" && !renderedLazyTrans) {
            renderedLazyTrans = true;
            renderSection("transitive");
            applyRowFilter();
          }
        }
      });
    }

    function saveUiState() {
      try {
        var o = {
          search: $("filter_search").value,
          status: $("filter_status").value || "ALL"
        };
        localStorage.setItem(LG_STATE_KEY, JSON.stringify(o));
      } catch (e) {}
    }

    function loadUiState() {
      try {
        var raw = localStorage.getItem(LG_STATE_KEY);
        if (!raw) return;
        var s = JSON.parse(raw);
        if (s.search != null) $("filter_search").value = s.search;
        $("filter_status").value = s.status === "ALL" || s.status == null || s.status === "" ? "" : s.status;
      } catch (e) {}
    }

    function renderSection(kind) {
      var rows = lastPartition[kind];
      var tbodyId = kind === "direct" ? "tbody_direct" : "tbody_transitive";
      var tb = $(tbodyId);
      if (!tb) return;
      var qLower = $("filter_search").value.trim().toLowerCase();
      var lim = limits[kind];
      var slice = rows.slice(0, lim);
      var html = slice.map(function (r) { return buildRowHtml(r, qLower); }).join("");
      if (rows.length > lim) {
        var rem = rows.length - lim;
        html += '<tr class="lg-load-more-tr"><td colspan="5"><button type="button" class="secondary lg-load-more" data-section="' + kind + '">Load more (' + rem + " more)</button></td></tr>";
      }
      tb.innerHTML = html;
    }

    function initTheme() {
      var dark = localStorage.getItem(THEME_KEY) === "dark";
      if (dark) document.body.classList.add("dark");
      updateThemeToggle();
    }

    function updateThemeToggle() {
      var dark = document.body.classList.contains("dark");
      $("btn_theme").setAttribute("aria-pressed", dark ? "true" : "false");
      $("btn_theme").textContent = dark ? "☀ Light Mode" : "🌙 Dark Mode";
    }

    function toggleTheme() {
      document.body.classList.toggle("dark");
      localStorage.setItem(THEME_KEY, document.body.classList.contains("dark") ? "dark" : "light");
      updateThemeToggle();
      var s = window.lastSummary;
      if (s) drawDistributionChart(s);
    }

    function setBanners(err, warn) {
      var be = $("banner_error");
      var bw = $("banner_warn");
      if (err) {
        be.textContent = err;
        be.classList.add("visible");
      } else {
        be.textContent = "";
        be.classList.remove("visible");
      }
      if (warn) {
        bw.textContent = warn;
        bw.classList.add("visible");
      } else {
        bw.textContent = "";
        bw.classList.remove("visible");
      }
    }

    function setLoading(on) {
      $("loading_overlay").classList.toggle("visible", on);
      $("loading_overlay").setAttribute("aria-hidden", on ? "false" : "true");
      $("btn_run").disabled = on;
    }

    function renderSummaryBar(s) {
      window.lastSummary = s;
      var el = $("summary_bar");
      if (!s || s.total == null && s.approved == null) {
        el.innerHTML = "";
        return;
      }
      var parts = [
        ["Approved", s.approved != null ? s.approved : "—", "stat-badge stat-approved"],
        ["Restricted", s.restricted != null ? s.restricted : "—", "stat-badge stat-restricted"],
        ["Denied", s.denied != null ? s.denied : "—", "stat-badge stat-denied"],
        ["Unknown", s.unknown != null ? s.unknown : "—", "stat-badge stat-unknown"]
      ];
      el.innerHTML = parts.map(function (p) {
        return '<div class="' + p[2] + '"><span class="stat-label">' + p[0] + "</span>" + escapeHtml(String(p[1])) + "</div>";
      }).join("");
    }

    function chartLabelColor() {
      return document.body.classList.contains("dark") ? "#b0b0b0" : "#444";
    }

    function layoutChart(summary) {
      var c = $("dist_chart");
      var w = c.width;
      var h = c.height;
      var empty = { w: w, h: h, cols: [], vals: [0, 0, 0, 0], n: 4, draw: false };
      if (!summary) return empty;
      var a = Number(summary.approved) || 0;
      var r = Number(summary.restricted) || 0;
      var d = Number(summary.denied) || 0;
      var u = Number(summary.unknown) || 0;
      var vals = [a, r, d, u];
      var labels = ["Approved", "Restricted", "Denied", "Unknown"];
      var colors = ["#2e7d32", "#ef6c00", "#c62828", "#757575"];
      var max = Math.max.apply(null, vals.concat([1]));
      var padL = 12;
      var padR = 12;
      var padB = 36;
      var padT = 16;
      var innerW = w - padL - padR;
      var n = 4;
      var gap = 14;
      var barW = (innerW - gap * (n - 1)) / n;
      var maxBarH = h - padT - padB;
      var baseY = h - padB;
      var cols = [];
      for (var i = 0; i < n; i++) {
        var x = padL + i * (barW + gap);
        cols.push({ x0: x, x1: x + barW, y0: padT, y1: h, status: CHART_STATUSES[i] });
      }
      return {
        w: w,
        h: h,
        cols: cols,
        vals: vals,
        labels: labels,
        colors: colors,
        max: max,
        padL: padL,
        padR: padR,
        padB: padB,
        padT: padT,
        barW: barW,
        gap: gap,
        n: n,
        maxBarH: maxBarH,
        baseY: baseY,
        draw: true,
      };
    }

    function drawDistributionChart(summary) {
      var c = $("dist_chart");
      if (!c || !c.getContext) return;
      var ctx = c.getContext("2d");
      var L = layoutChart(summary);
      window.lastChartLayout = L.draw ? L : null;
      ctx.clearRect(0, 0, L.w, L.h);
      if (!L.draw) {
        c.classList.remove("can-click");
        return;
      }
      ctx.font = "11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
      for (var i = 0; i < L.n; i++) {
        var bh = L.max > 0 ? (L.vals[i] / L.max) * L.maxBarH : 0;
        var x = L.padL + i * (L.barW + L.gap);
        ctx.fillStyle = L.colors[i];
        ctx.fillRect(x, L.baseY - bh, L.barW, bh);
        ctx.fillStyle = chartLabelColor();
        ctx.textAlign = "center";
        ctx.fillText(String(L.vals[i]), x + L.barW / 2, L.baseY - bh - 6);
        ctx.fillText(L.labels[i], x + L.barW / 2, L.h - 10);
      }
      c.classList.add("can-click");
    }

    function canvasDeviceXY(ev, canvas) {
      var r = canvas.getBoundingClientRect();
      var sx = canvas.width / r.width;
      var sy = canvas.height / r.height;
      return { x: (ev.clientX - r.left) * sx, y: (ev.clientY - r.top) * sy };
    }

    function chartHitStatus(mx, my) {
      var L = window.lastChartLayout;
      if (!L || !L.cols || !L.cols.length) return null;
      for (var i = 0; i < L.cols.length; i++) {
        var col = L.cols[i];
        if (mx >= col.x0 && mx <= col.x1 && my >= col.y0 && my <= col.y1) return col.status;
      }
      return null;
    }

    function onChartClick(ev) {
      var c = $("dist_chart");
      if (!c.classList.contains("can-click")) return;
      var p = canvasDeviceXY(ev, c);
      var st = chartHitStatus(p.x, p.y);
      if (!st) return;
      $("filter_status").value = st;
      saveUiState();
      applyRowFilter();
    }

    function onChartMouseMove(ev) {
      var c = $("dist_chart");
      if (!c.classList.contains("can-click")) {
        c.style.cursor = "default";
        return;
      }
      var p = canvasDeviceXY(ev, c);
      c.style.cursor = chartHitStatus(p.x, p.y) ? "pointer" : "default";
    }

    function getSortedScanRows() {
      var rows = scanRows.slice();
      if (!sortKey) return rows;
      var mult = sortDir === "desc" ? -1 : 1;
      rows.sort(function (a, b) {
        var va;
        var vb;
        if (sortKey === "package") {
          va = (a.package || "").toLowerCase();
          vb = (b.package || "").toLowerCase();
        } else if (sortKey === "license") {
          va = licenseText(a).toLowerCase();
          vb = licenseText(b).toLowerCase();
        } else {
          va = String(a.status || "").toLowerCase();
          vb = String(b.status || "").toLowerCase();
        }
        if (va < vb) return -1 * mult;
        if (va > vb) return 1 * mult;
        return 0;
      });
      return rows;
    }

    function buildRowHtml(r, qLower) {
      var ver = rowVersion(r);
      var lic = licenseText(r);
      var st = r.status != null ? r.status : "UNKNOWN";
      var stUpper = String(st).toUpperCase();
      var pkg = r.package != null ? r.package : "-";
      var searchBlob = (pkg + " " + lic + " " + st).toLowerCase();
      var reason = r.reason != null ? r.reason : "";
      var ut = r.unknown_type != null ? r.unknown_type : null;
      var stHtml = statusCellHtml(st, qLower, reason, ut);
      return (
        '<tr data-status="' + escapeHtml(stUpper) + '" data-search="' + escapeHtml(searchBlob) + '">' +
        "<td>" + highlightPlain(pkg, qLower) + "</td>" +
        "<td>" + escapeHtml(String(ver)) + "</td>" +
        "<td>" + highlightPlain(String(lic), qLower) + "</td>" +
        "<td>" + stHtml + "</td>" +
        '<td><span class="pill ' + (r.direct ? "pill-yes" : "pill-no") + '">' + (r.direct ? "Yes" : "No") + "</span></td>" +
        "</tr>"
      );
    }

    function updateSortHeaders() {
      document.querySelectorAll("#dep_tables thead [data-sort]").forEach(function (th) {
        var ind = th.querySelector(".sort-ind");
        var k = th.getAttribute("data-sort");
        if (sortKey === k) ind.textContent = sortDir === "asc" ? "↑" : "↓";
        else ind.textContent = "";
      });
    }

    function updateResultCount() {
      var el = $("result_count");
      var total = scanRows.length;
      if (!total) {
        el.textContent = "";
        return;
      }
      var visible = 0;
      document.querySelectorAll("#dep_tables tbody tr").forEach(function (tr) {
        if (tr.classList.contains("lg-load-more-tr")) return;
        if (!tr.classList.contains("hidden")) visible++;
      });
      el.textContent = "Showing " + visible + " of " + total + " packages";
    }

    function applyRowFilter() {
      var q = $("filter_search").value.trim().toLowerCase();
      var st = $("filter_status").value;
      document.querySelectorAll("#dep_tables tbody tr").forEach(function (tr) {
        if (tr.classList.contains("lg-load-more-tr")) return;
        var blob = (tr.getAttribute("data-search") || "").toLowerCase();
        var rowSt = tr.getAttribute("data-status") || "";
        var okQ = !q || blob.indexOf(q) >= 0;
        var okS = !st || rowSt === st;
        tr.classList.toggle("hidden", !(okQ && okS));
      });
      updateResultCount();
    }

    function refreshTable() {
      limits = { direct: ROW_PAGE, transitive: ROW_PAGE };
      $("tbody_direct").innerHTML = "";
      $("tbody_transitive").innerHTML = "";
      $("cnt_direct").textContent = "0";
      $("cnt_transitive").textContent = "0";
      if (!scanRows.length) {
        lastPartition = { direct: [], transitive: [] };
        updateSortHeaders();
        updateResultCount();
        return;
      }
      lastPartition = partitionRows(getSortedScanRows());
      $("cnt_direct").textContent = String(lastPartition.direct.length);
      $("cnt_transitive").textContent = String(lastPartition.transitive.length);
      renderSection("direct");
      var transPanel = $("panel_transitive");
      var transExpanded = transPanel && !transPanel.classList.contains("collapsed");
      if (renderedLazyTrans || transExpanded) {
        if (transExpanded) renderedLazyTrans = true;
        renderSection("transitive");
      }
      updateSortHeaders();
      applyRowFilter();
    }

    function renderTableRows(rows) {
      scanRows = rows || [];
      renderedLazyTrans = false;
      refreshTable();
    }

    function clearFilters() {
      $("filter_search").value = "";
      $("filter_status").value = "";
      saveUiState();
      refreshTable();
    }

    function debouncedRefreshTable() {
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(function () {
        saveUiState();
        refreshTable();
      }, 260);
    }

    function clearResults() {
      $("tbody_direct").innerHTML = "";
      $("tbody_transitive").innerHTML = "";
      $("cnt_direct").textContent = "0";
      $("cnt_transitive").textContent = "0";
      $("summary_bar").innerHTML = "";
      $("result_count").textContent = "";
      scanRows = [];
      renderedLazyTrans = false;
      lastPartition = { direct: [], transitive: [] };
      window.lastSummary = null;
      window.lastChartLayout = null;
      drawDistributionChart(null);
    }

    async function runScan() {
      setBanners("", "");
      $("pol_confirm").textContent = "";
      $("scan_status").textContent = "";
      $("btn_download").disabled = true;
      $("btn_download_csv").disabled = true;
      var start = performance.now();
      setLoading(true);
      try {
        var res = await fetch("/scan");
        var data = await res.json().catch(function () { return {}; });
        if (!res.ok) {
          var det = data.detail;
          var msg = typeof det === "string" ? det : JSON.stringify(det);
          throw new Error(msg || res.statusText);
        }
        var duration = ((performance.now() - start) / 1000).toFixed(1);
        var rows = data.rows || [];
        var n = rows.length;
        var pkgWord = n === 1 ? "package" : "packages";
        $("scan_status").textContent = "Scan completed in " + duration + "s • " + n + " " + pkgWord + " analyzed";
        $("empty_state").classList.add("hidden");
        $("results_panel").classList.remove("results-panel--hidden");
        var s = data.summary || {};
        renderSummaryBar(s);
        drawDistributionChart(s);
        renderTableRows(rows);
        var w = data.warnings || [];
        setBanners("", w.length ? w.join(String.fromCharCode(10)) : "");
        $("btn_download").disabled = false;
        $("btn_download_csv").disabled = false;
      } catch (e) {
        setBanners(String(e.message || e), "");
        clearResults();
        $("btn_download").disabled = true;
        $("btn_download_csv").disabled = true;
      } finally {
        setLoading(false);
      }
    }

    async function applyPolicy() {
      setBanners("", "");
      $("pol_confirm").textContent = "";
      var body = {
        approved: splitCsv($("pol_approved").value),
        restricted: splitCsv($("pol_restricted").value),
        denied: splitCsv($("pol_denied").value)
      };
      try {
        var res = await fetch("/policy", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        var data = await res.json().catch(function () { return {}; });
        if (!res.ok) {
          var det = data.detail;
          var msg = typeof det === "string" ? det : JSON.stringify(det);
          throw new Error(msg || res.statusText);
        }
        $("pol_confirm").textContent = data.message || "Policy updated successfully.";
      } catch (e) {
        setBanners(String(e.message || e), "");
      }
    }

    $("btn_theme").addEventListener("click", toggleTheme);
    $("btn_run").addEventListener("click", runScan);
    $("btn_apply_policy").addEventListener("click", applyPolicy);
    $("btn_clear_filters").addEventListener("click", clearFilters);
    $("btn_download").addEventListener("click", function () {
      if (!this.disabled) window.location.href = "/download";
    });
    $("btn_download_csv").addEventListener("click", function () {
      if (!this.disabled) window.location.href = "/download/csv";
    });
    $("filter_search").addEventListener("input", debouncedRefreshTable);
    $("filter_status").addEventListener("change", function () {
      saveUiState();
      applyRowFilter();
    });

    $("dep_tables").addEventListener("click", function (ev) {
      var lmb = ev.target.closest(".lg-load-more");
      if (lmb) {
        var sec = lmb.getAttribute("data-section");
        if (sec) {
          limits[sec] += ROW_PAGE;
          renderSection(sec);
          applyRowFilter();
        }
        return;
      }
      var th = ev.target.closest("[data-sort]");
      if (!th) return;
      var k = th.getAttribute("data-sort");
      if (sortKey === k) sortDir = sortDir === "asc" ? "desc" : "asc";
      else {
        sortKey = k;
        sortDir = "asc";
      }
      refreshTable();
    });

    bindDepToggle("toggle_direct", "panel_direct", null);
    bindDepToggle("toggle_transitive", "panel_transitive", "transitive");

    var chartEl = $("dist_chart");
    chartEl.addEventListener("click", onChartClick);
    chartEl.addEventListener("mousemove", onChartMouseMove);
    chartEl.addEventListener("mouseleave", function () { chartEl.style.cursor = "default"; });

    loadUiState();
    initTheme();
  </script>
</body>
</html>
"""
