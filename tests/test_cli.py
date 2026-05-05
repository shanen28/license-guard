"""CLI exit codes and subprocess smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "licenseguard", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_cli_no_command_exits_2(project_root: Path) -> None:
    r = _run([], cwd=project_root)
    assert r.returncode == 2
    assert "command required" in (r.stderr or "").lower()


def test_cli_missing_requirements_exits_1(project_root: Path) -> None:
    r = _run(["scan", "___no_such_requirements___.txt", "--cli"], cwd=project_root)
    assert r.returncode == 1
    assert "not found" in (r.stderr or "").lower()


def test_cli_scan_json_valid(project_root: Path, tmp_path: Path) -> None:
    req = tmp_path / "r.txt"
    req.write_text("packaging\n", encoding="utf-8")
    r = _run(["scan", str(req), "--cli", "--json-only"], cwd=project_root)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert any(row["package"] == "packaging" for row in data["rows"])


def test_cli_scan_project_requirements(project_root: Path) -> None:
    req = project_root / "requirements.txt"
    if not req.is_file():
        pytest.skip("project requirements.txt not present")
    r = _run(["scan", str(req), "--cli", "--json-only"], cwd=project_root)
    assert r.returncode in (0, 1)
    data = json.loads(r.stdout)
    assert "summary" in data and "rows" in data
    assert data["summary"]["total"] == len(data["rows"])


def test_cli_unparseable_line_emits_warning(project_root: Path, tmp_path: Path) -> None:
    req = tmp_path / "r.txt"
    req.write_text("packaging\nhttp://example.com/foo\n", encoding="utf-8")
    r = _run(["scan", str(req), "--cli", "--json-only"], cwd=project_root)
    assert r.returncode == 0, r.stderr
    assert "could not parse" in (r.stderr or "").lower()
    json.loads(r.stdout)
