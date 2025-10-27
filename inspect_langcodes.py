#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["langcodes"]
# ///
"""Resolve language names and tags using langcodes."""

import argparse
import sys
from typing import Iterable

from langcodes import Language, find, standardize_tag, tag_distance, tag_is_valid
from langcodes.data_dicts import (
    LANGUAGE_ALPHA3,
    LANGUAGE_ALPHA3_BIBLIOGRAPHIC,
    LANGUAGE_REPLACEMENTS,
    MACROLANGUAGES,
    NORMALIZED_MACROLANGUAGES,
)


def _to_standard_tag(value: Language | str) -> str | None:
    """Return a standardized BCP 47 tag for ``value`` if possible."""

    if isinstance(value, Language):
        value = value.to_tag()
    try:
        return standardize_tag(value)
    except Exception:  # pragma: no cover - defensive, depends on langcodes internals
        return None


MAX_NEAR_DISTANCE = 1
US_TERRITORY_LANG_ALLOWLIST = {"en", "es"}


def _is_near_identical(base_tag: str, candidate: str) -> bool:
    """Return True when ``candidate`` is effectively identical to ``base_tag``."""

    try:
        forward = tag_distance(base_tag, candidate)
        backward = tag_distance(candidate, base_tag)
    except Exception:  # pragma: no cover - resilient to langcodes data issues
        return False
    return forward <= MAX_NEAR_DISTANCE and backward <= MAX_NEAR_DISTANCE


def _collect_related_codes(
    lang: Language,
    maximized: Language | None = None,
    base_tag: str | None = None,
) -> list[str]:
    """Collect canonical and closely related language tags for ``lang``."""

    tags: list[str] = []
    seen: set[str] = set()

    def add(values: Iterable[str | Language]) -> None:
        for val in values:
            raw = val.to_tag() if isinstance(val, Language) else str(val)
            tag = _to_standard_tag(val)

            for candidate in (tag, raw):
                if candidate and candidate not in seen:
                    seen.add(candidate)
                    tags.append(candidate)

    add([lang])

    try:
        minimized = lang.minimize()
    except Exception:  # pragma: no cover - varies by lang tag completeness
        minimized = None
    if minimized:
        add([minimized])

    if maximized is None:
        try:
            maximized = lang.maximize()
        except Exception:  # pragma: no cover - maximize may fail for unusual tags
            maximized = None

    if maximized:
        add([maximized])

        base = getattr(maximized, "language", None) or None
        script = getattr(maximized, "script", None) or None
        territory = getattr(maximized, "territory", None) or None

        variants: list[str] = []
        for attr in ("variants", "variant"):
            value = getattr(maximized, attr, None)
            if not value:
                continue
            if isinstance(value, str):
                variants.append(value)
            else:
                variants.extend(str(item) for item in value if item)

        components: list[str] = []
        if base:
            components.append(base)
            if script:
                components.append(f"{base}-{script}")
            if territory:
                components.append(f"{base}-{territory}")
            if script and territory:
                components.append(f"{base}-{script}-{territory}")
            for variant in variants:
                components.append(f"{base}-{variant}")
                if script:
                    components.append(f"{base}-{script}-{variant}")
                if territory:
                    components.append(f"{base}-{territory}-{variant}")
                if script and territory:
                    components.append(f"{base}-{script}-{territory}-{variant}")

        add(components)

    base_language = getattr(lang, "language", None)
    if base_language:
        add([
            code
            for code, macro in MACROLANGUAGES.items()
            if macro == base_language
        ])

        parent = MACROLANGUAGES.get(base_language)
        if parent:
            add([parent])

        add([
            code
            for code, macro in NORMALIZED_MACROLANGUAGES.items()
            if macro == base_language
        ])

        normalized_parent = NORMALIZED_MACROLANGUAGES.get(base_language)
        if normalized_parent:
            add([normalized_parent])

        add([
            code
            for code, replacement in LANGUAGE_REPLACEMENTS.items()
            if replacement == base_language
        ])

        add([
            replacement
            for replacement, canonical in LANGUAGE_REPLACEMENTS.items()
            if canonical == base_language
        ])

        for getter in ((lambda: LANGUAGE_ALPHA3.get(base_language)),
                       (lambda: LANGUAGE_ALPHA3_BIBLIOGRAPHIC.get(base_language))):
            try:
                code = getter()
            except Exception:  # pragma: no cover - mapping lookups should not fail
                code = None
            if code:
                add([code])

    primary = _to_standard_tag(lang)
    reference = base_tag or primary or lang.to_tag()

    if not reference:
        return [tag for tag in tags if tag and tag != primary]

    filtered: list[str] = []
    for candidate in tags:
        if not candidate or candidate == primary:
            continue
        try:
            candidate_lang = Language.get(candidate)
        except Exception:  # pragma: no cover - language parser is strict
            candidate_lang = None

        if (
            candidate_lang
            and (candidate_lang.territory or "").upper() == "US"
            and (candidate_lang.language or "").lower() not in US_TERRITORY_LANG_ALLOWLIST
        ):
            continue
        if _is_near_identical(reference, candidate):
            filtered.append(candidate)
    return filtered


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+", help="Language tag or English name")
    parser.add_argument(
        "-s",
        "--simple",
        action="store_true",
        help="Only show the primary result (legacy behaviour)",
    )
    args = parser.parse_args(argv)

    query = " ".join(args.query).strip()
    if not query:
        parser.error("Expected a non-empty query")

    try:
        if tag_is_valid(query):
            lang = Language.get(query)
            if args.simple:
                print(lang.display_name())
                return 0
        else:
            lang = find(query)
            if args.simple:
                print(f"{standardize_tag(lang)}: {lang.describe()}")
                return 0

        tag = _to_standard_tag(lang) or query
        description = lang.describe()

        print(f"Tag: {tag}")
        print(f"Name: {description}")

        try:
            maximized = lang.maximize()
        except Exception:  # pragma: no cover - maximize may fail for incomplete tags
            maximized = None

        likely_script = getattr(maximized, "script", None) or "Unknown"
        print(f"Likely script: {likely_script}")

        related = _collect_related_codes(lang, maximized=maximized, base_tag=tag)
        if related:
            print("Identical or near-identical codes:")
            for code in related:
                try:
                    display_name = Language.get(code).display_name()
                except Exception:  # pragma: no cover - fallback for non-standard codes
                    display_name = "Unknown"
                print(f"  - {code}: {display_name}")
        return 0
    except Exception as exc:  # pragma: no cover - simple CLI
        print(f"langcodes: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
