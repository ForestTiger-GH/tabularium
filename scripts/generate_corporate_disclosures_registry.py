#!/usr/bin/env python3
"""Generate the latest corporate-disclosures registry for Tabularium."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CORPORATE_ROOT = Path("scrolls/russia/corporate-disclosures")
EXCLUDED_ROOT = CORPORATE_ROOT / "financial-reporting" / "ras-banks"
OUTPUT_PATH = Path("registry/corporate-disclosures.md")
SUPPORTED_EXTENSIONS = {".md", ".html"}
CONTROL_FILENAMES = {"README.md", "AGENTS.md"}

FILENAME_RE = re.compile(
    r"^(?P<entity>.+?)_"
    r"(?P<year>\d{4})М(?P<month>1[0-2]|[1-9])_"
    r"(?P<kind>.+)\."
    r"(?P<extension>md|html)$",
    re.UNICODE,
)


@dataclass(frozen=True)
class Artifact:
    entity: str
    year: int
    month: int
    kind: str
    extension: str
    path: Path

    @property
    def period(self) -> str:
        return f"{self.year}М{self.month}"

    @property
    def period_key(self) -> tuple[int, int]:
        return (self.year, self.month)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def discover_artifacts() -> list[Artifact]:
    if not CORPORATE_ROOT.is_dir():
        raise RuntimeError(f"Corporate disclosures root not found: {CORPORATE_ROOT}")

    artifacts: list[Artifact] = []
    malformed: list[Path] = []

    for path in sorted(CORPORATE_ROOT.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        if is_within(path, EXCLUDED_ROOT):
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if path.name in CONTROL_FILENAMES:
            continue

        match = FILENAME_RE.fullmatch(path.name)
        if match is None:
            malformed.append(path)
            continue

        artifacts.append(
            Artifact(
                entity=match.group("entity"),
                year=int(match.group("year")),
                month=int(match.group("month")),
                kind=match.group("kind"),
                extension=match.group("extension").lower(),
                path=path,
            )
        )

    if malformed:
        details = "\n".join(f"  - {path.as_posix()}" for path in malformed)
        raise RuntimeError(
            "Found .md/.html files outside ras-banks that do not match the "
            "corporate publication filename contract "
            "<COMPANY>_<YYYYМ#>_<DOCUMENT_KIND>.{md,html}:\n"
            f"{details}"
        )

    if not artifacts:
        raise RuntimeError("No corporate publication artifacts found.")

    return artifacts


def validate_no_collisions(artifacts: list[Artifact]) -> None:
    by_identity: dict[tuple[str, int, int, str], list[Artifact]] = {}
    for artifact in artifacts:
        key = (artifact.entity, artifact.year, artifact.month, artifact.kind)
        by_identity.setdefault(key, []).append(artifact)

    collisions = {key: items for key, items in by_identity.items() if len(items) > 1}
    if not collisions:
        return

    lines = ["Duplicate corporate publication identities detected:"]
    for (entity, year, month, kind), items in sorted(collisions.items()):
        lines.append(f"  - {entity}_{year}М{month}_{kind}")
        lines.extend(f"      {item.path.as_posix()}" for item in items)
    raise RuntimeError("\n".join(lines))


def select_latest(artifacts: list[Artifact]) -> list[Artifact]:
    latest: dict[tuple[str, str], Artifact] = {}
    for artifact in artifacts:
        key = (artifact.entity, artifact.kind)
        current = latest.get(key)
        if current is None or artifact.period_key > current.period_key:
            latest[key] = artifact
    return list(latest.values())


def escape_table_text(value: str) -> str:
    return value.replace("|", r"\|")


def relative_link(path: Path) -> str:
    return Path(os.path.relpath(path, OUTPUT_PATH.parent)).as_posix()


def render_registry(latest: list[Artifact]) -> str:
    grouped: dict[tuple[str, int, int], list[Artifact]] = {}
    for artifact in latest:
        key = (artifact.entity, artifact.year, artifact.month)
        grouped.setdefault(key, []).append(artifact)

    rows = sorted(
        grouped.items(),
        key=lambda item: (item[0][0].casefold(), -item[0][1], -item[0][2]),
    )

    lines = [
        "# Corporate disclosures registry",
        "",
        "This file is generated automatically from publication artifacts under "
        "`scrolls/russia/corporate-disclosures/`.",
        "",
        "Rules:",
        "",
        "- `scrolls/russia/corporate-disclosures/financial-reporting/ras-banks/` is excluded.",
        "- Only `.md` and `.html` publication artifacts are included.",
        "- Publication filenames follow "
        "`<COMPANY>_<YYYYМ#>_<DOCUMENT_KIND>.{md,html}`.",
        "- The document kind is the literal filename suffix after the reporting period; "
        "it is not normalized or reinterpreted.",
        "- For each company and document kind, only the latest reporting period present "
        "in the repository is shown.",
        "- Document kinds whose latest artifacts share the same reporting period are "
        "shown together in one table cell.",
        "",
        "This registry is a navigational projection of repository contents. It does not "
        "assert semantic equivalence between documents or reporting perimeters.",
        "",
        "| Company | Latest reporting period | Report type |",
        "|---|---:|---|",
    ]

    for (entity, year, month), artifacts in rows:
        docs = []
        for artifact in sorted(artifacts, key=lambda item: item.kind.casefold()):
            label = escape_table_text(artifact.kind)
            docs.append(f"[{label}]({relative_link(artifact.path)})")
        lines.append(
            f"| {escape_table_text(entity)} | {year}М{month} | "
            f"{'<br>'.join(docs)} |"
        )

    lines.append("")
    return "\n".join(lines)


def generate() -> str:
    artifacts = discover_artifacts()
    validate_no_collisions(artifacts)
    return render_registry(select_latest(artifacts))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the generated registry differs from the committed file.",
    )
    args = parser.parse_args()

    try:
        content = generate()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if not OUTPUT_PATH.exists():
            print(f"error: registry file does not exist: {OUTPUT_PATH}", file=sys.stderr)
            return 1
        current = OUTPUT_PATH.read_text(encoding="utf-8")
        if current != content:
            print(f"error: registry is out of date: {OUTPUT_PATH}", file=sys.stderr)
            return 1
        print(f"Registry is up to date: {OUTPUT_PATH}")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8", newline="\n")
    print(f"Updated {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
