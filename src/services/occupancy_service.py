from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd


OWNER_OCCUPIED_STATUS = "LIKELY_OWNER_OCCUPIED"
NON_OWNER_OCCUPIED_STATUS = "LIKELY_NON_OWNER_OCCUPIED"
UNKNOWN_OCCUPANCY_STATUS = "OCCUPANCY_UNKNOWN"
OCCUPANCY_STATUS_COLUMN = "Occupancy Status"
OCCUPANCY_CONFIDENCE_COLUMN = "Occupancy Confidence"

FULL_COMPONENT_MATCH_CONFIDENCE = 0.98
STREET_ZIP_MATCH_CONFIDENCE = 0.92
STREET_CITY_STATE_MATCH_CONFIDENCE = 0.90
STREET_ONLY_MATCH_CONFIDENCE = 0.80
ADDRESS_MISMATCH_CONFIDENCE = 0.95
UNKNOWN_CONFIDENCE = 0.00

EXACT_COLUMN_SCORE = 100
SPECIFIC_COLUMN_SCORE = 80
EXACT_GENERIC_COLUMN_SCORE = 60
GENERIC_COLUMN_SCORE = 40

ADDRESS_ABBREVIATIONS = {
    "ALLEY": "ALY",
    "AVENUE": "AVE",
    "BOULEVARD": "BLVD",
    "CIRCLE": "CIR",
    "COURT": "CT",
    "DRIVE": "DR",
    "HIGHWAY": "HWY",
    "LANE": "LN",
    "PARKWAY": "PKWY",
    "PLACE": "PL",
    "ROAD": "RD",
    "STREET": "ST",
    "TERRACE": "TER",
    "TRAIL": "TRL",
}

UNIT_LABEL_NORMALIZATION = {
    "APT": "UNIT",
    "APARTMENT": "UNIT",
    "BLDG": "BUILDING",
    "BUILDING": "BUILDING",
    "FL": "FLOOR",
    "FLOOR": "FLOOR",
    "LOT": "LOT",
    "SPACE": "SPACE",
    "STE": "UNIT",
    "SUITE": "UNIT",
    "UNIT": "UNIT",
}

PROPERTY_STREET_PATTERNS = (
    ("PROPERTY ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("SITUS ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("SITE ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("PHYSICAL ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("LOCATION ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("ADDRESS", GENERIC_COLUMN_SCORE),
)
PROPERTY_CITY_PATTERNS = (
    ("PROPERTY CITY", SPECIFIC_COLUMN_SCORE),
    ("SITUS CITY", SPECIFIC_COLUMN_SCORE),
    ("SITE CITY", SPECIFIC_COLUMN_SCORE),
    ("PROPERTY MUNICIPALITY", SPECIFIC_COLUMN_SCORE),
    ("CITY", GENERIC_COLUMN_SCORE),
)
PROPERTY_STATE_PATTERNS = (
    ("PROPERTY STATE", SPECIFIC_COLUMN_SCORE),
    ("SITUS STATE", SPECIFIC_COLUMN_SCORE),
    ("SITE STATE", SPECIFIC_COLUMN_SCORE),
    ("STATE", GENERIC_COLUMN_SCORE),
)
PROPERTY_ZIP_PATTERNS = (
    ("PROPERTY ZIP CODE", SPECIFIC_COLUMN_SCORE),
    ("PROPERTY ZIP", SPECIFIC_COLUMN_SCORE),
    ("SITUS ZIP", SPECIFIC_COLUMN_SCORE),
    ("SITE ZIP", SPECIFIC_COLUMN_SCORE),
    ("ZIP CODE", GENERIC_COLUMN_SCORE),
    ("ZIP", GENERIC_COLUMN_SCORE),
)
MAILING_STREET_PATTERNS = (
    ("MAILING ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("MAIL ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("OWNER ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("CO MAILING ADDRESS", SPECIFIC_COLUMN_SCORE),
    ("MAILING STREET", SPECIFIC_COLUMN_SCORE),
)
MAILING_CITY_PATTERNS = (
    ("MAILING CITY", SPECIFIC_COLUMN_SCORE),
    ("MAILING MUNICIPALITY", SPECIFIC_COLUMN_SCORE),
    ("MAIL CITY", SPECIFIC_COLUMN_SCORE),
    ("MAIL MUNICIPALITY", SPECIFIC_COLUMN_SCORE),
    ("OWNER CITY", SPECIFIC_COLUMN_SCORE),
    ("CO MAILING CITY", SPECIFIC_COLUMN_SCORE),
)
MAILING_STATE_PATTERNS = (
    ("MAILING STATE", SPECIFIC_COLUMN_SCORE),
    ("MAILING PROVINCE", SPECIFIC_COLUMN_SCORE),
    ("MAIL STATE", SPECIFIC_COLUMN_SCORE),
    ("MAIL PROVINCE", SPECIFIC_COLUMN_SCORE),
    ("OWNER STATE", SPECIFIC_COLUMN_SCORE),
    ("CO MAILING STATE", SPECIFIC_COLUMN_SCORE),
)
MAILING_ZIP_PATTERNS = (
    ("MAILING ZIP CODE", SPECIFIC_COLUMN_SCORE),
    ("MAILING ZIP", SPECIFIC_COLUMN_SCORE),
    ("MAILING POSTAL CODE", SPECIFIC_COLUMN_SCORE),
    ("MAIL ZIP", SPECIFIC_COLUMN_SCORE),
    ("MAIL POSTAL CODE", SPECIFIC_COLUMN_SCORE),
    ("OWNER ZIP", SPECIFIC_COLUMN_SCORE),
    ("CO MAILING ZIP", SPECIFIC_COLUMN_SCORE),
)


class OccupancyDetectionError(ValueError):
    """Raised when occupancy column detection cannot be completed safely."""


@dataclass(frozen=True)
class OccupancyColumns:
    """Detected spreadsheet columns used by the occupancy engine."""

    property_street: str
    mailing_street: str
    property_city: str | None = None
    property_state: str | None = None
    property_zip: str | None = None
    mailing_city: str | None = None
    mailing_state: str | None = None
    mailing_zip: str | None = None


@dataclass(frozen=True)
class OccupancyClassification:
    """Rule-based occupancy classification for one property row."""

    status: str
    confidence: float


@dataclass(frozen=True)
class AddressComponents:
    """Normalized address components available for comparison."""

    street: str
    city: str = ""
    state: str = ""
    zip_code: str = ""


class OccupancyService:
    """Detect likely owner occupancy by comparing situs and mailing addresses."""

    def classify_dataframe(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of imported data with occupancy status and confidence."""
        classified_data = data_frame.copy()
        try:
            columns = detect_occupancy_columns(data_frame)
        except OccupancyDetectionError:
            classified_data[OCCUPANCY_STATUS_COLUMN] = UNKNOWN_OCCUPANCY_STATUS
            classified_data[OCCUPANCY_CONFIDENCE_COLUMN] = UNKNOWN_CONFIDENCE
            return classified_data

        classifications = classified_data.apply(
            lambda row: classify_occupancy(row, columns),
            axis=1,
        )
        classified_data[OCCUPANCY_STATUS_COLUMN] = [
            classification.status for classification in classifications
        ]
        classified_data[OCCUPANCY_CONFIDENCE_COLUMN] = [
            classification.confidence for classification in classifications
        ]
        return classified_data


def detect_occupancy_columns(data_frame: pd.DataFrame) -> OccupancyColumns:
    """Detect the address columns required for owner occupancy classification."""
    columns = list(data_frame.columns)
    mailing_street = find_required_column(columns, MAILING_STREET_PATTERNS)
    return OccupancyColumns(
        property_street=find_required_column(
            columns,
            PROPERTY_STREET_PATTERNS,
            excluded_columns={mailing_street},
            disallowed_terms=("MAIL", "MAILING"),
        ),
        mailing_street=mailing_street,
        property_city=find_optional_column(
            columns,
            PROPERTY_CITY_PATTERNS,
            disallowed_terms=("MAIL", "MAILING", "OWNER"),
        ),
        property_state=find_optional_column(
            columns,
            PROPERTY_STATE_PATTERNS,
            disallowed_terms=("MAIL", "MAILING", "OWNER"),
        ),
        property_zip=find_optional_column(
            columns,
            PROPERTY_ZIP_PATTERNS,
            disallowed_terms=("MAIL", "MAILING", "OWNER"),
        ),
        mailing_city=find_optional_column(columns, MAILING_CITY_PATTERNS),
        mailing_state=find_optional_column(columns, MAILING_STATE_PATTERNS),
        mailing_zip=find_optional_column(columns, MAILING_ZIP_PATTERNS),
    )


def classify_occupancy(
    row: pd.Series,
    columns: OccupancyColumns,
) -> OccupancyClassification:
    """Classify one property as likely owner occupied or not owner occupied."""
    property_address = build_address_components(
        row=row,
        street_column=columns.property_street,
        city_column=columns.property_city,
        state_column=columns.property_state,
        zip_column=columns.property_zip,
    )
    mailing_address = build_address_components(
        row=row,
        street_column=columns.mailing_street,
        city_column=columns.mailing_city,
        state_column=columns.mailing_state,
        zip_column=columns.mailing_zip,
    )

    if not property_address.street or not mailing_address.street:
        return unknown_classification()

    if property_address.street != mailing_address.street:
        return non_owner_classification()

    compared_components = compare_optional_components(property_address, mailing_address)
    if any(not components_match for components_match in compared_components.values()):
        return non_owner_classification()

    return owner_classification(compared_components)


def build_address_components(
    row: pd.Series,
    street_column: str,
    city_column: str | None,
    state_column: str | None,
    zip_column: str | None,
) -> AddressComponents:
    """Build normalized address components from a dataframe row."""
    return AddressComponents(
        street=normalize_street_address(row.get(street_column, "")),
        city=normalize_place_value(row.get(city_column, "")) if city_column else "",
        state=normalize_place_value(row.get(state_column, "")) if state_column else "",
        zip_code=normalize_zip_code(row.get(zip_column, "")) if zip_column else "",
    )


def owner_classification(compared_components: dict[str, bool]) -> OccupancyClassification:
    """Return an owner-occupied classification with component-based confidence."""
    if all(component in compared_components for component in ("city", "state", "zip")):
        return OccupancyClassification(
            status=OWNER_OCCUPIED_STATUS,
            confidence=FULL_COMPONENT_MATCH_CONFIDENCE,
        )
    if "zip" in compared_components:
        return OccupancyClassification(
            status=OWNER_OCCUPIED_STATUS,
            confidence=STREET_ZIP_MATCH_CONFIDENCE,
        )
    if all(component in compared_components for component in ("city", "state")):
        return OccupancyClassification(
            status=OWNER_OCCUPIED_STATUS,
            confidence=STREET_CITY_STATE_MATCH_CONFIDENCE,
        )
    return OccupancyClassification(
        status=OWNER_OCCUPIED_STATUS,
        confidence=STREET_ONLY_MATCH_CONFIDENCE,
    )


def non_owner_classification() -> OccupancyClassification:
    """Return a likely non-owner-occupied classification."""
    return OccupancyClassification(
        status=NON_OWNER_OCCUPIED_STATUS,
        confidence=ADDRESS_MISMATCH_CONFIDENCE,
    )


def unknown_classification() -> OccupancyClassification:
    """Return an unknown occupancy classification."""
    return OccupancyClassification(
        status=UNKNOWN_OCCUPANCY_STATUS,
        confidence=UNKNOWN_CONFIDENCE,
    )


def compare_optional_components(
    property_address: AddressComponents,
    mailing_address: AddressComponents,
) -> dict[str, bool]:
    """Compare optional city, state, and ZIP components when both sides exist."""
    comparisons: dict[str, bool] = {}
    if property_address.city and mailing_address.city:
        comparisons["city"] = property_address.city == mailing_address.city
    if property_address.state and mailing_address.state:
        comparisons["state"] = property_address.state == mailing_address.state
    if property_address.zip_code and mailing_address.zip_code:
        comparisons["zip"] = property_address.zip_code == mailing_address.zip_code
    return comparisons


def normalize_street_address(value: object) -> str:
    """Normalize street address text while preserving unit identifiers."""
    if is_missing(value):
        return ""

    address = str(value).upper().replace("#", " UNIT ")
    address = re.sub(r"[#,/\.\-]", " ", address)
    address = re.sub(r"[^A-Z0-9\s]", " ", address)
    tokens = [normalize_street_token(token) for token in address.split()]
    return " ".join(tokens)


def normalize_street_token(token: str) -> str:
    """Normalize one street-address token."""
    if token in UNIT_LABEL_NORMALIZATION:
        return UNIT_LABEL_NORMALIZATION[token]
    return ADDRESS_ABBREVIATIONS.get(token, token)


def normalize_place_value(value: object) -> str:
    """Normalize city or state text for deterministic comparison."""
    if is_missing(value):
        return ""
    normalized = re.sub(r"[^A-Z0-9\s]", " ", str(value).upper())
    return " ".join(normalized.split())


def normalize_zip_code(value: object) -> str:
    """Normalize a ZIP or postal code while preserving leading zeros."""
    if is_missing(value):
        return ""
    zip_code = str(value).strip().upper()
    if zip_code.endswith(".0"):
        zip_code = zip_code[:-2]
    return re.sub(r"[^A-Z0-9]", "", zip_code)


def find_required_column(
    columns: list[str],
    patterns: tuple[tuple[str, int], ...],
    excluded_columns: set[str] | None = None,
    disallowed_terms: tuple[str, ...] = (),
) -> str:
    """Find a required column or raise a controlled detection error."""
    column = find_best_column(columns, patterns, excluded_columns, disallowed_terms)
    if column is None:
        raise OccupancyDetectionError(
            f"Could not confidently detect required column for {patterns[0][0].lower()}."
        )
    return column


def find_optional_column(
    columns: list[str],
    patterns: tuple[tuple[str, int], ...],
    excluded_columns: set[str] | None = None,
    disallowed_terms: tuple[str, ...] = (),
) -> str | None:
    """Find an optional column without guessing when matches are ambiguous."""
    return find_best_column(columns, patterns, excluded_columns, disallowed_terms)


def find_best_column(
    columns: list[str],
    patterns: tuple[tuple[str, int], ...],
    excluded_columns: set[str] | None = None,
    disallowed_terms: tuple[str, ...] = (),
) -> str | None:
    """Find the highest-ranked deterministic column match."""
    excluded_columns = excluded_columns or set()
    candidates: list[tuple[int, str]] = []
    for column in columns:
        normalized_column = normalize_column_name(column)
        if column in excluded_columns:
            continue
        if any(term in normalized_column.split() for term in disallowed_terms):
            continue
        score = score_column(normalized_column, patterns)
        if score > 0:
            candidates.append((score, column))

    if not candidates:
        return None

    candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))
    best_score = candidates[0][0]
    best_candidates = [
        column for score, column in candidates if score == best_score
    ]
    if len(best_candidates) > 1:
        raise OccupancyDetectionError(
            f"Ambiguous column detection for {patterns[0][0].lower()}: "
            f"{', '.join(best_candidates)}."
        )
    return best_candidates[0]


def score_column(
    normalized_column: str,
    patterns: tuple[tuple[str, int], ...],
) -> int:
    """Score a normalized column name against ranked patterns."""
    for pattern, score in patterns:
        if normalized_column == pattern:
            if score == GENERIC_COLUMN_SCORE:
                return EXACT_GENERIC_COLUMN_SCORE
            return EXACT_COLUMN_SCORE
        if pattern in normalized_column:
            return score
    return 0


def normalize_column_name(column: str) -> str:
    """Normalize a column name for deterministic keyword matching."""
    normalized = re.sub(r"[^A-Z0-9]+", " ", str(column).upper())
    return " ".join(normalized.split())


def is_missing(value: object) -> bool:
    """Return whether a spreadsheet cell value is missing or unusable."""
    if value is None or pd.isna(value):
        return True
    return str(value).strip() == ""


normalize_address = normalize_street_address
