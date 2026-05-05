"""HTTP API smoke tests (requires httpx for FastAPI TestClient)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from licenseguard.webapp import _state, configure_state, create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def reset_state() -> None:
    _state.clear()
    _state.update(
        {
            "requirements_path": None,
            "policy_path": None,
            "policy_config": None,
            "check_latest": False,
            "no_cache": False,
            "pypi_cache_file": None,
            "last_result": None,
        }
    )
    yield


def test_index_ok(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "LicenseGuard" in r.text


def test_scan_requires_requirements_path(client: TestClient) -> None:
    r = client.get("/scan")
    assert r.status_code == 400
    assert "requirements" in r.json()["detail"].lower()


def test_scan_empty_requirements(tmp_path: Path, client: TestClient) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("# empty\n", encoding="utf-8")
    configure_state(
        requirements_path=req,
        policy_path=None,
        policy_config=None,
        check_latest=False,
        no_cache=False,
        pypi_cache_file=None,
    )
    r = client.get("/scan")
    assert r.status_code == 200
    data = r.json()
    assert data["rows"] == []
    assert data["summary"]["total"] == 0


def test_download_json_404_without_scan(client: TestClient) -> None:
    assert client.get("/download").status_code == 404
    assert client.get("/download/csv").status_code == 404


def test_download_after_scan(tmp_path: Path, client: TestClient) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("packaging\n", encoding="utf-8")
    configure_state(
        requirements_path=req,
        policy_path=None,
        policy_config=None,
        check_latest=False,
        no_cache=False,
        pypi_cache_file=None,
    )
    assert client.get("/scan").status_code == 200
    jr = client.get("/download")
    assert jr.status_code == 200
    assert "rows" in jr.json()
    cr = client.get("/download/csv")
    assert cr.status_code == 200
    lines = cr.text.strip().splitlines()
    assert lines[0].startswith("package,")
    assert len(lines) >= 2


def test_policy_post_invalid(client: TestClient) -> None:
    r = client.post("/policy", json={"approved": "not-a-list"})
    assert r.status_code == 400


def test_policy_post_ok(client: TestClient) -> None:
    r = client.post(
        "/policy",
        json={"approved": ["MIT"], "restricted": [], "denied": []},
    )
    assert r.status_code == 200
    assert r.json().get("ok") is True
