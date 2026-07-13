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
FINGERPRINT_SPECIFICATION_ID = "document-layout-signals"
FINGERPRINT_SPECIFICATION_VERSION = "document-layout-signals-v1"
FINGERPRINT_SIGNALS = (
    "artifact_media_type",
    "language_tag",
    "normalized_text_tokens",
    "page_geometry",
    "anchor_positions",
)
PARSER_VERSION = "deterministic-document-profile-parser-v1"
EVALUATION_SUITE_VERSION = "document-profile-fixtures-v1"
SUPPORTED_NORMALIZATIONS = {
    "trim": {"string", "reference"},
    "casefold": {"string", "reference"},
    "iso_date": {"date"},
    "decimal": {"decimal"},
    "identifier": {"identifier"},
}
SUPPORTED_FIXTURE_KINDS = frozenset(
    {"supported_layout", "changed_layout", "unknown_layout"}
)


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


def profile_content_hash(profile: dict[str, Any]) -> str:
    body = {
        key: value
        for key, value in profile.items()
        if key not in {"lifecycle", "evaluationEvidence", "contentHash"}
    }
    for optional_reference in ("predecessor", "successor"):
        if body.get(optional_reference) is None:
            body.pop(optional_reference, None)
    return content_hash(body)


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


def _generic_line_token(raw: str, normalized: str) -> str:
    """Describe line shape without persisting customer-specific values."""
    if ":" in normalized:
        return f"label:{normalized.split(':', 1)[0].strip()}"
    if raw.isupper() and any(character.isalpha() for character in raw):
        return f"heading:{normalized}"
    return "text"


def _profile_line_token(
    raw: str,
    normalized: str,
    profile: dict[str, Any],
) -> str:
    if normalized in {normalize_token(item) for item in profile["vendorAliases"]}:
        return "field:vendor:vendor_alias"
    for field in profile["requiredFields"]:
        candidate = _label_value(raw, normalized, field["sourceLabels"])
        if candidate is not None:
            return f"field:{field['name']}:{normalize_token(candidate[0])}"
    return _generic_line_token(raw, normalized)


def validate_profile_definition(profile: dict[str, Any]) -> None:
    expected_specification = {
        "id": FINGERPRINT_SPECIFICATION_ID,
        "version": FINGERPRINT_SPECIFICATION_VERSION,
        "algorithm": FINGERPRINT_ALGORITHM,
        "signals": list(FINGERPRINT_SIGNALS),
    }
    if profile.get("fingerprintSpecification") != expected_specification:
        raise DocumentProfileError(
            "The document profile must use the supported executable fingerprint specification"
        )
    if not isinstance(profile.get("artifactClass"), str) or not profile["artifactClass"].strip():
        raise DocumentProfileError("artifactClass is required")
    if not isinstance(profile.get("languageTag"), str) or not profile["languageTag"].strip():
        raise DocumentProfileError("A BCP 47 languageTag is required")
    aliases = profile.get("vendorAliases")
    if (
        not isinstance(aliases, list)
        or not aliases
        or any(not isinstance(item, str) or not item.strip() for item in aliases)
        or len({normalize_token(item) for item in aliases}) != len(aliases)
    ):
        raise DocumentProfileError("Unique non-empty vendorAliases are required")
    fields = profile.get("requiredFields")
    if not isinstance(fields, list) or not fields:
        raise DocumentProfileError("At least one document profile field is required")
    names = [field.get("name") for field in fields if isinstance(field, dict)]
    if len(names) != len(fields) or any(not isinstance(name, str) or not name for name in names):
        raise DocumentProfileError("Every document profile field needs a name")
    if len(set(names)) != len(names):
        raise DocumentProfileError("Document profile field names must be unique")
    for field in fields:
        operation = field.get("normalization")
        field_type = field.get("fieldType")
        if operation not in SUPPORTED_NORMALIZATIONS:
            raise DocumentProfileError(f"Unsupported normalization operation: {operation}")
        if field_type not in SUPPORTED_NORMALIZATIONS[operation]:
            raise DocumentProfileError(
                f"Normalization {operation} is incompatible with field type {field_type}"
            )
        labels = field.get("sourceLabels")
        if (
            not isinstance(labels, list)
            or not labels
            or any(not isinstance(item, str) or not item.strip() for item in labels)
        ):
            raise DocumentProfileError(f"Source labels are required for field {field['name']}")
    rule = profile.get("ledgerMatchRule")
    if not isinstance(rule, dict) or not isinstance(rule.get("required"), bool):
        raise DocumentProfileError("A deterministic ledgerMatchRule is required")
    for key in ("sourceReferenceField", "amountField", "dateField", "vendorField"):
        if rule.get(key) not in names:
            raise DocumentProfileError(f"ledgerMatchRule {key} must reference a profile field")


def validate_fixture_suite(profile: dict[str, Any], fixtures: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = list(fixtures)
    if not cases:
        raise DocumentProfileError("A versioned fixture set is required")
    ids = [case.get("id") for case in cases]
    if any(not isinstance(identifier, str) or not identifier for identifier in ids):
        raise DocumentProfileError("Every profile fixture needs an id")
    if len(set(ids)) != len(ids):
        raise DocumentProfileError("Profile fixture ids must be unique")
    kinds = [case.get("caseKind") for case in cases]
    if any(kind not in SUPPORTED_FIXTURE_KINDS for kind in kinds):
        raise DocumentProfileError("Profile fixture caseKind is unsupported")
    supported = [case for case in cases if case["caseKind"] == "supported_layout"]
    changed = [case for case in cases if case["caseKind"] == "changed_layout"]
    unknown = [case for case in cases if case["caseKind"] == "unknown_layout"]
    if len(supported) < 2 or not changed or not unknown:
        raise DocumentProfileError(
            "Fixture evaluation requires two supported layouts plus changed and unknown cases"
        )
    required_names = {
        field["name"] for field in profile["requiredFields"] if field["required"]
    }
    for case in cases:
        if not isinstance(case.get("ocrText"), str) or not case["ocrText"].strip():
            raise DocumentProfileError("Profile fixture OCR text is required")
        if not isinstance(case.get("mediaType"), str) or not case["mediaType"].strip():
            raise DocumentProfileError("Profile fixture media type is required")
        fields = case.get("expectedFields")
        locations = case.get("expectedSourceLocations")
        if not isinstance(fields, dict) or not isinstance(locations, dict):
            raise DocumentProfileError("Profile fixture expectations must be mappings")
        if case["caseKind"] == "supported_layout":
            if case.get("expectedOutcome") != "recognized_profile_draft":
                raise DocumentProfileError("Supported fixtures must expect a recognized draft")
            if set(fields) != required_names or set(locations) != required_names:
                raise DocumentProfileError(
                    "Supported fixtures must cover every required field and source location"
                )
            analyze_profile(profile, case["ocrText"], case["mediaType"])
        elif (
            case.get("expectedOutcome") != "needs_profile_review"
            or fields
            or locations
        ):
            raise DocumentProfileError(
                "Changed and unknown fixtures must expect safe routing with no fields"
            )
    return cases


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
    validate_profile_definition(profile)
    lines = _lines(text)
    normalized_positions = {
        raw_line_number: position
        for position, (raw_line_number, _, _) in enumerate(lines, start=1)
    }
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
        anchors.append(
            {
                "field": field["name"],
                "position": normalized_positions[number],
                "label": normalize_token(label),
            }
        )

    ordered = sorted(anchors, key=lambda item: item["position"])
    normalized_anchors = [
        {
            "field": item["field"],
            "position": item["position"],
            "label": item["label"],
        }
        for item in ordered
    ]
    signals = {
        "artifactMediaType": media_type,
        "languageTag": profile["languageTag"],
        "normalizedTextTokens": [
            _profile_line_token(raw, normalized, profile)
            for _, raw, normalized in lines
        ],
        "pageGeometry": {
            "pageCount": 1,
            "nonEmptyLineCount": len(lines),
            "recognizedAnchorCount": len(ordered),
        },
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
    lines = _lines(text)
    markers = {
        "vendor": ("vendor:", "proveedor:"),
        "date": ("date:", "invoice date:", "fecha de factura:"),
        "amount": ("amount:", "total amount:", "importe total:"),
        "sourceReference": ("expense reference:", "referencia de gasto:"),
    }
    anchors: list[dict[str, Any]] = []
    for position, (_, _, line) in enumerate(lines, start=1):
        for name, prefixes in markers.items():
            if any(line.startswith(prefix) for prefix in prefixes):
                anchors.append({"field": name, "position": position})
                break
    return {
        "artifactMediaType": media_type,
        "languageTag": detect_language(text),
        "normalizedTextTokens": [
            _generic_line_token(raw, normalized) for _, raw, normalized in lines
        ],
        "pageGeometry": {
            "pageCount": 1,
            "nonEmptyLineCount": len(lines),
            "recognizedAnchorCount": len(anchors),
        },
        "anchorPositions": anchors,
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
    validate_profile_definition(profile)
    fixtures = validate_fixture_suite(profile, fixtures)
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
        if fixture["caseKind"] == "supported_layout":
            for name, value in fixture["expectedFields"].items():
                field_checks += 1
                field_passes += fields.get(name) == value
            for name, value in fixture["expectedSourceLocations"].items():
                location_checks += 1
                location_passes += locations.get(name) == value
        else:
            route_checks += 1
            route_passes += actual_outcome == expected_outcome
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


def ledger_expense_key(profile: dict[str, Any], fields: dict[str, str]) -> str | None:
    rule = profile["ledgerMatchRule"]
    reference = fields.get(rule["sourceReferenceField"], "").strip()
    if not reference:
        return None
    return reference.removeprefix("VENDOR-INVOICE-")


def ledger_values_match(
    profile: dict[str, Any],
    fields: dict[str, str],
    *,
    expense_date: str,
    vendor: str,
    amount: str,
) -> bool:
    rule = profile["ledgerMatchRule"]
    expected = {
        rule["dateField"]: expense_date,
        rule["vendorField"]: normalize_token(vendor),
        rule["amountField"]: str(Decimal(amount).quantize(Decimal("0.01"))),
    }
    actual = {
        rule["dateField"]: fields.get(rule["dateField"]),
        rule["vendorField"]: normalize_token(fields.get(rule["vendorField"], "")),
        rule["amountField"]: fields.get(rule["amountField"]),
    }
    return actual == expected
