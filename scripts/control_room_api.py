from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sessions import SessionStore
from workspace_root import ensure_authoritative_workspace_root


def _store() -> SessionStore:
    ensure_authoritative_workspace_root(ROOT, label="control_room_api root")
    return SessionStore(ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Program Kanban control-room service wrapper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    restore = subparsers.add_parser("restore-backup")
    restore.add_argument("--backup-id", required=True)
    restore.add_argument("--requested-by", default="Control Room")

    try:
        args = parser.parse_args()
        store = _store()
        if args.command == "restore-backup":
            payload = store.restore_dispatch_backup(backup_id=args.backup_id, requested_by=args.requested_by)
        else:
            payload = {"error": "Unknown command."}
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "error_type": exc.__class__.__name__,
                },
                ensure_ascii=True,
            )
        )
        raise SystemExit(1) from exc

    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
