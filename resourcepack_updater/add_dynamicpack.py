import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKS_DIR = ROOT / "packs"
REPO_DIR = ROOT / "dynamic_repo"
REPO_PACKS_DIR = REPO_DIR / "packs"

REPO_URL = "https://github.com/Arcdashckr/EzeliCraft/tree/main/resourcepack_updater/dynamic_repo"


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_dynamicmcpack_to_zip(zip_path: Path) -> None:
    temp_path = None
    try:
        with zipfile.ZipFile(zip_path, "r") as src:
            names = src.namelist()
            if "dynamicmcpack.json" in names:
                print(f"{zip_path.name}: dynamicmcpack.json already exists")
                return

            data = {
                "formatVersion": 1,
                "current": {
                    "version_number": "local"
                },
                "remote": {
                    "type": "dynamic_repo",
                    "url": REPO_URL,
                    "sign_no_required": True
                }
            }
            payload = json.dumps(data, indent=2).encode("utf-8")

            temp_fd, temp_name = tempfile.mkstemp(prefix="dynamicpack-", suffix=".zip", dir=str(zip_path.parent))
            os.close(temp_fd)
            temp_path = Path(temp_name)

            with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as dst:
                for info in src.infolist():
                    if info.filename == "dynamicmcpack.json":
                        continue
                    content = src.read(info.filename)
                    dst.writestr(info, content)
                dst.writestr("dynamicmcpack.json", payload)

        shutil.move(str(temp_path), str(zip_path))
        print(f"{zip_path.name}: updated")
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def write_repo_files(pack_names: list[Path]) -> None:
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    REPO_PACKS_DIR.mkdir(parents=True, exist_ok=True)

    contents = []
    for pack_path in pack_names:
        target_path = REPO_PACKS_DIR / pack_path.name
        shutil.copy2(pack_path, target_path)
        content_file_name = f"content_{pack_path.stem.lower()}.json"
        file_hash = sha1_file(target_path)
        content_data = {
            "formatVersion": 1,
            "content": {
                "parent": "",
                "remote_parent": "packs",
                "files": {
                    pack_path.name: {
                        "hash": file_hash
                    }
                }
            }
        }
        (REPO_DIR / content_file_name).write_text(json.dumps(content_data, indent=2) + "\n", encoding="utf-8")
        contents.append({
            "id": pack_path.stem.lower(),
            "url": content_file_name,
            "hash": file_hash,
            "required": True,
            "name": pack_path.stem
        })

    repo_data = {
        "formatVersion": 1,
        "build": 1,
        "name": "EzeliCraft DynamicPack Repo",
        "minimal_mod_build": 0,
        "contents": contents
    }
    (REPO_DIR / "dynamicmcpack.repo.json").write_text(json.dumps(repo_data, indent=2) + "\n", encoding="utf-8")
    (REPO_DIR / "dynamicmcpack.repo.build").write_text("1\n", encoding="utf-8")


def main() -> None:
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    pack_paths = sorted([p for p in PACKS_DIR.glob("*.zip") if p.is_file()])
    if not pack_paths:
        raise SystemExit("No .zip files found in resourcepack_updater/packs")

    for pack_path in pack_paths:
        add_dynamicmcpack_to_zip(pack_path)

    write_repo_files(pack_paths)
    print("DynamicPack setup completed")


if __name__ == "__main__":
    main()
