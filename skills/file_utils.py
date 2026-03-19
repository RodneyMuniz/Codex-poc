from pathlib import Path


def ensure_file(path: str, default_content: str = "") -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        file_path.write_text(default_content, encoding="utf-8")


def read_text(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


def write_text(path: str, content: str) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def append_under_heading(path: str, heading: str, block: str) -> bool:
    file_path = Path(path)

    if not file_path.exists():
        return False

    content = file_path.read_text(encoding="utf-8")

    if heading not in content:
        return False

    replacement = f"{heading}\n\n{block}\n"
    updated = content.replace(heading, replacement, 1)

    file_path.write_text(updated, encoding="utf-8")
    return True