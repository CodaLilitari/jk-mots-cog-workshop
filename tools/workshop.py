"""Managed portable updates and public-corpus commands. Python 3.10+."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request
import zipfile

PRODUCT = "jk-mots-cog-workshop"
DEFAULT_FEED = "https://richard-pemberton-research.darkahn.chatgpt.site/updates/jk-mots-cog-workshop/releases.json"
ROOT = Path(__file__).resolve().parents[1]
MAX_FEED = 1024 * 1024
MAX_DOWNLOAD = 512 * 1024 * 1024
MAX_EXTRACTED = 256 * 1024 * 1024
MAX_FILES = 2048
MIRROR_HOSTS = frozenset({"github.com", "gitlab.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"})
VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class WorkshopError(Exception):
    """An actionable validation or update error."""


def outside_checkout(path):
    """Reject lexical and resolved Git ancestors without launching Git."""
    path = Path(path).expanduser().absolute()
    for candidate in (path, path.resolve()):
        for ancestor in (candidate, *candidate.parents):
            if (ancestor / '.git').exists():
                raise WorkshopError('Managed update storage must be outside Git checkouts; choose a separate --home.')
    return path.resolve()


def is_link(path):
    return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)


def version_key(value):
    if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
        raise WorkshopError("Versions must be three nonnegative integers, e.g. 0.1.0 (no prerelease suffix).")
    return tuple(int(x) for x in value.split("."))


def read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")
        return value
    except (OSError, ValueError) as exc:
        raise WorkshopError(f"Cannot read JSON {path}: {exc}") from exc


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def data_home():
    custom = os.environ.get("COG_WORKSHOP_HOME")
    if custom:
        return Path(custom).expanduser().absolute()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "COGWorkshop"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / PRODUCT


def release_version(root):
    info = read_json(Path(root) / "release.json")
    if info.get("schema_version") != 1 or info.get("product") != PRODUCT:
        raise WorkshopError("This directory is not a supported COG Workshop release.")
    version_key(info.get("version"))
    return info["version"]


def origin(url):
    try:
        p = urllib.parse.urlsplit(url)
        if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment or p.port not in (None, 443):
            raise ValueError("HTTPS without credentials, fragments or custom ports is required")
        return "https://" + p.hostname.lower()
    except (ValueError, TypeError) as exc:
        raise WorkshopError(f"Unsafe URL: {exc}") from exc


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed):
        self.allowed = allowed
        self.max_redirections = 5
        self.max_repeats = 2

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if origin(newurl) not in self.allowed:
            raise WorkshopError("Download redirect leaves the approved HTTPS origins.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def stream_url(url, allowed, destination, limit, timeout=10, deadline=60):
    if origin(url) not in allowed:
        raise WorkshopError("URL is outside the approved HTTPS origins.")
    opener = urllib.request.build_opener(SafeRedirect(allowed))
    req = urllib.request.Request(url, headers={"User-Agent": "COG-Workshop-Updater/1", "Accept-Encoding": "identity"})
    started = time.monotonic()
    with opener.open(req, timeout=timeout) as response:
        if origin(response.url) not in allowed:
            raise WorkshopError("Response is outside the approved HTTPS origins.")
        length = response.headers.get("Content-Length")
        if length and int(length) > limit:
            raise WorkshopError("Response exceeds its download limit.")
        count = 0
        while True:
            if time.monotonic() - started > deadline:
                raise WorkshopError("Download exceeded its time budget; try explicit update later.")
            chunk = response.read1(min(65536, limit - count + 1))
            if not chunk:
                break
            count += len(chunk)
            if count > limit:
                raise WorkshopError("Response exceeds its download limit.")
            destination.write(chunk)
        return count


def read_feed(url):
    import io
    output = io.BytesIO()
    stream_url(url, {origin(url)}, output, MAX_FEED, timeout=5, deadline=10)
    try:
        feed = json.loads(output.getvalue())
    except (ValueError, UnicodeError) as exc:
        raise WorkshopError("Feed is not valid JSON.") from exc
    return validate_feed(feed, url)


def validate_feed(feed, url):
    if not isinstance(feed, dict) or feed.get("schema_version") != 1 or feed.get("product") != PRODUCT:
        raise WorkshopError("Unsupported release feed.")
    latest = feed.get("latest")
    if not isinstance(latest, dict):
        raise WorkshopError("Release feed has no latest release.")
    version_key(latest.get("version"))
    if type(latest.get("size")) is not int or not 0 < latest["size"] <= MAX_DOWNLOAD:
        raise WorkshopError("Release size is missing or outside the supported bound.")
    if not isinstance(latest.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", latest["sha256"]):
        raise WorkshopError("Release SHA-256 is invalid.")
    if origin(latest.get("url")) != origin(url):
        raise WorkshopError("Primary package must be served from the portfolio feed origin.")
    mirrors = latest.get("mirrors", [])
    if not isinstance(mirrors, list) or len(mirrors) > 5:
        raise WorkshopError("Invalid release mirror list.")
    allowed = {"https://" + host for host in MIRROR_HOSTS}
    for mirror in mirrors:
        if origin(mirror) not in allowed:
            raise WorkshopError("Only the documented GitHub/GitLab mirror origins are permitted.")
    return latest


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_members(archive):
    files, all_paths, spellings, total = [], {}, {}, 0
    infos = archive.infolist()
    if len(infos) > MAX_FILES:
        raise WorkshopError("Archive has too many entries.")
    for item in infos:
        name = item.filename
        pieces = name.rstrip("/").split("/")
        if len(pieces) > 16:
            raise WorkshopError('Archive member path is too deeply nested.')
        if name != item.orig_filename or not name or "\\" in name or name.startswith("/") or any(not p or p in (".", "..") or p.endswith((".", " ")) or any(ord(c) < 32 or c in ':<>"|?*' for c in p) or p.split(".", 1)[0].upper() in RESERVED for p in pieces):
            raise WorkshopError("Unsafe archive member path.")
        if item.flag_bits & 1:
            raise WorkshopError("Encrypted archive entries are not supported.")
        mode = (item.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
            raise WorkshopError("Archive symlinks and special files are forbidden.")
        key = unicodedata.normalize("NFC", "/".join(pieces)).casefold()
        for i in range(1, len(pieces) + 1):
            spelling = "/".join(pieces[:i])
            canonical = unicodedata.normalize("NFC", spelling).casefold()
            if canonical in spellings and spellings[canonical] != spelling:
                raise WorkshopError("Archive has case/Unicode-colliding directory paths.")
            spellings[canonical] = spelling
            if len(spellings) > MAX_FILES:
                raise WorkshopError('Archive has too many files and implicit directories.')
        if key in all_paths:
            raise WorkshopError("Archive has duplicate or case/Unicode-colliding paths.")
        all_paths[key] = item.is_dir()
        total += item.file_size
        if total > MAX_EXTRACTED or item.file_size > MAX_EXTRACTED or (item.file_size > 1024 * 1024 and item.file_size > max(1, item.compress_size) * 1000):
            raise WorkshopError("Archive expansion exceeds bounds.")
        if not item.is_dir():
            files.append(item)
    for key in all_paths:
        parts = key.split("/")
        if any(all_paths.get("/".join(parts[:i])) is False for i in range(1, len(parts))):
            raise WorkshopError("Archive contains a file/directory collision.")
    return files


def extract_release(package, destination, expected_version):
    with zipfile.ZipFile(package) as archive:
        members = safe_members(archive)
        for item in members:
            target = Path(destination).joinpath(*PurePosixPath(item.filename).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item) as source, target.open("xb") as out:
                shutil.copyfileobj(source, out, 65536)
    if release_version(destination) != expected_version:
        raise WorkshopError("Package version differs from the feed.")
    for required in ("cog_workshop.py", "tools/workshop.py", "skill/jk-mots-cog-workflow/SKILL.md"):
        if not (Path(destination) / required).is_file():
            raise WorkshopError(f"Release is missing {required}.")


@contextlib.contextmanager
def update_lock(home):
    home = outside_checkout(home)
    home.mkdir(parents=True, exist_ok=True)
    stream = (home / "update.lock").open("a+b")
    try:
        stream.seek(0)
        stream.write(b"0")
        stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise WorkshopError("Another workshop update is already running.") from exc
        yield
    finally:
        stream.close()


def active_release(home, recover=True):
    for name in (("active.json", "active.previous.json") if recover else ("active.json",)):
        pointer = home / name
        if not pointer.exists():
            continue
        try:
            value = read_json(pointer)
            version = value["version"]
            version_key(version)
            target = home / "versions" / version
            if target.is_symlink() or release_version(target) != version or not (target / ".verified-install.json").is_file():
                raise WorkshopError("Invalid managed release.")
            receipt = read_json(target / ".verified-install.json")
            if receipt.get("files") != tree_hashes(target, exclude_receipt=True):
                raise WorkshopError("Managed release files changed; preserve them and recover the previous release.")
            return target
        except (WorkshopError, KeyError, TypeError):
            continue
    return None


def current_version(home, source_root=ROOT):
    version = release_version(source_root)
    active = active_release(home)
    if active and version_key(release_version(active)) > version_key(version):
        version = release_version(active)
    return version


def activate_package(package, latest, home, source_root=ROOT):
    home = outside_checkout(home)
    if version_key(latest["version"]) <= version_key(current_version(home, source_root)):
        raise WorkshopError("Refusing a downgrade or reinstall of the current release.")
    package = Path(package)
    if package.stat().st_size != latest["size"] or sha256_file(package) != latest["sha256"]:
        raise WorkshopError("Package size or SHA-256 does not match the feed.")
    versions = home / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    final = versions / latest["version"]
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=versions))
    try:
        extract_release(package, staging, latest["version"])
        files = tree_hashes(staging)
        atomic_json(staging / ".verified-install.json", {"version": latest["version"], "sha256": latest["sha256"], "size": latest["size"], "installed_at": int(time.time()), "files": files})
        if final.exists():
            receipt = read_json(final / ".verified-install.json")
            if receipt.get("sha256") != latest["sha256"] or release_version(final) != latest["version"] or tree_hashes(final, exclude_receipt=True) != files:
                raise WorkshopError("A different directory already occupies this version; it was preserved.")
        else:
            os.replace(staging, final)
        old = active_release(home)
        if old:
            atomic_json(home / "active.previous.json", {"version": release_version(old)})
        atomic_json(home / "active.json", {"version": latest["version"]})
        return final
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def update(home, feed_url=DEFAULT_FEED, check_only=False, source_root=ROOT):
    with update_lock(home):
        # Record attempts as well as successes so offline commands do not hammer the feed.
        atomic_json(home / "check-state.json", {"checked_at": int(time.time()), "feed": feed_url})
        latest = read_feed(feed_url)
        current = current_version(home, source_root)
        if version_key(latest["version"]) <= version_key(current):
            return {"status": "current", "current": current, "offered": latest["version"]}
        if check_only:
            return {"status": "available", "current": current, "offered": latest["version"]}
        allowed = {origin(feed_url), *("https://" + host for host in MIRROR_HOSTS)}
        failures = []
        with tempfile.TemporaryDirectory(prefix="download-", dir=home) as temp:
            package = Path(temp) / "release.zip"
            for url in [latest["url"], *latest.get("mirrors", [])]:
                try:
                    with package.open("wb") as out:
                        stream_url(url, allowed, out, latest["size"], deadline=120)
                    if package.stat().st_size != latest["size"] or sha256_file(package) != latest["sha256"]:
                        raise WorkshopError("Downloaded package failed size/SHA-256 verification.")
                    target = activate_package(package, latest, home, source_root)
                    skill = sync_installed_skill(home, target)
                    return {"status": "updated", "previous": current, "current": latest["version"], "path": str(target), "skill": skill}
                except (WorkshopError, OSError, ValueError, zipfile.BadZipFile) as exc:
                    failures.append(str(exc))
        raise WorkshopError("Update failed; existing installation was retained. " + "; ".join(failures))


def tree_hashes(folder, exclude_receipt=False):
    folder = Path(folder)
    if is_link(folder):
        raise WorkshopError("A managed skill cannot be a symlink.")
    result = {}
    entries, total, pending = 0, 0, [folder]
    while pending:
        with os.scandir(pending.pop()) as children:
            for child in children:
                path = Path(child.path)
                if child.name == '__pycache__' or path.suffix == '.pyc' or (exclude_receipt and child.name == '.verified-install.json'):
                    continue
                entries += 1
                if entries > MAX_FILES:
                    raise WorkshopError('Managed tree has too many entries; keep private corpora outside the installation.')
                if is_link(path):
                    raise WorkshopError('A managed tree cannot contain symlinks or junctions.')
                if child.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif child.is_file(follow_symlinks=False):
                    total += child.stat(follow_symlinks=False).st_size
                    if total > MAX_EXTRACTED:
                        raise WorkshopError('Managed tree exceeds its byte budget.')
                    result[path.relative_to(folder).as_posix()] = sha256_file(path)
    return result


def install_skill(home, release_root, target=None):
    home = outside_checkout(home)
    release_root = Path(release_root).expanduser().resolve()
    source = Path(release_root) / "skill/jk-mots-cog-workflow"
    if not (source / "SKILL.md").is_file():
        raise WorkshopError("This release has no public skill.")
    registration = home / "skill-install.json"
    old = read_json(registration) if registration.exists() else None
    target = Path(target or (Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills/jk-mots-cog-workflow-public")).expanduser().absolute()
    if target.exists() or target.is_symlink():
        if not old or old.get("target") != str(target) or tree_hashes(target) != old.get("files"):
            raise WorkshopError("Skill destination is unrelated or has local changes; it was preserved. Choose a new/nonexistent --destination.")
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".cog-skill-", dir=target.parent))
    backup = None
    try:
        # Only this release's skill is copied; research roots and user files are never followed.
        tree_hashes(source)
        shutil.copytree(source, stage, dirs_exist_ok=True)
        # Generated only in the installed copy; no private machine paths ship in releases.
        atomic_json(stage / ".workshop-install.json", {"schema_version": 1, "home": str(home)})
        hashes = tree_hashes(stage)
        if target.exists():
            backup_root = target.parent / ".cog-workshop-backups"
            if backup_root.is_symlink():
                raise WorkshopError("Skill backup directory cannot be a symlink.")
            backup_root.mkdir(exist_ok=True)
            backup = backup_root / (target.name + ".backup-" + str(time.time_ns()))
            os.replace(target, backup)
        try:
            os.replace(stage, target)
        except BaseException:
            if backup and not target.exists():
                os.replace(backup, target)
            raise
        atomic_json(registration, {"target": str(target), "launcher": str(release_root / "cog_workshop.py"), "version": release_version(release_root), "files": hashes, "backup": str(backup) if backup else None})
        return {"status": "installed", "target": str(target), "version": release_version(release_root), "backup": str(backup) if backup else None}
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def sync_installed_skill(home, release_root):
    registration = home / "skill-install.json"
    if not registration.exists():
        return {"status": "not-opted-in"}
    try:
        old = read_json(registration)
        target = old.get("target")
        if not isinstance(target, str) or not target.strip() or not Path(target).is_absolute():
            raise WorkshopError("Installed skill registration has an invalid target; no skill destination was selected.")
        return install_skill(home, release_root, target)
    except (WorkshopError, OSError, KeyError) as exc:
        return {"status": "preserved", "reason": str(exc)}


def auto_due(home, interval):
    try:
        stamp = read_json(home / "check-state.json")["checked_at"]
        now = time.time()
        return stamp > now or now - stamp >= interval
    except (WorkshopError, KeyError, TypeError):
        return True


def public_files(root):
    for base in ("corpus", "docs", "skill/jk-mots-cog-workflow/references"):
        folder = Path(root) / base
        if folder.is_dir():
            for path in sorted(folder.rglob("*")):
                if path.is_file() and not path.is_symlink() and path.suffix.lower() in (".md", ".jsonl", ".json", ".txt"):
                    yield path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Public JK/MotS COG Workshop. Managed updates never replace your checkout or private corpus.")
    parser.add_argument("--offline", action="store_true", help="Make no network requests.")
    parser.add_argument("--no-auto-update", action="store_true", help="Skip the automatic update check for this invocation.")
    parser.add_argument("--home", type=Path, default=data_home(), help="Separate managed installation and update-state directory.")
    parser.add_argument("--feed", default=DEFAULT_FEED, help="Explicit trusted HTTPS feed override (changes your update trust source).")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version")
    sub.add_parser("update", help="Check, verify, and activate a newer release.")
    sub.add_parser("check-update", help="Check without installing.")
    sub.add_parser("stats")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("path", type=Path)
    inspect.add_argument("--target", choices=("jk", "mots"), required=True)
    capacity = sub.add_parser("capacity", help="Read-only static.jkl / items.dat instance accounting. Never updates or writes files.")
    capacity.add_argument("static_jkl", type=Path)
    capacity.add_argument("items_dat", type=Path)
    capacity.add_argument("--reserve", type=int, default=0)
    skill = sub.add_parser("install-skill", help="Opt in to installing and maintaining the public skill; unrelated content is preserved.")
    skill.add_argument("--destination", type=Path)
    from tools import reporting
    reporter = sub.add_parser("report", help="Optional local research-finding drafts. Never sends or checks for updates.")
    reporting.add_commands(reporter)
    args = parser.parse_args(argv)
    home = args.home.expanduser().absolute()
    offline = args.offline or os.environ.get("COG_WORKSHOP_OFFLINE", "").lower() in ("1", "true", "yes")
    no_auto = args.no_auto_update or os.environ.get("COG_WORKSHOP_AUTO_UPDATE", "").lower() in ("0", "false", "off", "no")
    try:
        if args.command == "report":
            return reporting.run(args)
        if args.command == "capacity":
            return subprocess.call([sys.executable, "-B", str(ROOT / "skill/jk-mots-cog-workflow/scripts/audit_static_capacity.py"), str(args.static_jkl.resolve()), str(args.items_dat.resolve()), "--reserve", str(args.reserve)])
        home = outside_checkout(home)
        if args.command in ("update", "check-update"):
            if offline:
                raise WorkshopError("Offline mode forbids an update check.")
            print(json.dumps(update(home, args.feed, args.command == "check-update", source_root=ROOT), indent=2))
            return 0
        interval = max(3600, int(os.environ.get("COG_WORKSHOP_UPDATE_INTERVAL", "86400")))
        if not offline and not no_auto and auto_due(home, interval):
            try:
                outcome = update(home, args.feed, source_root=ROOT)
                if outcome["status"] == "updated":
                    print(f"Workshop updated to {outcome['current']}.", file=sys.stderr)
                    if outcome["skill"].get("status") == "preserved":
                        print("Installed skill was preserved: " + outcome["skill"].get("reason", "review install-skill state"), file=sys.stderr)
            except (WorkshopError, OSError, ValueError, zipfile.BadZipFile) as exc:
                print(f"Update check skipped: {exc}", file=sys.stderr)
        active = active_release(home)
        if active and active.resolve() != ROOT.resolve() and version_key(release_version(active)) > version_key(release_version(ROOT)):
            command_args = list(argv) if argv is not None else sys.argv[1:]
            return subprocess.call([sys.executable, str(active / "cog_workshop.py"), "--no-auto-update", *command_args])
        if args.command == "version":
            print(release_version(ROOT))
        elif args.command == "install-skill":
            print(json.dumps(install_skill(home, ROOT, args.destination), indent=2))
        elif args.command == "inspect":
            return subprocess.call([sys.executable, "-B", str(ROOT / "skill/jk-mots-cog-workflow/scripts/inspect_cog.py"), str(args.path.resolve()), "--target", args.target])
        elif args.command == "stats":
            counts = {}
            for path in public_files(ROOT):
                if path.suffix == ".jsonl":
                    counts[path.relative_to(ROOT).as_posix()] = sum(1 for line in path.open(encoding="utf-8") if line.strip())
            print(json.dumps({"version": release_version(ROOT), "public_catalog_records": counts, "note": "Catalog counts are provenance metadata, not bundled retail/private source bodies."}, indent=2))
        elif args.command == "search":
            if not 1 <= args.limit <= 1000:
                raise WorkshopError("Search limit must be between 1 and 1000.")
            count = 0
            for path in public_files(ROOT):
                with path.open(encoding="utf-8", errors="replace") as stream:
                    for line_no, line in enumerate(stream, 1):
                        if args.query.casefold() in line.casefold():
                            print(f"{path.relative_to(ROOT).as_posix()}:{line_no}: {line.rstrip()[:1200]}")
                            count += 1
                            if count >= args.limit:
                                return 0
            if not count:
                print("No matching public metadata or notes.")
        return 0
    except (WorkshopError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
