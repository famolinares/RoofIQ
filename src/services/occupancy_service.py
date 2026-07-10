from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd


OWNER_OCCUPIED_STATUS = "LIKELY_OWNER_OCCUPIED"
NON_OWNER_OCCUPIED_STATUS = "LIKELY_NON_OWNER_OCCUPIED"
OCCUPANCY_STATUS_COLUMN = "Occupancy Status"
OCCUPANCY_CONFIDENCE_COLUMN = "Occupancy Confidence"
OWNER_OCCUPIED_CONFIDENCE = 1.0
NON_OWNER_OCCUPIED_CONFIDENCE = 0.9
MISSING_ADDRESS_CONFIDENCE = 0.0

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

UNIT_LABELS = {
    "APT",
    "APARTMENT",
    "BLDG",
    "BUILDING",
    "FL",
    "FLOOR",
    "LOT",
    "ROOM",
    "RM",
    "SPACE",
    "STE",
    "SUITE",
    "UNIT",
}

PROPERTY_ADDRESS_KEYWORDS = (
    "PROPERTY ADDRESS",
    "SITUS ADDRESS",
    "SITE ADDRESS",
    "PHYSICAL ADDRESS",
    "LOCATION ADDRESS",
    "ADDRESS",
)
MAILING_ADDRESS_KEYWORDS = (
    "MAILING ADDRESS",
    "MAIL ADDRESS",
    "OWNER ADDRESS",
    "CO MAILING ADDRESS",
    "MAILING STREET",
)
MAILING_CITY_KEYWORDS = (
    "MAILING CITY",
    "MAILING MUNICIPALITY",
    "MAIL CITY",
    "MAIL MUNICIPALITY",
    "OWNER CITY",
    "CO MAILING CITY",
)
MAILING_STATE_KEYWORDS = (
    "MAILING STATE",
    "MAILING PROVINCE",
    "MAIL STATE",
    "MAIL PROVINCE",
    "OWNER STATE",
    "CO MAILING STATE",
)
MAILING_ZIP_KEYWORDS = (
    "MAILING ZIP",
    "MAILING ZIP CODE",
    "MAILING POSTAL CODE",
    "MAIL ZIP",
    "MAIL POSTAL CODE",
    "OWNER ZIP",
    "CO MAILING ZIP",
)


@dataclass(frozen=True)
class OccupancyColumns:
    """Detected spreadsheet columns used by the occupancy engine."""

    property_address: str
    mailing_address: str
    mailing_city: str
    mailing_state: str
    mailing_zip: str


@dataclass(frozen=True)
class OccupancyClassification:
    """Rule-based occupancy classification for one property row."""

    status: str
    confidence: float


class OccupancyService:
    """Detect likely owner occupancy by comparing situs and mailing addresses."""

    def classify_dataframe(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of imported data with occupancy status and confidence."""
        columns = detect_occupancy_columns(data_frame)
        classified_data = data_frame.copy()
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
    mailing_address = find_column(columns, MAILING_ADDRESS_KEYWORDS)
    return OccupancyColumns(
        property_address=find_property_address_column(columns, mailing_address),
        mailing_address=mailing_address,
        mailing_city=find_column(columns, MAILING_CITY_KEYWORDS),
        mailing_state=find_column(columns, MAILING_STATE_KEYWORDS),
        mailing_zip=find_column(columns, MAILING_ZIP_KEYWORDS),
    )


def classify_occupancy(
    row: pd.Series,
    columns: OccupancyColumns,
) -> OccupancyClassification:
    """Classify one property as likely owner occupied or not owner occupied."""
    property_address = normalize_address(row.get(columns.property_address, ""))
    mailing_address = normalize_address(row.get(columns.mailing_address, ""))

    if not property_address or not mailing_address:
        return OccupancyClassification(
            status=NON_OWNER_OCCUPIED_STATUS,
            confidence=MISSING_ADDRESS_CONFIDENCE,
        )

    if property_address == mailing_address:
        return OccupancyClassification(
            status=OWNER_OCCUPIED_STATUS,
            confidence=OWNER_OCCUPIED_CONFIDENCE,
        )

    return OccupancyClassification(
        status=NON_OWNER_OCCUPIED_STATUS,
        confidence=NON_OWNER_OCCUPIED_CONFIDENCE,
    )


def normalize_address(value: object) -> str:
    """Normalize an address for deterministic rule-based comparison."""
    if value is None or pd.isna(value):
        return ""

    address = str(value).upper()
    address = address.replace("#", " UNIT ")
    address = re.sub(r"[#,/\.\-]", " ", address)
    address = re.sub(r"[^A-Z0-9\s]", " ", address)
    tokens = [ADDRESS_ABBREVIATIONS.get(token, token) for token in address.split()]
    return " ".join(remove_unit_tokens(tokens))


def find_property_address_column(columns: list[str], mailing_address_column: str) -> str:
    """Find the property address column while excluding mailing address columns."""
    property_candidates = [
        column
        for column in columns
        if column != mailing_address_column
        and "MAIL" not in normalize_column_name(column)
        and column_matches(column, PROPERTY_ADDRESS_KEYWORDS)
    ]
    if property_candidates:
        return property_candidates[0]

    raise ValueError("Could not detect a property address column.")


def find_column(columns: list[str], keywords: tuple[str, ...]) -> str:
    """Find the best spreadsheet column matching one of the provided keywords."""
    for keyword in keywords:
        for column in columns:
            if keyword in normalize_column_name(column):
                return column
    raise ValueError(f"Could not detect required column for {keywords[0].lower()}.")


def column_matches(column: str, keywords: tuple[str, ...]) -> bool:
    """Return whether a column name matches any supported keyword variation."""
    normalized_column = normalize_column_name(column)
    return any(keyword in normalized_column for keyword in keywords)


def normalize_column_name(column: str) -> str:
    """Normalize a column name for fuzzy keyword matching."""
    normalized = re.sub(r"[^A-Z0-9]+", " ", str(column).upper())
    return " ".join(normalized.split())


def remove_unit_tokens(tokens: list[str]) -> list[str]:
    """Remove apartment, suite, and unit suffixes from normalized address tokens."""
    cleaned_tokens: list[str] = []
    for token in tokens:
        if token in UNIT_LABELS:
            break
        cleaned_tokens.append(token)
    return cleaned_tokens
