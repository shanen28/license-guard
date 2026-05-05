"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from licenseguard.license_detection import clear_license_detection_cache
from licenseguard.pypi import clear_pypi_cache
from licenseguard.resolver import clear_distribution_map_cache


@pytest.fixture(autouse=True)
def _reset_caches() -> None:
    clear_distribution_map_cache()
    clear_license_detection_cache()
    clear_pypi_cache()
    yield
    clear_distribution_map_cache()
    clear_license_detection_cache()
    clear_pypi_cache()
