#!/usr/bin/env python3
"""Generate the corporate-disclosures registry for Tabularium."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

RUSSIA_CORPORATE_ROOT = Path("scrolls/russia/corporate-disclosures")
WORLD_CORPORATE_ROOT = Path("scrolls/world/corporate-disclosures")

RUSSIA_REPORT_ROOTS = (
    RUSSIA_CORPORATE_ROOT / "financial-reporting",
    RUSSIA_CORPORATE_ROOT / "annual-reports",
    RUSSIA_CORPORATE_ROOT / "issuer-reports",
)
RUSSIA_REPORT_EXCLUDED_ROOTS = (
    RUSSIA_CORPORATE_ROOT / "financial-reporting" / "ras-banks",
)
WORLD_REPORT_ROOTS = (
    WORLD_CORPORATE_ROOT / "financial-reporting",
    WORLD_CORPORATE_ROOT / "annual-reports",
)

RUSSIA_STRATEGY_ROOT = RUSSIA_CORPORATE_ROOT / "strategies"
WORLD_STRATEGY_ROOT = WORLD_CORPORATE_ROOT / "strategies"

OUTPUT_PATH = Path("registry/corporate-disclosures.md")
SUPPORTED_EXTENSIONS = {".md", ".html"}
CONTROL_FILENAMES = {"README.md", "AGENTS.md"}

RUSSIA_REPORT_FILENAME_RE = re.compile(
    r"^(?P<entity>.+?)_"
    r"(?P<year>\d{4})М(?P<month>1[0-2]|[1-9])_"
    r"(?P<kind>.+)\."
    r"(?P<extension>md|html)$",
    re.UNICODE,
)

WORLD_REPORT_FILENAME_RE = re.compile(
    r"^(?P<country>[A-Z]{2})_"
    r"(?P<entity>.+?)_"
    r"(?P<period>\d{4}-\d{2}-\d{2})_"
    r"(?P<kind>.+)\."
    r"(?P<extension>md|html)$",
    re.UNICODE,
)

RUSSIA_STRATEGY_FILENAME_RE = re.compile(
    r"^(?P<entity>.+?)_"
    r"(?P<publication_date>\d{4}(?:-\d{2}(?:-\d{2})?)?)_"
    r"(?P<kind>.+)\."
    r"(?P<extension>md|html)$",
    re.UNICODE,
)

WORLD_STRATEGY_FILENAME_RE = re.compile(
    r"^(?P<country>[A-Z]{2})_"
    r"(?P<entity>.+?)_"
    r"(?P<publication_date>\d{4}(?:-\d{2}(?:-\d{2})?)?)_"
    r"(?P<kind>.+)\."
    r"(?P<extension>md|html)$",
    re.UNICODE,
)


@dataclass(frozen=True)
class ReportArtifact:
    entity: str
    period_label: str
    period_key: tuple[int, int, int]
    kind: str
    path: Path


@dataclass(frozen=True)
class StrategyArtifact:
    entity: str
    publication_year: int
    publication_date: str
    publication_key: tuple[int, int, int]
    kind: str
    path: Path


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def iter_publication_files(root: Path):
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        if path.name in CONTROL_FILENAMES:
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        yield path


def discover_russia_reports() -> list[ReportArtifact]:
    artifacts: list[ReportArtifact] = []
    malformed: list[Path] = []

    for root in RUSSIA_REPORT_ROOTS:
        if not root.is_dir():
            continue
        for path in iter_publication_files(root):
            if any(is_within(path, excluded) for excluded in RUSSIA_REPORT_EXCLUDED_ROOTS):
                continue
            match = RUSSIA_REPORT_FILENAME_RE.fullmatch(path.name)
            if match is None:
                malformed.append(path)
                continue
            year = int(match.group("year"))
            month = int(match.group("month"))
            artifacts.append(
                ReportArtifact(
                    entity=match.group("entity"),
                    period_label=f"{year}М{month}",
                    period_key=(year, month, 0),
                    kind=match.group("kind"),
                    path=path,
                )
            )

    if malformed:
        details = "\n".join(f"  - {path.as_posix()}" for path in malformed)
        raise RuntimeError(
            "Russian report files do not match "
            "<COMPANY>_<YYYYМ#>_<DOCUMENT_KIND>.{md,html}:\n"
            f"{details}"
        )
    return artifacts


def discover_world_reports() -> list[ReportArtifact]:
    artifacts: list[ReportArtifact] = []
    malformed: list[Path] = []

    for root in WORLD_REPORT_ROOTS:
        if not root.is_dir():
            continue
        for path in iter_publication_files(root):
            match = WORLD_REPORT_FILENAME_RE.fullmatch(path.name)
            if match is None:
                malformed.append(path)
                continue
            period = match.group("period")
            try:
                parsed = date.fromisoformat(period)
            except ValueError:
                malformed.append(path)
                continue
            artifacts.append(
                ReportArtifact(
                    entity=f"{match.group('country')}_{match.group('entity')}",
                    period_label=period,
                    period_key=(parsed.year, parsed.month, parsed.day),
                    kind=match.group("kind"),
                    path=path,
                )
            )

    if malformed:
        details = "\n".join(f"  - {path.as_posix()}" for path in malformed)
        raise RuntimeError(
            "World report files do not match "
            "<CC>_<ENTITY>_<YYYY-MM-DD>_<PUBLICATION-TYPE>[...].{md,html}:\n"
            f"{details}"
        )
    return artifacts


def parse_partial_iso_date(value: str) -> tuple[int, int, int]:
    parts = value.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) >= 2 else 0
    day = int(parts[2]) if len(parts) >= 3 else 0

    if len(parts) == 1:
        return (year, 0, 0)
    if len(parts) == 2:
        if not 1 <= month <= 12:
            raise ValueError(value)
        return (year, month, 0)

    date(year, month, day)
    return (year, month, day)


def discover_strategies(
    root: Path,
    pattern: re.Pattern[str],
    *,
    world: bool,
) -> list[StrategyArtifact]:
    artifacts: list[StrategyArtifact] = []
    malformed: list[Path] = []

    if not root.is_dir():
        return artifacts

    for path in iter_publication_files(root):
        try:
            relative = path.relative_to(root)
        except ValueError:
            malformed.append(path)
            continue

        if len(relative.parts) < 2 or not relative.parts[0].isdigit():
            malformed.append(path)
            continue

        directory_year = int(relative.parts[0])
        match = pattern.fullmatch(path.name)
        if match is None:
            malformed.append(path)
            continue

        publication_date = match.group("publication_date")
        try:
            publication_key = parse_partial_iso_date(publication_date)
        except ValueError:
            malformed.append(path)
            continue

        if publication_key[0] != directory_year:
            malformed.append(path)
            continue

        entity = match.group("entity")
        if world:
            entity = f"{match.group('country')}_{entity}"

        artifacts.append(
            StrategyArtifact(
                entity=entity,
                publication_year=directory_year,
                publication_date=publication_date,
                publication_key=publication_key,
                kind=match.group("kind"),
                path=path,
            )
        )

    if malformed:
        contract = (
            "<CC>_<ENTITY>_<PUBLICATION-DATE>_<PUBLICATION-TYPE>[...].{md,html}"
            if world
            else "<ENTITY>_<PUBLICATION-DATE>_<DOCUMENT-KIND>[...].{md,html}"
        )
        details = "\n".join(f"  - {path.as_posix()}" for path in malformed)
        raise RuntimeError(
            f"Strategy files must sit under their publication-year directory and match "
            f"{contract}; the filename publication year must equal the directory year:\n"
            f"{details}"
        )

    return artifacts


def validate_report_collisions(artifacts: list[ReportArtifact], label: str) -> None:
    by_identity: dict[tuple[str, tuple[int, int, int], str], list[ReportArtifact]] = {}
    for artifact in artifacts:
        key = (artifact.entity, artifact.period_key, artifact.kind)
        by_identity.setdefault(key, []).append(artifact)

    collisions = {key: items for key, items in by_identity.items() if len(items) > 1}
    if not collisions:
        return

    lines = [f"Duplicate {label} report identities detected:"]
    for (entity, _, kind), items in sorted(collisions.items()):
        lines.append(f"  - {entity}: {kind}")
        lines.extend(f"      {item.path.as_posix()}" for item in items)
    raise RuntimeError("\n".join(lines))


def validate_strategy_collisions(artifacts: list[StrategyArtifact], label: str) -> None:
    by_identity: dict[tuple[str, str, str], list[StrategyArtifact]] = {}
    for artifact in artifacts:
        key = (artifact.entity, artifact.publication_date, artifact.kind)
        by_identity.setdefault(key, []).append(artifact)

    collisions = {key: items for key, items in by_identity.items() if len(items) > 1}
    if not collisions:
        return

    lines = [f"Duplicate {label} strategy identities detected:"]
    for (entity, publication_date, kind), items in sorted(collisions.items()):
        lines.append(f"  - {entity}_{publication_date}_{kind}")
        lines.extend(f"      {item.path.as_posix()}" for item in items)
    raise RuntimeError("\n".join(lines))


def select_latest_reports(artifacts: list[ReportArtifact]) -> list[ReportArtifact]:
    latest: dict[tuple[str, str], ReportArtifact] = {}
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


def render_report_table(artifacts: list[ReportArtifact]) -> list[str]:
    latest = select_latest_reports(artifacts)
    grouped: dict[tuple[str, str, tuple[int, int, int]], list[ReportArtifact]] = {}
    for artifact in latest:
        key = (artifact.entity, artifact.period_label, artifact.period_key)
        grouped.setdefault(key, []).append(artifact)

    rows = sorted(
        grouped.items(),
        key=lambda item: (item[0][0].casefold(), tuple(-v for v in item[0][2])),
    )

    lines = [
        "| Company | Latest reporting period | Report type |",
        "|---|---:|---|",
    ]
    for (entity, period_label, _), items in rows:
        docs = []
        for artifact in sorted(items, key=lambda item: item.kind.casefold()):
            label = escape_table_text(artifact.kind)
            docs.append(f"[{label}]({relative_link(artifact.path)})")
        lines.append(
            f"| {escape_table_text(entity)} | {period_label} | "
            f"{'<br>'.join(docs)} |"
        )
    return lines


def render_strategy_block(artifacts: list[StrategyArtifact]) -> list[str]:
    if not artifacts:
        return ["_No strategy documents are currently loaded._"]

    by_year: dict[int, list[StrategyArtifact]] = {}
    for artifact in artifacts:
        by_year.setdefault(artifact.publication_year, []).append(artifact)

    lines: list[str] = []
    for year in sorted(by_year, reverse=True):
        items = sorted(
            by_year[year],
            key=lambda item: (
                item.entity.casefold(),
                tuple(-value for value in item.publication_key),
                item.kind.casefold(),
            ),
        )
        rendered = [
            f"{escape_table_text(item.entity)} - "
            f"[{escape_table_text(item.kind)}]({relative_link(item.path)})"
            for item in items
        ]
        lines.append(f"- **{year}:** " + "; ".join(rendered))
    return lines


def generate() -> str:
    russia_reports = discover_russia_reports()
    world_reports = discover_world_reports()
    russia_strategies = discover_strategies(
        RUSSIA_STRATEGY_ROOT,
        RUSSIA_STRATEGY_FILENAME_RE,
        world=False,
    )
    world_strategies = discover_strategies(
        WORLD_STRATEGY_ROOT,
        WORLD_STRATEGY_FILENAME_RE,
        world=True,
    )

    validate_report_collisions(russia_reports, "Russian")
    validate_report_collisions(world_reports, "world")
    validate_strategy_collisions(russia_strategies, "Russian")
    validate_strategy_collisions(world_strategies, "world")

    lines = [
        "# Corporate disclosures registry",
        "",
        "This file is generated automatically from the corporate-disclosure source "
        "routes under `scrolls/russia/` and `scrolls/world/`.",
        "",
        "The registry has four independent sections. Report tables are latest-period "
        "navigational projections; strategy blocks are publication inventories and are "
        "not reduced to a latest-period view.",
        "",
        "Generation rules:",
        "",
        "- Russian report identity follows `<COMPANY>_<YYYYМ#>_<DOCUMENT_KIND>.{md,html}`.",
        "- World report identity follows `<CC>_<ENTITY>_<YYYY-MM-DD>_<PUBLICATION-TYPE>[...].{md,html}`.",
        "- Strategy inventories use their publication-year directories and publication-date filenames; "
        "strategy or forecast horizon is not used as the registry year.",
        "- Control files are excluded. Strategy documents are listed separately from report tables.",
        "",
        "## 1. Russian company reports",
        "",
        "Included routes: Russian financial reporting, annual reports, and issuer reports. "
        "Bank of Russia `ras-banks` bridge material is excluded.",
        "",
    ]
    lines.extend(render_report_table(russia_reports))
    lines.extend(
        [
            "",
            "## 2. Russian strategic documents",
            "",
            "Grouped by source publication year, newest year first. The year is the "
            "publication year, not the strategy or forecast horizon.",
            "",
        ]
    )
    lines.extend(render_strategy_block(russia_strategies))
    lines.extend(
        [
            "",
            "## 3. World company reports",
            "",
            "Included routes: world financial reporting and annual reports. Company "
            "identity retains the ISO country prefix used by the world corpus.",
            "",
        ]
    )
    lines.extend(render_report_table(world_reports))
    lines.extend(
        [
            "",
            "## 4. World strategic documents",
            "",
            "Grouped by source publication year, newest year first. The year is the "
            "publication year, not the strategy or forecast horizon.",
            "",
        ]
    )
    lines.extend(render_strategy_block(world_strategies))
    lines.extend(
        [
            "",
            "This registry is a navigational projection of repository contents. It does "
            "not assert semantic equivalence between documents, reporting perimeters, "
            "strategy horizons, targets, forecasts, or outcomes.",
            "",
        ]
    )
    return "\n".join(lines)


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
