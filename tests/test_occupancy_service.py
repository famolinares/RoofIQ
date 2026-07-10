import pandas as pd
import pytest

from src.services.occupancy_service import (
    NON_OWNER_OCCUPIED_STATUS,
    OCCUPANCY_CONFIDENCE_COLUMN,
    OCCUPANCY_STATUS_COLUMN,
    OWNER_OCCUPIED_STATUS,
    OccupancyService,
    detect_occupancy_columns,
    normalize_address,
)


def build_row(
    property_address: object,
    mailing_address: object,
) -> pd.DataFrame:
    """Build a single-row dataframe with varied address column names."""
    return pd.DataFrame(
        {
            "Situs Property Address": [property_address],
            "Owner Mailing Street": [mailing_address],
            "Mailing Municipality": ["Miami"],
            "Mailing Province": ["FL"],
            "Mailing Postal Code": ["033101"],
        }
    )


def classify_status(
    property_address: object,
    mailing_address: object,
) -> tuple[str, float]:
    """Classify one address pair and return status plus confidence."""
    result = OccupancyService().classify_dataframe(
        build_row(property_address, mailing_address)
    )
    return (
        result.loc[0, OCCUPANCY_STATUS_COLUMN],
        result.loc[0, OCCUPANCY_CONFIDENCE_COLUMN],
    )


def test_detects_supported_column_variations() -> None:
    data_frame = build_row("123 Main St", "123 Main St")

    columns = detect_occupancy_columns(data_frame)

    assert columns.property_address == "Situs Property Address"
    assert columns.mailing_address == "Owner Mailing Street"
    assert columns.mailing_city == "Mailing Municipality"
    assert columns.mailing_state == "Mailing Province"
    assert columns.mailing_zip == "Mailing Postal Code"


def test_matching_addresses_are_owner_occupied() -> None:
    status, confidence = classify_status("123 Main St", "123 Main St")

    assert status == OWNER_OCCUPIED_STATUS
    assert confidence == 1.0


def test_different_mailing_address_is_non_owner_occupied() -> None:
    status, confidence = classify_status("123 Main St", "999 Other Ave")

    assert status == NON_OWNER_OCCUPIED_STATUS
    assert confidence == 0.9


def test_case_differences_match() -> None:
    status, _ = classify_status("123 main st", "123 MAIN ST")

    assert status == OWNER_OCCUPIED_STATUS


def test_abbreviations_match() -> None:
    status, _ = classify_status("123 Main Street", "123 Main St")

    assert status == OWNER_OCCUPIED_STATUS


def test_spacing_differences_match() -> None:
    status, _ = classify_status("123   Main     St", "123 Main St")

    assert status == OWNER_OCCUPIED_STATUS


def test_punctuation_differences_match() -> None:
    status, _ = classify_status("123 Main St.", "123 Main, St")

    assert status == OWNER_OCCUPIED_STATUS


def test_unit_labels_are_ignored() -> None:
    status, _ = classify_status("123 Main St Apt 2", "123 Main Street #2")

    assert status == OWNER_OCCUPIED_STATUS


def test_missing_values_are_non_owner_occupied_with_zero_confidence() -> None:
    status, confidence = classify_status("123 Main St", "")

    assert status == NON_OWNER_OCCUPIED_STATUS
    assert confidence == 0.0


def test_missing_required_columns_raise_validation_error() -> None:
    data_frame = pd.DataFrame({"Address": ["123 Main St"]})

    with pytest.raises(ValueError, match="mailing address"):
        OccupancyService().classify_dataframe(data_frame)


def test_normalize_address_removes_punctuation_and_units() -> None:
    assert normalize_address("123 Main Street, Apt. 4") == "123 MAIN ST"
