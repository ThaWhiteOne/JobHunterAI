from pathlib import Path


def read_text_file(path: Path, required: bool = True) -> str:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Missing required file: {path}")
        return ""
    if not path.is_file():
        raise FileNotFoundError(f"Expected a file but found something else: {path}")
    return path.read_text(encoding="utf-8").strip()


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
