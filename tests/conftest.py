from __future__ import annotations

import pytest

from workspace_root import AUTHORITATIVE_ROOT_ENV, KNOWN_DUPLICATE_ROOT_ENV, write_workspace_authority_marker


@pytest.fixture(autouse=True)
def _tmp_path_workspace_authority(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if "tmp_path" not in request.fixturenames:
        return
    tmp_path = request.getfixturevalue("tmp_path")
    monkeypatch.setenv(AUTHORITATIVE_ROOT_ENV, str(tmp_path))
    monkeypatch.setenv(KNOWN_DUPLICATE_ROOT_ENV, str(tmp_path.parent / f"{tmp_path.name}_duplicate"))
    write_workspace_authority_marker(tmp_path, repo_name="test-workspace")
