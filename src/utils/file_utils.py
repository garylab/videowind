from pathlib import Path
import json


async def write_json(path: Path, content: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2))