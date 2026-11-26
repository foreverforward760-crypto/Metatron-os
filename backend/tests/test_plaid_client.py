import pytest

from app.plaid_client import PlaidClient


def test_missing_credentials_do_not_silently_use_mock_data(monkeypatch):
    monkeypatch.delenv("PLAID_CLIENT_ID", raising=False)
    monkeypatch.delenv("PLAID_SECRET", raising=False)
    monkeypatch.delenv("METATRON_DEMO_MODE", raising=False)
    client = PlaidClient()
    assert client.demo_mode is False
    assert client._client is None
    with pytest.raises(RuntimeError):
        client.exchange_public_token("public-token-example")


def test_mock_data_requires_explicit_demo_mode(monkeypatch):
    monkeypatch.setenv("METATRON_DEMO_MODE", "true")
    client = PlaidClient()
    token = client.exchange_public_token("public-token-example")
    assert token == "demo_access_token"
    assert "AAPL" in client.get_holdings(token)
    assert client.get_transactions(token)
