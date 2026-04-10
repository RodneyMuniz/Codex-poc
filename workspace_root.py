from __future__ import annotations

import os
from pathlib import Path


AUTHORITATIVE_ROOT_ENV = "AISTUDIO_AUTHORITATIVE_ROOT"
KNOWN_DUPLICATE_ROOT_ENV = "AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT"
DEFAULT_AUTHORITATIVE_ROOT = Path(r"C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC").resolve()
DEFAULT_KNOWN_DUPLICATE_ROOT = Path(r"C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC").resolve()


class WorkspaceRootAuthorityError(RuntimeError):
    """Raised when a governed path resolves outside the authoritative workspace root."""


def _normalize_path(path: str | Path) -> Path:
    return Path(path).resolve()


def authoritative_workspace_root() -> Path:
    configured = os.getenv(AUTHORITATIVE_ROOT_ENV)
    if configured and configured.strip():
        return _normalize_path(configured)
    return DEFAULT_AUTHORITATIVE_ROOT


def known_duplicate_workspace_root() -> Path:
    configured = os.getenv(KNOWN_DUPLICATE_ROOT_ENV)
    if configured and configured.strip():
        return _normalize_path(configured)
    return DEFAULT_KNOWN_DUPLICATE_ROOT


def _is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def classify_workspace_path(path: str | Path) -> str:
    candidate = _normalize_path(path)
    duplicate_root = known_duplicate_workspace_root()
    authoritative_root = authoritative_workspace_root()
    if candidate == duplicate_root or _is_within(duplicate_root, candidate):
        return "known_duplicate"
    if candidate == authoritative_root or _is_within(authoritative_root, candidate):
        return "authoritative"
    return "out_of_root"


def ensure_authoritative_workspace_root(path: str | Path, *, label: str = "workspace root") -> Path:
    normalized = _normalize_path(path)
    classification = classify_workspace_path(normalized)
    if classification == "known_duplicate":
        raise WorkspaceRootAuthorityError(f"{label} resolves into the known non-authoritative duplicate workspace root.")
    authoritative_root = authoritative_workspace_root()
    if classification != "authoritative" or normalized != authoritative_root:
        raise WorkspaceRootAuthorityError(f"{label} must equal the authoritative workspace root.")
    return normalized


def ensure_authoritative_workspace_path(path: str | Path, *, label: str = "workspace path") -> Path:
    normalized = _normalize_path(path)
    classification = classify_workspace_path(normalized)
    if classification == "known_duplicate":
        raise WorkspaceRootAuthorityError(f"{label} resolves into the known non-authoritative duplicate workspace root.")
    if classification != "authoritative":
        raise WorkspaceRootAuthorityError(f"{label} is outside the authoritative workspace root.")
    return normalized
