# Metatron OS — SAP Portfolio Reflection Prototype

## What it is

Metatron OS is an experimental portfolio-analysis prototype built around the owner's 0-9-0 / SAP framework. It combines:

- A rule-based market-stage classifier using supplied volatility, RSI, sentiment, put/call ratio, and price-history inputs.
- A keyword-based trading-journal heuristic that flags selected absolute or overconfident language.
- A threat-keyword scanner with static demonstration examples available only when explicitly enabled.
- An optional Plaid integration intended to retrieve brokerage holdings and investment transactions.

## What it is not

This is not a validated financial forecasting model, investment adviser, cybersecurity threat-intelligence feed, or psychological assessment. The stage rules are hand-written thresholds, not a trained model. No backtest or independent predictive evaluation is included.

## Important data limitation

The current Plaid holdings parser retrieves account holdings but fills volatility, RSI, sentiment, and put/call ratio with fixed placeholders. The market-stage output therefore must not be treated as a live market analysis until those fields are connected to reliable market-data sources. Price history currently contains only the institution's current holding price.

The threat scanner does not connect to live news, social media, or cybersecurity feeds. It returns no alerts by default. Static sample alerts can be enabled in tests or demonstrations only.

The user-behavior module uses keyword counts and simple holdings/holding-period proxies. Its diversification score counts holdings and does not inspect sectors, correlations, or portfolio weights.

## Run a local demonstration

Install dependencies:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

To use only static demonstration holdings, explicitly enable demo mode:

```bash
METATRON_DEMO_MODE=true METATRON_COOKIE_SECURE=false uvicorn app.main:app --reload
```

METATRON_COOKIE_SECURE=false is for localhost development only. Do not use it on a network-facing deployment.

To attempt a real Plaid sandbox or production connection, install plaid-python and configure PLAID_CLIENT_ID, PLAID_SECRET, and PLAID_ENV. Do not commit credentials.

Optional CORS configuration: set METATRON_ALLOWED_ORIGINS to a comma-separated allowlist of exact frontend origins. By default, cross-origin access is not enabled.

## Session and security limitations

Plaid access tokens are kept in a process-local in-memory map and are not returned to the browser. They are lost when the server restarts. This is a single-process prototype, not secure multi-user account storage. Before real customer use, implement authenticated users, persistent encrypted token storage, CSRF protections, audit logging, secure session lifecycle, and a security review.

## Tests

From the repository root:

```bash
pip install -r backend/requirements.txt pytest
pytest backend/tests -q
```

The tests use synthetic inputs and explicit mock threat examples. Passing them verifies selected code paths only; it does not validate market predictions, investment outcomes, threat detection, or user-behavior classifications.

## Conceptual origin and implementation

The project owner states that the underlying concepts and the 0-9-0 / SAP framework originated with him. AI systems generated the implementation code and suggested technical mechanisms. NSDT and the Container Rule were introduced by AI as supporting implementation mechanisms within the owner's framework, not as independent conceptual origins. This records the owner's account and is not a legal determination of copyright ownership, inventorship, or exclusive rights. Review third-party licenses, dependencies, and AI-service terms before commercial transfer.