"""LicenseGuard: scan installed dependencies for license policy compliance."""

from licenseguard.policy import PolicyConfig, load_policy_file
from licenseguard.scan import scan_requirements_file

__all__ = ["PolicyConfig", "load_policy_file", "scan_requirements_file"]
# NOTE: Keep this version in sync with pyproject.toml [project].version
__version__ = "0.3.0"
