import pytest
from app.services.normalization_service import normalize_merchant


def test_uses_plaid_merchant_name_when_present():
    result = normalize_merchant("AMZN MKTP US*2K3J", "Amazon")
    assert result == "Amazon"


def test_maps_amazon_abbreviation():
    result = normalize_merchant("AMZN MKTP US*2K3J", None)
    assert result == "Amazon"


def test_strips_square_prefix():
    result = normalize_merchant("SQ *BLUE BOTTLE COFFEE", None)
    assert "SQ" not in result
    assert "BLUE BOTTLE" in result.upper() or "Blue Bottle" in result


def test_strips_store_numbers():
    result = normalize_merchant("WALMART #4892", None)
    assert result == "Walmart"


def test_maps_starbucks():
    result = normalize_merchant("STARBUCKS STORE 12345", None)
    assert result == "Starbucks"


def test_maps_netflix():
    result = normalize_merchant("NETFLIX.COM", None)
    assert result == "Netflix"


def test_handles_empty_description():
    result = normalize_merchant("", None)
    assert result == "Unknown"


def test_handles_none_plaid_merchant():
    result = normalize_merchant("CHECKCARD TRADER JOES", None)
    assert "Trader" in result or "trader" in result.lower()


def test_title_cases_unknown_merchants():
    result = normalize_merchant("LOCAL COFFEE SHOP", None)
    assert result[0].isupper()


def test_paypal_prefix_handled():
    result = normalize_merchant("PAYPAL *VENDOR123", None)
    assert "PayPal" in result
