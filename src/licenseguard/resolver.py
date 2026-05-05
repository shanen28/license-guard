"""Resolve direct and transitive dependencies from the active environment."""

from __future__ import annotations

import functools
import re
from collections import deque
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


@dataclass(frozen=True)
class ResolvedPackage:
    name: str
    version: str
    direct: bool
    installed: bool


def _iter_requirement_file_lines(text: str) -> List[str]:
    kept: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--requirement ")):
            continue
        if line.startswith(("-c ", "--constraint ")):
            continue
        kept.append(line)
    return kept


def _strip_editable_prefix(line: str) -> str:
    for prefix in ("-e ", "--editable "):
        if line.startswith(prefix):
            rest = line[len(prefix) :].strip()
            return rest
    return line


def _name_from_egg_fragment(url: str) -> Optional[str]:
    m = re.search(r"[?&]egg=([^&]+)", url)
    if not m:
        return None
    return canonicalize_name(m.group(1).split("[")[0].strip())


def _name_from_pep508(fragment: str) -> Optional[str]:
    try:
        return canonicalize_name(Requirement(fragment).name)
    except Exception:
        return None


def _name_from_loose_token(fragment: str) -> Optional[str]:
    token = re.split(r"[\[<=!>~]", fragment, maxsplit=1)[0].strip()
    if not token or "/" in token:
        return None
    return canonicalize_name(token)


def package_name_from_requirement_line(line: str) -> Optional[str]:
    """Canonical package name from one requirements.txt line."""
    s = _strip_editable_prefix(line.strip())
    egg = _name_from_egg_fragment(s)
    if egg:
        return egg
    pep = _name_from_pep508(s)
    if pep:
        return pep
    return _name_from_loose_token(s)


def load_requirement_roots(path: Path) -> Tuple[List[str], List[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    warnings: List[str] = []
    roots: List[str] = []
    for line in _iter_requirement_file_lines(text):
        name = package_name_from_requirement_line(line)
        if name:
            roots.append(name)
        else:
            warnings.append(f"[Resolver] could not parse package name: {line!r}")
    return roots, warnings


def _line_looks_like_url(s: str) -> bool:
    return "://" in s or s.startswith(("git+", "hg+", "svn+", "bzr+"))


def _is_strictly_pinned_requirement_line(line: str) -> bool:
    """
    True only for a single ``==`` or ``===`` version (no wildcards, no extra specifiers).
    """
    s = _strip_editable_prefix(line.strip())
    if not s:
        return False
    if _line_looks_like_url(s):
        return False
    if _name_from_egg_fragment(s) and ("://" in s or "+" in s.split("egg=")[0]):
        return False
    try:
        req = Requirement(s)
    except Exception:
        return False
    if not str(req.specifier).strip():
        return False
    specs = list(req.specifier)
    if len(specs) != 1:
        return False
    sp = specs[0]
    if sp.operator not in ("==", "==="):
        return False
    ver = str(sp.version)
    if any(ch in ver for ch in "*?[],{}"):
        return False
    return True


def unpinned_direct_package_names(path: Path) -> Set[str]:
    """Canonical names of direct requirements that are not strictly ``==``/``===`` pinned."""
    text = path.read_text(encoding="utf-8", errors="replace")
    out: Set[str] = set()
    for line in _iter_requirement_file_lines(text):
        name = package_name_from_requirement_line(line)
        if not name:
            continue
        if not _is_strictly_pinned_requirement_line(line):
            out.add(name)
    return out


def _canonical_name_from_distribution(dist: metadata.Distribution) -> Optional[str]:
    raw = (dist.metadata.get("Name") or "").strip()
    if not raw:
        return None
    return canonicalize_name(raw)


def clear_distribution_map_cache() -> None:
    """Invalidate the distribution map cache (e.g. after environment changes)."""
    installed_distribution_map.cache_clear()


@functools.lru_cache(maxsize=1)
def installed_distribution_map() -> Dict[str, metadata.Distribution]:
    by_name: Dict[str, metadata.Distribution] = {}
    for dist in metadata.distributions():
        try:
            key = _canonical_name_from_distribution(dist)
            if key:
                by_name[key] = dist
        except Exception:
            continue
    return by_name


def dependency_name_from_requires_dist(req_str: str) -> Optional[str]:
    try:
        return canonicalize_name(Requirement(req_str).name)
    except Exception:
        return None


def _walk_installed_dependency_names(
    root_names: List[str],
    dist_map: Dict[str, metadata.Distribution],
) -> Set[str]:
    """BFS over the dependency graph, visiting only packages present in ``dist_map``."""
    seen: Set[str] = set()
    queue: deque[str] = deque(n for n in root_names if n in dist_map)

    while queue:
        name = queue.popleft()
        if name in seen:
            continue
        dist = dist_map.get(name)
        if dist is None:
            continue
        seen.add(name)

        for req_str in dist.requires or []:
            dep = dependency_name_from_requires_dist(req_str)
            if dep and dep in dist_map and dep not in seen:
                queue.append(dep)

    return seen


def resolved_packages_for_roots(root_names: List[str]) -> Tuple[List[ResolvedPackage], List[str]]:
    dist_map = installed_distribution_map()
    root_set = set(root_names)
    seen = _walk_installed_dependency_names(root_names, dist_map)

    packages: List[ResolvedPackage] = []
    for name in sorted(seen):
        dist = dist_map[name]
        packages.append(
            ResolvedPackage(
                name=name,
                version=dist.version or "unknown",
                direct=name in root_set,
                installed=True,
            )
        )
    return packages, []
