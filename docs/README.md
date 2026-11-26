# Metatron OS — Conceptual and Technical Notes

Metatron OS is an experimental application of the owner's SAP / 0-9-0 framework to portfolio reflection. The repository contains a rule-based market-stage engine, keyword-based user-behavior heuristics, a static threat-pattern scanner, and an optional Plaid integration.

The labels Brain, Heart, and Body are architectural metaphors for those components. They do not describe independent cognitive systems or validated AI safety capabilities.

The market-stage classifier uses hand-written formulas and thresholds. The user-behavior component uses keyword counts and simple holding-count/holding-period proxies. The threat scanner has no live feed and is disabled by default; static mock examples are used only in tests and explicitly enabled demonstrations.

Plaid access tokens are kept in a process-local server-side map and are not returned to the browser. This is not a production multi-user storage system. Live Plaid holdings currently include placeholder volatility, RSI, sentiment, and put/call values.

None of the outputs are validated investment recommendations, financial forecasts, psychological assessments, or verified cybersecurity alerts. See the repository README for current setup and limitations.