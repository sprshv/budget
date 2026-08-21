import sys
from unittest.mock import MagicMock
sys.modules.setdefault("plaid", MagicMock())
sys.modules.setdefault("plaid.api", MagicMock())
sys.modules.setdefault("plaid.api.plaid_api", MagicMock())
sys.modules.setdefault("plaid.model", MagicMock())
sys.modules.setdefault("plaid.model.link_token_create_request", MagicMock())
sys.modules.setdefault("plaid.configuration", MagicMock())
sys.modules.setdefault("plaid.api_client", MagicMock())

import pytest
from app.services.receipt_service import validate_receipt_file


def test_validate_rejects_non_image():
    with pytest.raises(ValueError, match="not allowed"):
        validate_receipt_file("application/pdf", 100)


def test_validate_rejects_oversized_file():
    with pytest.raises(ValueError, match="exceeds 10 MB"):
        validate_receipt_file("image/jpeg", 11 * 1024 * 1024)


def test_validate_accepts_valid_jpeg():
    validate_receipt_file("image/jpeg", 1024 * 1024)  # 1 MB — should not raise


def test_validate_accepts_valid_png():
    validate_receipt_file("image/png", 5 * 1024 * 1024)  # 5 MB — should not raise


def test_validate_rejects_svg():
    with pytest.raises(ValueError, match="not allowed"):
        validate_receipt_file("image/svg+xml", 100)
