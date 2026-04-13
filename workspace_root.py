from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


AUTHORITATIVE_ROOT_ENV = "AISTUDIO_AUTHORITATIVE_ROOT"
KNOWN_DUPLICATE_ROOT_ENV = "AISTUDIO_NON_AUTHORITATIVE_DUPLICATE_ROOT"
DEFAULT_AUTHORITATIVE_ROOT = Path(r"C:\Users\rodne\OneDrive\Desktop\_AIStudio_POC").resolve()
DEFAULT_KNOWN_DUPLICATE_ROOT = Path(r"C:\Users\rodne\OneDrive\Documentos\_AIStudio_POC").resolve()
WORKSPACE_AUTHORITY_MARKER = ".workspace_authority.json"


class WorkspaceRootAuthorityError(RuntimeError):
    """Raised when a governed path resolves outside the authoritative workspace root."""


def _normalize_path(path: str | Path) -> Path:
    return Path(path).resolve()


def workspace_authority_marker_path(root: str | Path) -> Path:
    return _normalize_path(root) / WORKSPACE_AUTHORITY_MARKER


def write_workspace_authority_marker(
    root: str | Path,
    *,
    repo_name: str,
    canonical_root_hint: str | Path | None = None,
    authority_status: str = "authoritative",
) -> Path:
    normalized_root = _normalize_path(root)
    timestamp = datetime.now(timezone.utc).isoformat()
    marker_payload = {
        "repo_name": repo_name,
        "authority_status": authority_status,
        "canonical_root_hint": str(_normalize_path(canonical_root_hint or normalized_root)),
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    marker_path = workspace_authority_marker_path(normalized_root)
    marker_path.write_text(json.dumps(marker_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return marker_path


def _load_authoritative_workspace_marker(root: str | Path, *, label: str) -> dict[str, str]:
    normalized_root = _normalize_path(root)
    marker_path = workspace_authority_marker_path(normalized_root)
    if not marker_path.exists():
        raise WorkspaceRootAuthorityError(
            f"{label} is missing {WORKSPACE_AUTHORITY_MARKER}; authoritative workspace root marker required."
        )
    try:
        marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkspaceRootAuthorityError(
            f"{label} has an invalid {WORKSPACE_AUTHORITY_MARKER}; authoritative workspace root marker must be valid JSON."
        ) from exc
    if not isinstance(marker_payload, dict):
        raise WorkspaceRootAuthorityError(
            f"{label} has an invalid {WORKSPACE_AUTHORITY_MARKER}; marker payload must be a JSON object."
        )
    repo_name = marker_payload.get("repo_name")
    if not isinstance(repo_name, str) or not repo_name.strip():
        raise WorkspaceRootAuthorityError(
            f"{label} has an invalid {WORKSPACE_AUTHORITY_MARKER}; repo_name must be a non-empty string."
        )
    authority_status = marker_payload.get("authority_status")
    if authority_status != "authoritative":
        raise WorkspaceRootAuthorityError(
            f"{label} has an invalid {WORKSPACE_AUTHORITY_MARKER}; authority_status must equal 'authoritative'."
        )
    canonical_root_hint = marker_payload.get("canonical_root_hint")
    if not isinstance(canonical_root_hint, str) or not canonical_root_hint.strip():
        raise WorkspaceRootAuthorityError(
            f"{label} has an invalid {WORKSPACE_AUTHORITY_MARKER}; canonical_root_hint must be a non-empty string."
        )
    if _normalize_path(canonical_root_hint) != normalized_root:
        raise WorkspaceRootAuthorityError(
            f"{label} has an invalid {WORKSPACE_AUTHORITY_MARKER}; canonical_root_hint must resolve to the authoritative workspace root."
        )
    return {
        "repo_name": repo_name.strip(),
        "authority_status": authority_status,
        "canonical_root_hint": canonical_root_hint.strip(),
    }


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
    _load_authoritative_workspace_marker(normalized, label=label)
    return normalized


def ensure_authoritative_workspace_path(path: str | Path, *, label: str = "workspace path") -> Path:
    normalized = _normalize_path(path)
    classification = classify_workspace_path(normalized)
    if classification == "known_duplicate":
        raise WorkspaceRootAuthorityError(f"{label} resolves into the known non-authoritative duplicate workspace root.")
    if classification != "authoritative":
        raise WorkspaceRootAuthorityError(f"{label} is outside the authoritative workspace root.")
    _load_authoritative_workspace_marker(authoritative_workspace_root(), label="authoritative workspace root")
    return normalized
