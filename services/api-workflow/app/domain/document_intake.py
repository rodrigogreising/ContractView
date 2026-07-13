"""Pure deterministic document-profile evaluation and matching.

This module has no persistence, HTTP, OCR, or framework dependency. It turns a
declared profile plus OCR text into canonical signals, an exact fingerprint,
source-located draft fields, and reproducible evaluation evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
import unicodedata
from typing import Any, Iterable

FINGERPRINT_ALGORITHM = "sha256-canonical-json-v1"
FINGERPRINT_SPECIFICATION_VERSION = "document-layout-signals-v1"
PARSER_VERSION = "deterministic-document-profile-parser-v1"
EVALUATION_SUITE_VERSION = "document-profile-fixtures-v1"


class DocumentProfileError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedField:
    name: str
    field_type: str
    value: str
    source_location: str
    source_line: int
    source_label: str


@dataclass(frozen=True)
class ProfileAnalysis:
    language_tag: str
    signals: dict[str, Any]
    fingerprint: str
    fields: tuple[ParsedField, ...]


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(value: object) -> str:
    return sha256(canonical_json(value).encode()).hexdigest()


def normalize_token(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(ascii_text.casefold().strip().split())


def _lines(text: str) -> list[tuple[int, str, str]]:
    return [
        (number, raw.strip(), normalize_token(raw))
        for number, raw in enumerate(text.splitlines(), start=1)
        if raw.strip()
    ]


def _label_value(raw: str, normalized: str, labels: Iterable[str]) -> tuple[str, str] | None:
    for label in labels:
        canonical = normalize_token(label).rstrip(":")
        if normalized == canonical:
            return label, ""
        for separator in (":", " - "):
            prefix = canonical + separator
            if normalized.startswith(prefix):
                split_at = raw.find(":" if separator == ":" else " - ")
                return label, raw[split_at + len(separator):].strip()
    return None


def _field_source(
    field: dict[str, Any],
    profile: dict[str, Any],
    lines: list[tuple[int, str, str]],
) -> tuple[int, str, str] | None:
    for number, raw, normalized in lines:
        candidate = _label_value(raw, normalized, field["sourceLabels"])
        if candidate is not None and candidate[1]:
            return number, candidate[0], candidate[1]
    if field["name"] == "vendor":
        aliases = {normalize_token(item): item for item in profile["vendorAliases"]}
        for number, raw, normalized in lines:
            if normalized in aliases:
                return number, "vendor_alias", raw
    return None


def _normalize_value(operation: str, raw: str) -> str:
    value = raw.strip()
    if operation == "trim":
        return value
    if operation == "casefold":
        return normalize_token(value)
    if operation == "iso_date":
        match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", value)
        if not match:
            raise DocumentProfileError("Date does not contain an ISO value")
        return match.group(1)
    if operation == "decimal":
        match = re.search(r"-?\d[\d,]*\.\d{2}", value)
        if not match:
            raise DocumentProfileError("Amount does not contain a decimal value")
        try:
            return str(Decimal(match.group(0).replace(",", "")).quantize(Decimal("0.01")))
        except InvalidOperation as error:
            raise DocumentProfileError("Amount is not a finite decimal") from error
    if operation == "identifier":
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9-]+", normalized):
            raise DocumentProfileError("Reference is not a supported identifier")
        return normalized
    raise DocumentProfileError(f"Unsupported normalization operation: {operation}")


def analyze_profile(
    profile: dict[str, Any],
    text: str,
    media_type: str,
    *,
    require_fields: bool = True,
) -> ProfileAnalysis:
    lines = _lines(text)
    fields: list[ParsedField] = []
    anchors: list[dict[str, Any]] = []
    for field in profile["requiredFields"]:
        source = _field_source(field, profile, lines)
        if source is None:
            if field["required"] and require_fields:
                raise DocumentProfileError(f"Required field is missing: {field['name']}")
            continue
        number, label, raw_value = source
        value = _normalize_value(field["normalization"], raw_value)
        fields.append(
            ParsedField(
                name=field["name"],
                field_type=field["fieldType"],
                value=value,
                source_location=f"page=1;line={number};label={normalize_token(label)}",
                source_line=number,
                source_label=normalize_token(label),
            )
        )
        anchors.append({"field": field["name"], "line": number})

    ordered = sorted(anchors, key=lambda item: item["line"])
    normalized_anchors = [
        {"field": item["field"], "position": index + 1}
        for index, item in enumerate(ordered)
    ]
    signals = {
        "artifactMediaType": media_type,
        "languageTag": profile["languageTag"],
        "normalizedTextTokens": [item["field"] for item in normalized_anchors],
        "pageGeometry": {"pageCount": 1, "recognizedAnchorCount": len(ordered)},
        "anchorPositions": normalized_anchors,
    }
    fingerprint = content_hash(
        {
            "algorithm": FINGERPRINT_ALGORITHM,
            "specificationVersion": FINGERPRINT_SPECIFICATION_VERSION,
            "signals": signals,
        }
    )
    return ProfileAnalysis(profile["languageTag"], signals, fingerprint, tuple(fields))


def exact_profile_match(
    profiles: Iterable[dict[str, Any]], text: str, media_type: str
) -> tuple[dict[str, Any], ProfileAnalysis] | None:
    matches: list[tuple[dict[str, Any], ProfileAnalysis]] = []
    for profile in profiles:
        analysis = analyze_profile(profile, text, media_type, require_fields=False)
        if analysis.fingerprint not in profile["acceptedFingerprints"]:
            continue
        try:
            complete = analyze_profile(profile, text, media_type, require_fields=True)
        except DocumentProfileError:
            continue
        matches.append((profile, complete))
    if len(matches) > 1:
        raise DocumentProfileError("Document matched more than one active profile")
    return matches[0] if matches else None


def detect_language(text: str) -> str:
    normalized = normalize_token(text)
    spanish = sum(
        marker in normalized
        for marker in ("proveedor", "fecha de factura", "importe total", "referencia de gasto")
    )
    english = sum(
        marker in normalized
        for marker in ("vendor", "invoice date", "total amount", "expense reference")
    )
    if spanish > english and spanish >= 2:
        return "es"
    if english >= 2:
        return "en"
    return "und"


def cluster_signals(text: str, media_type: str) -> dict[str, Any]:
    normalized_lines = [line[2] for line in _lines(text)]
    markers = {
        "vendor": ("vendor:", "proveedor:"),
        "date": ("date:", "invoice date:", "fecha de factura:"),
        "amount": ("amount:", "total amount:", "importe total:"),
        "sourceReference": ("expense reference:", "referencia de gasto:"),
    }
    anchors: list[dict[str, Any]] = []
    for line_number, line in enumerate(normalized_lines, start=1):
        for name, prefixes in markers.items():
            if any(line.startswith(prefix) for prefix in prefixes):
                anchors.append({"field": name, "line": line_number})
                break
    return {
        "artifactMediaType": media_type,
        "languageTag": detect_language(text),
        "normalizedTextTokens": [item["field"] for item in anchors],
        "pageGeometry": {"pageCount": 1, "recognizedAnchorCount": len(anchors)},
        "anchorPositions": [
            {"field": item["field"], "position": index + 1}
            for index, item in enumerate(anchors)
        ],
    }


def cluster_fingerprint(text: str, media_type: str) -> tuple[dict[str, Any], str]:
    signals = cluster_signals(text, media_type)
    return signals, content_hash(
        {
            "algorithm": FINGERPRINT_ALGORITHM,
            "specificationVersion": FINGERPRINT_SPECIFICATION_VERSION,
            "signals": signals,
        }
    )


def evaluate_profile(
    profile: dict[str, Any],
    fixtures: Iterable[dict[str, Any]],
    *,
    ocr_version: str,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    field_checks = 0
    field_passes = 0
    location_checks = 0
    location_passes = 0
    route_checks = 0
    route_passes = 0
    for fixture in fixtures:
        expected_outcome = fixture["expectedOutcome"]
        analysis = analyze_profile(profile, fixture["ocrText"], fixture["mediaType"], require_fields=False)
        recognized = analysis.fingerprint in profile["acceptedFingerprints"]
        actual_outcome = "recognized_profile_draft" if recognized else "needs_profile_review"
        fields: dict[str, str] = {}
        locations: dict[str, str] = {}
        if recognized:
            try:
                complete = analyze_profile(profile, fixture["ocrText"], fixture["mediaType"])
                fields = {item.name: item.value for item in complete.fields}
                locations = {item.name: item.source_location for item in complete.fields}
            except DocumentProfileError:
                actual_outcome = "needs_profile_review"
        route_checks += 1
        route_passes += actual_outcome == expected_outcome
        for name, value in fixture["expectedFields"].items():
            field_checks += 1
            field_passes += fields.get(name) == value
        for name, value in fixture["expectedSourceLocations"].items():
            location_checks += 1
            location_passes += locations.get(name) == value
        passed = (
            actual_outcome == expected_outcome
            and fields == fixture["expectedFields"]
            and locations == fixture["expectedSourceLocations"]
        )
        results.append(
            {
                "fixtureId": fixture["id"],
                "passed": passed,
                "outcome": actual_outcome,
                "fingerprint": analysis.fingerprint,
                "normalizedFieldsHash": content_hash(fields),
                "sourceLocationsHash": content_hash(locations),
            }
        )
    metrics = {
        "supportedFieldExactness": field_passes / field_checks if field_checks else 1.0,
        "sourceLocationExactness": location_passes / location_checks if location_checks else 1.0,
        "unknownSafeRoutingRate": route_passes / route_checks if route_checks else 1.0,
    }
    body = {
        "suiteVersion": EVALUATION_SUITE_VERSION,
        "ocrVersion": ocr_version,
        "parserVersion": PARSER_VERSION,
        "results": results,
        **metrics,
        "passed": all(item["passed"] for item in results) and all(value == 1.0 for value in metrics.values()),
    }
    return {**body, "resultHash": content_hash(body)}
