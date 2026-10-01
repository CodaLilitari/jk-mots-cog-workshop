"""Delegate installed-skill updates to the registered Workshop launcher, never duplicate it."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]


def read_object(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Installation metadata must be a JSON object.")
    return value


def absolute_path(value, name):
    if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
        raise ValueError(f"Installation metadata has no absolute {name} path.")
    return Path(value)


def registered_launcher(skill_root):
    marker = read_object(skill_root / ".workshop-install.json")
    if marker.get("schema_version") != 1:
        raise ValueError("Unsupported skill installation metadata.")
    home = absolute_path(marker.get("home"), "managed home")
    receipt = read_object(home / "skill-install.json")
    target = absolute_path(receipt.get("target"), "skill target")
    if target.resolve() != skill_root.resolve():
        raise ValueError("This skill copy is not the registered installation.")
    launcher = absolute_path(receipt.get("launcher"), "launcher")
    if launcher.name != "cog_workshop.py" or not launcher.is_file():
        raise ValueError("The registered Workshop launcher has moved or is missing.")
    release = read_object(launcher.parent / "release.json")
    if release.get("product") != "jk-mots-cog-workshop" or release.get("schema_version") != 1:
        raise ValueError("The registered launcher is not a supported Workshop release.")
    return launcher, home


def main(argv=None):
    try:
        launcher, home = registered_launcher(SKILL_ROOT)
        args = list(sys.argv[1:] if argv is None else argv) or ["version"]
        # The existing launcher alone owns network, interval, integrity, dispatch and reporting rules.
        return subprocess.call([sys.executable, "-B", str(launcher), "--home", str(home), *args])
    except (OSError, ValueError) as exc:
        print(f"Workshop skill launcher unavailable: {exc}\n"
              "Offline corpus/inspection helpers still work. Restore the extracted release folder, "
              "or run its cog_workshop.py --offline install-skill --destination <this-skill-folder> "
              "using the same --home. Locally modified skills are preserved.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
