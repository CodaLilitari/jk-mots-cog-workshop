#!/usr/bin/env python3
"""Read-only authored COG instance accounting, not a game parser or runtime test.

Inspired by SM Sith Lord's P68 Survival Arena capacity report:
https://smsithlord.com/openjkdf2libretro/cogfactory/gen1/p68-survival-arena.html
Original implementation; no source or assets copied from that project.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

MAX_BYTES = 8 * 1024 * 1024
MAX_LINE = 1023
SOURCE_URL = "https://smsithlord.com/openjkdf2libretro/cogfactory/gen1/p68-survival-arena.html"
DECIMAL = re.compile(r"[0-9]+\Z")
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


class FormatError(ValueError):
    """Input is outside the deliberately conservative accounting grammar."""


def nonnegative(value):
    if not DECIMAL.fullmatch(value) or len(value) > 10 or int(value) > 2147483647:
        raise argparse.ArgumentTypeError("Expected a nonnegative decimal int32.")
    return int(value)


def lines(text):
    """The inspected reader lowercases, splits commas/space, and strips #.

    A semicolon starts a comment only in column zero. Backslashes inside a
    filename remain characters, not escape sequences. Continuations and quoted
    tokens are outside this preflight's grammar, and are never guessed.
    """
    if any((ord(c) < 32 and c not in "\t\r\n") or 127 <= ord(c) <= 159 for c in text):
        raise FormatError("input contains an unsupported control byte (including in comments)")
    text = text.replace("\r\n", "\n")
    if "\r" in text:
        raise FormatError("bare CR line endings are not supported; use LF or CRLF")
    for number, original in enumerate(text.split("\n"), 1):
        if len(original) > MAX_LINE:
            raise FormatError(f"line {number}: line exceeds conservative {MAX_LINE}-character bound")
        if original.startswith((";", "#")):
            continue
        value = original.split("#", 1)[0]
        if not value.strip():
            continue
        if value.rstrip().endswith("\\"):
            raise FormatError(f"line {number}: line continuation is not supported")
        if any(c in value for c in ('\"', "'", "\x00")):
            raise FormatError(f"line {number}: quoted or NUL-containing input is not supported")
        yield number, re.split(r"[, \t]+", value.strip())


def integer(value, number, name):
    try:
        return nonnegative(value)
    except argparse.ArgumentTypeError as exc:
        raise FormatError(f"line {number}: {name} must be a nonnegative decimal int32") from exc


def filename(value, number):
    if not value or "=" in value or value.startswith((";", ":")):
        raise FormatError(f"line {number}: malformed script binding")
    return value


def parse_static(text):
    sections = 0
    active = False
    ended = False
    capacity = None
    rows = []
    row_ids = set()
    for number, tokens in lines(text):
        lower = [token.lower() for token in tokens]
        if lower[0] == "section:":
            if active and not ended:
                raise FormatError(f"line {number}: COGS section has no end marker")
            if len(tokens) != 2:
                raise FormatError(f"line {number}: malformed section header")
            active = lower[1] == "cogs"
            if active:
                sections += 1
                if sections > 1:
                    raise FormatError(f"line {number}: duplicate COGS section")
                ended = False
            continue
        if lower[:2] == ["world", "cogs"] and not active:
            raise FormatError(f"line {number}: World cogs header is outside the COGS section")
        if not active:
            continue
        if ended:
            raise FormatError(f"line {number}: unexpected content after COGS end")
        if lower[:2] == ["world", "cogs"]:
            if capacity is not None or rows:
                raise FormatError(f"line {number}: duplicate World cogs header")
            if len(tokens) != 3:
                raise FormatError(f"line {number}: malformed World cogs header")
            capacity = integer(tokens[2], number, "capacity")
        elif lower[0] == "end":
            if len(tokens) != 1 or capacity is None:
                raise FormatError(f"line {number}: malformed end or missing World cogs header")
            ended = True
        else:
            if capacity is None or len(tokens) < 2 or not re.fullmatch(r"[0-9]+:", tokens[0]):
                raise FormatError(f"line {number}: expected a conventional numbered COG row")
            row_id = integer(tokens[0][:-1], number, "row index")
            if row_id in row_ids:
                raise FormatError(f"line {number}: duplicate COG row index")
            row_ids.add(row_id)
            rows.append({"line": number, "index": row_id, "script": filename(tokens[1], number)})
    if sections != 1 or capacity is None or not ended:
        raise FormatError("expected one complete SECTION: COGS, World cogs header and end marker")
    return {"capacity": capacity, "placed_instances": len(rows), "bindings": rows}


def parse_items(text):
    ended = False
    rows = 0
    bindings = []
    for number, tokens in lines(text):
        if ended:
            raise FormatError(f"line {number}: unexpected content after ITEMS.DAT end")
        if tokens[0].lower() == "end":
            if len(tokens) != 1:
                raise FormatError(f"line {number}: malformed ITEMS.DAT end")
            ended = True
            continue
        if len(tokens) < 5 or any("=" in token for token in tokens[:5]):
            raise FormatError(f"line {number}: item requires name, bin, minimum, maximum and flags")
        bin_id = integer(tokens[1], number, "item bin")
        if bin_id >= 200:
            raise FormatError(f"line {number}: item bin is outside the inspected 0..199 range")
        for token in tokens[2:4]:
            if not NUMBER.fullmatch(token) or not math.isfinite(float(token)):
                raise FormatError(f"line {number}: malformed item minimum/maximum")
        if not re.fullmatch(r"(?:0[xX])?[0-9a-fA-F]{1,8}", tokens[4]):
            raise FormatError(f"line {number}: flags must be a hexadecimal uint32")
        rows += 1
        for token in tokens[5:]:
            if token.count("=") != 1:
                raise FormatError(f"line {number}: optional item fields require key=value without spaces")
            key, value = token.split("=", 1)
            if not key or not value:
                raise FormatError(f"line {number}: empty optional item field")
            if key.lower() == "cog":
                bindings.append({"line": number, "bin": bin_id, "script": filename(value, number)})
    if not ended:
        raise FormatError("ITEMS.DAT has no end marker")
    return {"item_rows": rows, "item_instances": len(bindings), "bindings": bindings}


def read_input(path):
    path = Path(path)
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise FormatError(f"input exceeds {MAX_BYTES}-byte bound; no complete hash computed")
    identity = {"name": path.name, "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    # The accounting syntax is ASCII. Latin-1 preserves all other byte values
    # without replacement, so a filename does not change through decoding.
    return raw.decode("latin-1"), identity


def audit(static_path, items_path, reserve=0):
    result = {
        "schema_version": 1,
        "status": "unknown",
        "scope": "Authored-input COG instance budget assuming successful loads; not runtime or retail certification.",
        "credit": {"inspiration": "SM Sith Lord", "source_url": SOURCE_URL},
        "inputs": {},
        "observations": {},
        "reserve": reserve,
        "instance_budget": None,
        "script_table": {"status": "not_assessed", "reason": "Instance counts and unique filenames do not establish script-table capacity, cache identity or successful resource loading."},
        "errors": [],
    }
    if type(reserve) is not int or not 0 <= reserve <= 2147483647:
        result["errors"].append({"input": "reserve", "message": "reserve must be a nonnegative decimal int32"})
        return result
    for label, path, parser in (("static_jkl", static_path, parse_static), ("items_dat", items_path, parse_items)):
        try:
            text, identity = read_input(path)
            result["inputs"][label] = identity
            result["observations"][label] = parser(text)
        except (OSError, FormatError) as exc:
            # No absolute paths in receipts or platform-specific error details.
            message = str(exc) if isinstance(exc, FormatError) else f"input cannot be read ({type(exc).__name__})"
            result["errors"].append({"input": label, "message": message})
    if result["errors"]:
        return result
    static = result["observations"]["static_jkl"]
    items = result["observations"]["items_dat"]
    required = static["placed_instances"] + items["item_instances"] + reserve
    headroom = static["capacity"] - required
    result["instance_budget"] = {
        "capacity": static["capacity"], "placed_instances": static["placed_instances"],
        "item_instances": items["item_instances"], "reserved_instances": reserve,
        "required_instances": required, "headroom": headroom, "shortfall": max(0, -headroom),
    }
    result["status"] = "fits" if headroom >= 0 else "shortfall"
    return result


def add_arguments(parser):
    parser.add_argument("static_jkl", type=Path)
    parser.add_argument("items_dat", type=Path)
    parser.add_argument("--reserve", type=nonnegative, default=0, help="Explicit extra instance allowance for producers not counted from these two inputs (default 0).")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    args = parser.parse_args(argv)
    result = audit(args.static_jkl, args.items_dat, args.reserve)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return {"fits": 0, "shortfall": 1, "unknown": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
