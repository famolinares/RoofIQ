import pandas as pd
import pytest

from src.services.occupancy_service import (
    ADDRESS_MISMATCH_CONFIDENCE,
    FULL_COMPONENT_MATCH_CONFIDENCE,
    NON_OWNER_OCCUPIED_STATUS,
    OCCUPANCY_CONFIDENCE_COLUMN,
    OCCUPANCY_STATUS_COLUMN,
    OWNER_OCCUPIED_STATUS,
    STREET_ONLY_MATCH_CONFIDENCE,
    STREET_ZIP_MATCH_CONFIDENCE,
    UNKNOWN_CONFIDENCE,
    UNKNOWN_OCCUPANCY_STATUS,
    OccupancyDetectionError,
    OccupancyService,
    detect_occupancy_columns,
    normalize_address,
)


def build_component_row(
    property_street: object,
    mailing_street: object,
    property_city: object = "Miami",
    mailing_city: object = "Miami",
    property_state: object = "FL",
    mailing_state: object = "FL",
    property_zip: object = "033101",
    mailing_zip: object = "033101",
) -> pd.DataFrame:
    """Build a dataframe with separate property and mailing components."""
    return pd.DataFrame(
        {
            "Situs Property Address": [property_street],
            "Property City": [property_city],
            "Property State": [property_state],
            "Property Zip": [property_zip],
            "Owner Mailing Street": [mailing_street],
            "Mailing City": [mailing_city],
            "Mailing State": [mailing_state],
            "Mailing Zip": [mailing_zip],
        }
    )


def classify(data_frame: pd.DataFrame) -> tuple[str, float]:
    """Classify the first row and return status plus confidence."""
    result = OccupancyService().classify_dataframe(data_frame)
    return (
        result.loc[0, OCCUPANCY_STATUS_COLUMN],
        result.loc[0, OCCUPANCY_CONFIDENCE_COLUMN],
    )


def test_matching_addresses_are_owner_occupied() -> None:
    status, confidence = classify(
        build_component_row("123 Main St", "123 Main St")
    )

    assert status == OWNER_OCCUPIED_STATUS
    assert confidence == FULL_COMPONENT_MATCH_CONFIDENCE


def test_different_mailing_address_is_non_owner_occupied() -> None:
    status, confidence = classify(
        build_component_row("123 Main St", "999 Other Ave")
    )

    assert status == NON_OWNER_OCCUPIED_STATUS
    assert confidence == ADDRESS_MISMATCH_CONFIDENCE


def test_case_differences_match() -> None:
    status, _ = classify(build_component_row("123 main st", "123 MAIN ST"))

    assert status == OWNER_OCCUPIED_STATUS


def test_abbreviations_match() -> None:
    status, _ = classify(build_component_row("123 Main Street", "123 Main St"))

    assert status == OWNER_OCCUPIED_STATUS


def test_spacing_differences_match() -> None:
    status, _ = classify(build_component_row("123   Main     St", "123 Main St"))

    assert status == OWNER_OCCUPIED_STATUS


def test_punctuation_differences_match() -> None:
    status, _ = classify(build_component_row("123 Main St.", "123 Main, St"))

    assert status == OWNER_OCCUPIED_STATUS


def test_different_unit_numbers_do_not_match() -> None:
    status, confidence = classify(
        build_component_row("123 Main St Unit 1", "123 Main St Unit 2")
    )

    assert status == NON_OWNER_OCCUPIED_STATUS
    assert confidence == ADDRESS_MISMATCH_CONFIDENCE


def test_different_unit_letters_do_not_match() -> None:
    status, _ = classify(
        build_component_row("123 Main St Apt A", "123 Main St Apt B")
    )

    assert status == NON_OWNER_OCCUPIED_STATUS


def test_different_lot_numbers_do_not_match() -> None:
    status, _ = classify(
        build_component_row("123 Main St Lot 4", "123 Main St Lot 9")
    )

    assert status == NON_OWNER_OCCUPIED_STATUS


def test_equivalent_unit_labels_match() -> None:
    examples = [
        ("123 Main St #4", "123 Main St Unit 4"),
        ("123 Main St Apt 4", "123 Main St Apartment 4"),
        ("123 Main St Ste 200", "123 Main St Suite 200"),
    ]

    for property_street, mailing_street in examples:
        status, _ = classify(build_component_row(property_street, mailing_street))
        assert status == OWNER_OCCUPIED_STATUS


def test_missing_property_address_produces_unknown() -> None:
    status, confidence = classify(build_component_row("", "123 Main St"))

    assert status == UNKNOWN_OCCUPANCY_STATUS
    assert confidence == UNKNOWN_CONFIDENCE


def test_missing_mailing_address_produces_unknown() -> None:
    status, confidence = classify(build_component_row("123 Main St", ""))

    assert status == UNKNOWN_OCCUPANCY_STATUS
    assert confidence == UNKNOWN_CONFIDENCE


def test_street_only_match_produces_reduced_confidence() -> None:
    data_frame = pd.DataFrame(
        {
            "Situs Property Address": ["123 Main St"],
            "Owner Mailing Street": ["123 Main Street"],
        }
    )

    status, confidence = classify(data_frame)

    assert status == OWNER_OCCUPIED_STATUS
    assert confidence == STREET_ONLY_MATCH_CONFIDENCE


def test_full_street_city_state_zip_match_produces_high_confidence() -> None:
    status, confidence = classify(
        build_component_row("123 Main Street", "123 Main St")
    )

    assert status == OWNER_OCCUPIED_STATUS
    assert confidence == FULL_COMPONENT_MATCH_CONFIDENCE


def test_street_and_zip_match_without_other_components_uses_zip_confidence() -> None:
    data_frame = pd.DataFrame(
        {
            "Situs Property Address": ["123 Main St"],
            "Property Zip": ["033101"],
            "Owner Mailing Street": ["123 Main Street"],
            "Mailing Zip": ["033101"],
        }
    )

    status, confidence = classify(data_frame)

    assert status == OWNER_OCCUPIED_STATUS
    assert confidence == STREET_ZIP_MATCH_CONFIDENCE


def test_zip_mismatch_prevents_owner_occupied_classification() -> None:
    status, confidence = classify(
        build_component_row(
            "123 Main St",
            "123 Main St",
            property_zip="033101",
            mailing_zip="033102",
        )
    )

    assert status == NON_OWNER_OCCUPIED_STATUS
    assert confidence == ADDRESS_MISMATCH_CONFIDENCE


def test_ambiguous_address_columns_do_not_produce_silent_guess() -> None:
    data_frame = pd.DataFrame(
        {
            "Property Address": ["123 Main St"],
            "Situs Address": ["123 Main St"],
            "Mailing Address": ["123 Main St"],
        }
    )

    with pytest.raises(OccupancyDetectionError, match="Ambiguous"):
        detect_occupancy_columns(data_frame)

    status, confidence = classify(data_frame)
    assert status == UNKNOWN_OCCUPANCY_STATUS
    assert confidence == UNKNOWN_CONFIDENCE


def test_optional_missing_city_state_zip_columns() -> None:
    data_frame = pd.DataFrame(
        {
            "Situs Property Address": ["123 Main St"],
            "Owner Mailing Street": ["123 Main St"],
        }
    )

    status, confidence = classify(data_frame)

    assert status == OWNER_OCCUPIED_STATUS
    assert confidence == STREET_ONLY_MATCH_CONFIDENCE


def test_miami_dade_style_column_names() -> None:
    data_frame = pd.DataFrame(
        {
            "Address": ["123 Main Street"],
            "Zip_Code": ["033101"],
            "CO_Property City": ["Miami"],
            "CO_Mailing Address": ["123 Main St"],
            "CO_Mailing City": ["Miami"],
            "CO_Mailing State": ["FL"],
            "CO_Mailing Zip": ["033101"],
        }
    )

    status, confidence = classify(data_frame)
    columns = detect_occupancy_columns(data_frame)

    assert status == OWNER_OCCUPIED_STATUS
    assert confidence == STREET_ZIP_MATCH_CONFIDENCE
    assert columns.property_street == "Address"
    assert columns.property_city == "CO_Property City"
    assert columns.property_zip == "Zip_Code"
    assert columns.mailing_street == "CO_Mailing Address"


def test_missing_required_columns_return_unknown_for_dataframe() -> None:
    data_frame = pd.DataFrame({"Owner": ["Example"]})

    status, confidence = classify(data_frame)

    assert status == UNKNOWN_OCCUPANCY_STATUS
    assert confidence == UNKNOWN_CONFIDENCE


def test_normalize_address_preserves_unit_identifiers() -> None:
    assert normalize_address("123 Main Street, Apt. 4") == "123 MAIN ST UNIT 4"
