import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import AnalyzeRequest, LinkResponse


def test_plaid_access_token_is_not_exposed_in_api_models():
    assert "access_token" not in LinkResponse.model_fields
    assert "access_token" not in AnalyzeRequest.model_fields
