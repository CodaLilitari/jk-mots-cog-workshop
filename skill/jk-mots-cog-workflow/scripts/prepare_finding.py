"""Prepare optional, reviewed COG research reports locally. Never sends mail."""
from __future__ import annotations
import argparse
from email.message import EmailMessage
from email.policy import SMTP
import hashlib
import json
from pathlib import Path

RECIPIENT = "lilitarikiralv@gmail.com"
MAX_REPORT_BYTES = 64 * 1024


class ReportError(ValueError):
    pass


def template():
    """Deliberately incomplete until the contributor supplies actual evidence."""
    return {
        "schema_version": 1, "kind": "addition", "title": "",
        "target": {"game": "jk", "version": "", "base_game": "jk"},
        "research_review": {"release": "", "references": [], "searches": [], "comparison": ""},
        "finding": {"claim": "", "expected": "", "observed": "", "reproduction": [], "evidence": "", "limitations": "", "proposed_change": ""},
        "credit": "", "public_sources": [], "sharing_review": "",
    }


def require_keys(value, expected, name):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ReportError(f"{name} must have exactly these fields: {', '.join(expected)}")


def text(value, name, limit=12000, header=False):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ReportError(f"{name} must be nonempty text of at most {limit} characters.")
    if any(ord(c) < 32 and c not in "\n\r\t" for c in value) or "\x7f" in value:
        raise ReportError(f"{name} contains a forbidden control character.")
    if header and any(c in value for c in "\r\n\t"):
        raise ReportError(f"{name} must be one line without control characters.")
    return value.strip().replace("\r\n", "\n").replace("\r", "\n")


def text_list(value, name, required=True):
    if not isinstance(value, list) or len(value) > 50 or (required and not value):
        raise ReportError(f"{name} must contain {'1–50' if required else '0–50'} text entries.")
    return [text(item, f"{name}[{index}]", 2000) for index, item in enumerate(value)]


def validate(report):
    require_keys(report, template(), "report")
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        raise ReportError("Unsupported finding schema version.")
    if report["kind"] not in ("addition", "correction"):
        raise ReportError("kind must be addition or correction.")
    cleaned = {"schema_version": 1, "kind": report["kind"], "title": text(report["title"], "title", 160, header=True)}
    target = report["target"]
    require_keys(target, ("game", "version", "base_game"), "target")
    if target["game"] not in ("jk", "mots", "enhanced") or target["base_game"] not in ("jk", "mots"):
        raise ReportError("Target game is jk, mots or enhanced; base_game is jk or mots.")
    if target["game"] in ("jk", "mots") and target["base_game"] != target["game"]:
        raise ReportError("A retail target's base_game must match its game.")
    cleaned["target"] = {**target, "version": text(target["version"], "target.version", 300)}
    review = report["research_review"]
    require_keys(review, ("release", "references", "searches", "comparison"), "research_review")
    cleaned["research_review"] = {
        "release": text(review["release"], "research_review.release", 200),
        "references": text_list(review["references"], "research_review.references"),
        "searches": text_list(review["searches"], "research_review.searches"),
        "comparison": text(review["comparison"], "research_review.comparison"),
    }
    finding = report["finding"]
    require_keys(finding, ("claim", "expected", "observed", "reproduction", "evidence", "limitations", "proposed_change"), "finding")
    cleaned["finding"] = {key: text_list(value, "finding.reproduction") if key == "reproduction" else text(value, "finding." + key) for key, value in finding.items()}
    cleaned["credit"] = text(report["credit"], "credit", 2000)
    cleaned["sharing_review"] = text(report["sharing_review"], "sharing_review", 4000)
    cleaned["public_sources"] = text_list(report["public_sources"], "public_sources", required=False)
    if len(json.dumps(cleaned, ensure_ascii=False).encode("utf-8")) > MAX_REPORT_BYTES:
        raise ReportError("Keep the complete report below 64 KiB.")
    return cleaned


def load_report(path):
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_REPORT_BYTES + 1)
    if len(data) > MAX_REPORT_BYTES:
        raise ReportError("Keep the report below 64 KiB; link separately reviewed public evidence.")
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ReportError("Duplicate JSON fields are not permitted.")
            result[key] = value
        return result
    try:
        return validate(json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique_keys))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReportError("Report must be UTF-8 JSON matching the template.") from exc


def render(report):
    report = validate(report)
    target, review, finding = report["target"], report["research_review"], report["finding"]
    sections = [
        ("Proposed finding", finding["claim"]),
        ("Exact target", f"Game: {target['game']}\nBase game: {target['base_game']}\nExecutable/version/commit: {target['version']}"),
        ("Existing research reviewed", f"Research release: {review['release']}\n\nReferences inspected:\n" + "\n".join("- " + x for x in review["references"]) + "\n\nSearches and comparisons performed:\n" + "\n".join("- " + x for x in review["searches"])),
        ("Why this adds to or corrects the research", review["comparison"]),
        ("Expected result or existing claim", finding["expected"]),
        ("Actual observation", finding["observed"]),
        ("Reproduction", "\n".join(f"{i}. {x}" for i, x in enumerate(finding["reproduction"], 1))),
        ("Evidence and what actually ran", finding["evidence"]),
        ("Limits and unresolved questions", finding["limitations"]),
        ("Proposed research change", finding["proposed_change"]),
        ("Public sources", "\n".join("- " + x for x in report["public_sources"]) or "None supplied; do not infer a public source."),
        ("Contributor credit", report["credit"]),
        ("Contributor sharing review", report["sharing_review"]),
    ]
    body = f"# Proposed COG research {report['kind']}: {report['title']}\n\n"
    body += "This is a proposed contribution. Its novelty, correctness and acceptance require independent review.\n\n"
    body += "\n\n".join(f"## {heading}\n\n{content}" for heading, content in sections) + "\n"
    exact = {"to": RECIPIENT, "subject": f"JK/MotS COG research {report['kind']}: {report['title']}", "body": body, "attachments": []}
    digest = hashlib.sha256(json.dumps(exact, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return exact, digest


def prepare(path, out_prefix):
    exact, digest = render(load_report(path))
    prefix = Path(out_prefix)
    outputs = {"markdown": Path(str(prefix) + ".md"), "email_draft": Path(str(prefix) + ".eml"), "review_receipt": Path(str(prefix) + ".review.json")}
    for destination in outputs.values():
        if destination.exists() or destination.is_symlink():
            raise ReportError("Output already exists; select a new review prefix. No report files were replaced.")
    message = EmailMessage(policy=SMTP)
    message["To"] = exact["to"]
    message["Subject"] = exact["subject"]
    message.set_content(exact["body"])
    receipt = {
        "status": "prepared_not_sent", "report_sha256": digest,
        "review_required": "Show this exact recipient, subject and body; obtain explicit user permission before sending this report through a separate email route.",
        "novelty_status": "contributor_proposal_not_independently_verified", **exact,
    }
    payloads = {"markdown": exact["body"].encode("utf-8"), "email_draft": message.as_bytes(), "review_receipt": (json.dumps(receipt, indent=2, ensure_ascii=False) + "\n").encode("utf-8")}
    created = []
    try:
        for key, destination in outputs.items():
            with destination.open("xb") as stream:
                created.append(destination)
                stream.write(payloads[key])
    except BaseException:
        for destination in created:
            destination.unlink(missing_ok=True)
        raise
    return receipt


def add_commands(parent):
    commands = parent.add_subparsers(dest="report_command", required=True)
    new = commands.add_parser("template", help="Write an incomplete local JSON finding template.")
    new.add_argument("--out", type=Path, required=True)
    draft = commands.add_parser("prepare", help="Create local Markdown and email previews. Never sends.")
    draft.add_argument("report", type=Path)
    draft.add_argument("--out-prefix", type=Path, required=True)


def run(args):
    if args.report_command == "template":
        with args.out.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(template(), stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        print(json.dumps({"status": "template_only_not_sent", "instructions": "Complete every required field with actual evidence and inspect the current research before preparing a report."}))
        return 0
    print(json.dumps(prepare(args.report, args.out_prefix), indent=2, ensure_ascii=False))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_commands(parser)
    try:
        return run(parser.parse_args(argv))
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "not_sent", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
