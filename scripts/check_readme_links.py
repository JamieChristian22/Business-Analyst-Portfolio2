#!/usr/bin/env python3
"""Check relative Markdown links in the repository's root README.md.

This offline check intentionally ignores external URLs and fragment identifiers.
It does not validate website reachability or all Markdown/HTML link syntaxes.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
LINK = re.compile(r"!?(?:\[[^\]]*\])\(((?:\\.|[^)])*)\)")


def referenced_paths(markdown: str):
    for match in LINK.finditer(markdown):
        target = match.group(1).strip()
        if target.startswith("<") and ">" in target:
            target = target[1 : target.index(">")]
        else:
            target = re.sub(r"""\s+(?:"[^"]*"|'[^']*')$""", "", target)
        target = re.sub(r"\\([() ])", r"\1", target)
        if not target or target.startswith(("#", "//")):
            continue
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        decoded = unquote(urlsplit(target).path)
        if decoded:
            yield match.group(0), decoded


def main() -> int:
    if not README.is_file():
        print("ERROR: README.md is missing", file=sys.stderr)
        return 1
    checked = 0
    problems = []
    for markup, raw_path in referenced_paths(README.read_text(encoding="utf-8")):
        resolved = (ROOT / raw_path.lstrip("/")).resolve()
        checked += 1
        if not resolved.is_relative_to(ROOT.resolve()) or not resolved.exists():
            problems.append((markup, raw_path))
    for markup, path in problems:
        print(f"BROKEN: {path} (from {markup})", file=sys.stderr)
    print(f"Checked {checked} local README references; {len(problems)} missing.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
