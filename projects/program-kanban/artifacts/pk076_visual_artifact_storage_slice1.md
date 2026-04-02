# PK-076 Visual Artifact Storage Slice 1

Date:
- `2026-04-02`

Status:
- `implemented`

## Scope

This first slice adds the canonical SQLite table and store helpers for visual artifacts.

## What Landed

- `visual_artifacts` table in `sessions/studio.db`
- path enforcement for `projects/<project>/artifacts/design/`
- file-hash and byte-count capture from on-disk artifacts
- store helpers to create, fetch, and list visual artifacts
- focused regression coverage in `tests/test_store.py`

## Why This Slice Comes First

The M11 API-first model says runtime generation should not outrun governance and canonical storage. Before image generation or import expands, the framework needs a place to record:
- prompt summary
- provider
- model
- lineage
- review state
- selected direction
- file metadata

## Follow-On

Next slices should:
- surface visual artifacts in operator evidence and review surfaces
- connect `PK-080` image-generation runtime to this table
- connect later import and gallery work to the same canonical record
