"""Command-line interface for LicenseGuard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from licenseguard import __version__
from licenseguard.policy import LicenseStatus, load_policy_file, should_fail_scan
from licenseguard.scan import scan_requirements_file


def _render_table(rows: List[Dict[str, Any]], *, check_latest: bool) -> str:
    headers = [
        "package",
        "version",
        "D/T",
        "license (raw)",
        "SPDX (norm)",
        "status",
    ]
    if check_latest:
        headers.extend(["latest_version", "license_change"])

    cells: List[List[str]] = []
    for r in rows:
        row_cells = [
            r["package"],
            r["version"],
            "D" if r["direct"] else "T",
            (r["license_detected"] or "-")[:32],
            (r["license_spdx"] or "-")[:28],
            r["status"],
        ]
        if check_latest:
            lv = r.get("version_latest")
            row_cells.append("-" if lv is None else str(lv)[:16])
            if r.get("license_latest") is None:
                row_cells.append("-")
            else:
                row_cells.append("Y" if r.get("license_changed") else "N")
        cells.append(row_cells)
    widths = [len(h) for h in headers]
    for row in cells:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    def line(values: List[str]) -> str:
        return "  ".join(values[i].ljust(widths[i]) for i in range(len(values)))

    out = [line(headers), line(["-" * w for w in widths])]
    out.extend(line(row) for row in cells)
    return "\n".join(out)


def _format_cli_summary(summary: Dict[str, Any]) -> str:
    w = 10
    lines = [
        "Scan Summary:",
        f"  ✔ Approved:    {summary['approved']:>{w}}",
        f"  ⚠ Restricted:  {summary['restricted']:>{w}}",
        f"  ✖ Denied:      {summary['denied']:>{w}}",
        f"  ? Unknown:     {summary['unknown']:>{w}}",
    ]
    return "\n".join(lines)


def _render_json(result: Dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True)


def _print_scan(
    result: Dict[str, Any],
    payload: str,
    *,
    json_only: bool,
    no_table: bool,
) -> None:
    check_latest = bool(result.get("check_latest"))
    if json_only:
        warnings = result.get("warnings") or []
        if warnings:
            for w in warnings:
                print(f"warning: {w}", file=sys.stderr)
            print(file=sys.stderr)
        print(payload)
        return
    if not no_table:
        print(_render_table(result["rows"], check_latest=check_latest))
        print()
        print(_format_cli_summary(result["summary"]))
        print()
    warnings = result.get("warnings") or []
    if warnings:
        for w in warnings:
            print(f"warning: {w}", file=sys.stderr)
        print(file=sys.stderr)
    print(payload)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="licenseguard",
        description="Scan installed packages (from requirements.txt) for license policy compliance.",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Print version and exit",
    )
    sub = p.add_subparsers(dest="command", required=False)

    scan = sub.add_parser("scan", help="Scan requirements file against the current environment")
    scan.add_argument("requirements_file", type=Path, help="Path to requirements.txt")
    scan.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="YAML or JSON policy file (approved / restricted / denied lists)",
    )
    scan.add_argument(
        "--fail-on",
        choices=("denied", "restricted", "unknown"),
        default=None,
        help="Exit non-zero when worst status is at or above this level (default: denied or restricted)",
    )
    scan.add_argument("--json-only", action="store_true", help="Print only JSON to stdout")
    scan.add_argument(
        "--no-table",
        action="store_true",
        help="Skip the text table; JSON is still printed",
    )
    scan.add_argument(
        "-o",
        "--output-json",
        type=Path,
        default=None,
        help="Also write full JSON report to this path",
    )
    scan.add_argument(
        "--check-latest",
        action="store_true",
        help="Compare each package with the latest release on PyPI (network required)",
    )
    scan.add_argument(
        "--cache-file",
        type=Path,
        default=None,
        help="With --check-latest: load/save PyPI license snapshots as JSON (merged after scan)",
    )
    scan.add_argument(
        "--no-cache",
        action="store_true",
        help="With --check-latest: skip memory and disk PyPI cache (always fetch fresh)",
    )
    scan.add_argument(
        "--cli",
        action="store_true",
        help="Print scan results in the terminal instead of opening the web UI",
    )
    return p


def main(argv: Optional[list] = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command is None:
        print("error: command required (e.g. licenseguard scan requirements.txt)", file=sys.stderr)
        return 2
    if args.command != "scan":
        return 2

    req = args.requirements_file
    if not req.is_file():
        print(f"error: file not found: {req}", file=sys.stderr)
        return 1

    policy = None
    if args.policy is not None:
        if not args.policy.is_file():
            print(f"error: policy file not found: {args.policy}", file=sys.stderr)
            return 1
        try:
            policy = load_policy_file(args.policy)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"error: invalid policy file: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"error: could not load policy: {e}", file=sys.stderr)
            return 1

    if not args.cli:
        if args.json_only or args.no_table or args.output_json or args.fail_on is not None:
            print(
                "warning: --json-only, --no-table, -o/--output-json, and --fail-on "
                "only apply with --cli; starting web UI.",
                file=sys.stderr,
            )
        try:
            from licenseguard.webapp import run_web_ui
        except ImportError as e:
            print(
                "error: web UI requires fastapi and uvicorn. "
                "Install with: pip install fastapi uvicorn",
                file=sys.stderr,
            )
            print(f"detail: {e}", file=sys.stderr)
            return 1
        try:
            return run_web_ui(
                requirements_path=req,
                policy_path=args.policy,
                policy_config=policy,
                check_latest=bool(args.check_latest),
                no_cache=bool(args.no_cache),
                pypi_cache_file=args.cache_file if args.check_latest else None,
            )
        except KeyboardInterrupt:
            return 0

    result = scan_requirements_file(
        req,
        policy=policy,
        check_latest=args.check_latest,
        pypi_cache_file=args.cache_file if args.check_latest else None,
        pypi_no_cache=bool(args.no_cache),
    )
    payload = _render_json(result)
    _print_scan(result, payload, json_only=args.json_only, no_table=args.no_table)

    if args.output_json:
        args.output_json.write_text(payload + "\n", encoding="utf-8")

    worst = LicenseStatus(result["summary"]["worst_status"])
    if should_fail_scan(worst, args.fail_on):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
