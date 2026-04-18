"""Compatibility shim for anchorpy's legacy pytest_xprocess import.

The currently installed xprocess package exposes the runtime module as `xprocess`,
while older callers still import `pytest_xprocess.getrootdir`.
"""
from __future__ import annotations

from pathlib import Path


def getrootdir(config) -> Path:
    """Return pytest rootdir/rootpath in a version-tolerant way."""
    root = getattr(config, "rootpath", None)
    if root is not None:
        return Path(root)

    legacy_root = getattr(config, "rootdir", None)
    if legacy_root is not None:
        return Path(str(legacy_root))

    return Path(".").resolve()
