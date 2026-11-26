"""
Plaid integration prototype.

Mock account data is disabled unless METATRON_DEMO_MODE=true is explicitly set.
Live use requires plaid-python and PLAID_CLIENT_ID / PLAID_SECRET / PLAID_ENV.
The current holdings parser still supplies placeholder market indicators.
"""

import os
from typing import Dict, Any, Optional


class PlaidClient:
    """Thin wrapper around the Plaid API for brokerage account access."""

    def __init__(self) -> None:
        self.client_id = os.getenv("PLAID_CLIENT_ID", "")
        self.secret = os.getenv("PLAID_SECRET", "")
        self.env = os.getenv("PLAID_ENV", "sandbox").strip().lower()
        self.demo_mode = os.getenv("METATRON_DEMO_MODE", "").strip().lower() in {"1", "true", "yes"}
        self._client = self._init_client()

    def _init_client(self) -> Optional[Any]:
        if self.demo_mode or not self.client_id or not self.secret:
            return None
        try:
            import plaid
            from plaid.api import plaid_api
            from plaid.model.products import Products
            from plaid.model.country_code import CountryCode
            environments = {
                "sandbox": plaid.Environment.Sandbox,
                "development": plaid.Environment.Development,
                "production": plaid.Environment.Production,
            }
            if self.env not in environments:
                raise ValueError("PLAID_ENV must be sandbox, development, or production")
            configuration = plaid.Configuration(
                host=environments[self.env],
                api_key={
                    "clientId": self.client_id,
                    "secret": self.secret,
                },
            )
            api_client = plaid.ApiClient(configuration)
            return plaid_api.PlaidApi(api_client)
        except ImportError:
            # plaid-python not installed – fall back to mock
            return None

    @property
    def configured(self) -> bool:
        """Whether a live Plaid SDK client was initialized."""
        return self._client is not None

    # ---------------------------------------------------------------------------
    # Token exchange
    # ---------------------------------------------------------------------------

    def exchange_public_token(self, public_token: str) -> str:
        """Exchange a Plaid public token for a permanent access token."""
        if self.demo_mode:
            return "demo_access_token"
        if self._client is None:
            raise RuntimeError("Plaid is not configured. Set PLAID_CLIENT_ID and PLAID_SECRET, or explicitly enable METATRON_DEMO_MODE for mock data.")

        from plaid.model.item_public_token_exchange_request import (
            ItemPublicTokenExchangeRequest,
        )
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self._client.item_public_token_exchange(request)
        return response["access_token"]

    # ---------------------------------------------------------------------------
    # Holdings
    # ---------------------------------------------------------------------------

    def get_holdings(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch investment holdings for the linked brokerage account.

        Returns a dict keyed by ticker with minimal market data fields
        that the SAP Stage Engine can consume.
        """
        if self.demo_mode and access_token == "demo_access_token":
            return self._mock_holdings()
        if self._client is None:
            raise RuntimeError("Plaid client is unavailable; configure credentials or explicitly enable demo mode.")

        from plaid.model.investments_holdings_get_request import (
            InvestmentsHoldingsGetRequest,
        )
        request = InvestmentsHoldingsGetRequest(access_token=access_token)
        response = self._client.investments_holdings_get(request)
        return self._parse_holdings(response)

    def _parse_holdings(self, response: Any) -> Dict[str, Any]:
        """Convert Plaid InvestmentsHoldingsGetResponse to engine-ready format."""
        holdings: Dict[str, Any] = {}
        securities = {s["security_id"]: s for s in response.get("securities", [])}
        for holding in response.get("holdings", []):
            security = securities.get(holding["security_id"], {})
            ticker = security.get("ticker_symbol") or security.get("name", "UNKNOWN")
            holdings[ticker] = {
                "price_history": [holding.get("institution_price", 0)],
                "volatility": 20,        # placeholder – enrich from market data API
                "rsi": 50,               # placeholder
                "sentiment_score": 0,    # placeholder
                "put_call_ratio": 1.0,   # placeholder
                "quantity": holding.get("quantity", 0),
                "market_value": holding.get("institution_value", 0),
            }
        return holdings

    # ---------------------------------------------------------------------------
    # Transactions
    # ---------------------------------------------------------------------------

    def get_transactions(self, access_token: str, days: int = 90) -> list:
        """Fetch recent investment transactions."""
        if self.demo_mode and access_token == "demo_access_token":
            return self._mock_transactions()
        if self._client is None:
            raise RuntimeError("Plaid client is unavailable; configure credentials or explicitly enable demo mode.")

        from datetime import date, timedelta
        from plaid.model.investments_transactions_get_request import (
            InvestmentsTransactionsGetRequest,
        )
        from plaid.model.investments_transactions_get_request_options import (
            InvestmentsTransactionsGetRequestOptions,
        )

        end = date.today()
        start = end - timedelta(days=days)
        request = InvestmentsTransactionsGetRequest(
            access_token=access_token,
            start_date=start,
            end_date=end,
        )
        response = self._client.investments_transactions_get(request)
        return response.get("investment_transactions", [])

    # ---------------------------------------------------------------------------
    # Mock data
    # ---------------------------------------------------------------------------

    @staticmethod
    def _mock_holdings() -> Dict[str, Any]:
        return {
            "AAPL": {
                "price_history": [150, 152, 151, 153, 155],
                "volatility": 18,
                "rsi": 65,
                "sentiment_score": 0.6,
                "put_call_ratio": 0.9,
                "quantity": 10,
                "market_value": 1550,
            },
            "GME": {
                "price_history": [20, 22, 19, 25, 30],
                "volatility": 80,
                "rsi": 85,
                "sentiment_score": 0.9,
                "put_call_ratio": 0.4,
                "quantity": 5,
                "market_value": 150,
            },
            "MSFT": {
                "price_history": [310, 312, 315, 313, 318],
                "volatility": 14,
                "rsi": 58,
                "sentiment_score": 0.7,
                "put_call_ratio": 0.8,
                "quantity": 8,
                "market_value": 2544,
            },
        }

    @staticmethod
    def _mock_transactions() -> list:
        return [
            {"type": "buy",  "ticker": "AAPL", "amount": 1520, "days_held": 60},
            {"type": "buy",  "ticker": "GME",  "amount": 100,  "days_held": 5},
            {"type": "sell", "ticker": "TSLA", "amount": 800,  "days_held": 120},
        ]
