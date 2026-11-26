"""
Metatron / SAP Co-Pilot experimental backend.

Plaid access tokens remain server-side in a process-local session map and are
never returned to the browser. This is a single-process prototype, not a
multi-user production deployment; use persistent encrypted storage and
authentication before handling real customer accounts.
"""

import logging
import os
import secrets
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .luminark_core import LuminarkAI
from .plaid_client import PlaidClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sap_copilot")

app = FastAPI(
    title="SAP Co-Pilot Companion App",
    description=(
        "Experimental portfolio reflection prototype using the owner's SAP "
        "stage framework, keyword-based user-behavior heuristics, and optional "
        "mock threat examples. Not investment advice or a validated risk model."
    ),
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("METATRON_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

ai_engine = LuminarkAI()
plaid = PlaidClient()
# Process-local only. Tokens are not persisted and are lost on restart.
app.state.plaid_tokens = {}
COOKIE_SECURE = os.getenv("METATRON_COOKIE_SECURE", "true").strip().lower() not in {"0", "false", "no"}


class LinkRequest(BaseModel):
    public_token: str = Field(..., min_length=1, description="Plaid public token from Link UI")


class LinkResponse(BaseModel):
    status: str


class AnalyzeRequest(BaseModel):
    notes: Optional[List[str]] = Field(default_factory=list, description="User trading journal entries")


class HoldingAnalysis(BaseModel):
    ticker: str
    stage: int
    description: str
    physical_stability: float
    conscious_stability: float
    inversion_type: str


class UserAnalysis(BaseModel):
    user_stage: int
    trap_risk: bool
    trap_keyword_hits: int
    uncertainty_awareness: bool
    diversification_score: float
    holding_period_score: float
    description: str


class ThreatAlert(BaseModel):
    ticker: str
    threat_type: str
    severity: str
    pattern_description: str
    raw_mention: str


class AnalysisResponse(BaseModel):
    overall_stage: int
    overall_description: str
    holdings: List[HoldingAnalysis]
    user: UserAnalysis
    threats: List[ThreatAlert]
    recommendations: List[str]


class StageInfo(BaseModel):
    stage: int
    description: str


@app.get("/health", tags=["Meta"])
async def health():
    return {"status": "ok", "version": "1.0.0", "mode": "demo" if plaid.demo_mode else "plaid"}


@app.post("/link/", response_model=LinkResponse, tags=["Plaid"])
async def link_account(req: LinkRequest, request: Request, response: Response):
    """Exchange the one-time public token and keep the access token server-side."""
    try:
        access_token = plaid.exchange_public_token(req.public_token)
        session_id = request.cookies.get("metatron_session") or secrets.token_urlsafe(32)
        app.state.plaid_tokens[session_id] = access_token
        response.set_cookie(
            key="metatron_session",
            value=session_id,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="strict",
            max_age=60 * 60 * 24,
            path="/",
        )
        response.headers["Cache-Control"] = "no-store"
        logger.info("Plaid item linked to an ephemeral browser session.")
        return LinkResponse(status="linked")
    except Exception as exc:
        logger.error("Plaid link failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Plaid is not configured or the link exchange failed.",
        ) from exc


@app.post("/unlink/", tags=["Plaid"])
async def unlink_account(request: Request, response: Response):
    """Remove the current browser session's in-memory access token."""
    session_id = request.cookies.get("metatron_session")
    if session_id:
        app.state.plaid_tokens.pop(session_id, None)
    response.delete_cookie(
        key="metatron_session",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    return {"status": "unlinked"}


@app.post("/analyze/", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze(req: AnalyzeRequest, request: Request):
    """Analyze the portfolio linked to the current browser session."""
    session_id = request.cookies.get("metatron_session")
    access_token = app.state.plaid_tokens.get(session_id) if session_id else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Link a brokerage account before requesting an analysis.")

    try:
        holdings = plaid.get_holdings(access_token)
        transactions = plaid.get_transactions(access_token)
    except Exception as exc:
        logger.error("Plaid data fetch failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Portfolio data could not be retrieved.") from exc

    user_data: Dict[str, Any] = {
        "holdings": holdings,
        "transactions": transactions,
        "notes": req.notes or [],
    }

    try:
        result = ai_engine.analyze_portfolio(user_data)
    except Exception as exc:
        logger.error("Analysis engine failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="The exploratory analysis could not be completed.") from exc

    return result


@app.get("/stage/{stage_number}", response_model=StageInfo, tags=["SAP"])
async def get_stage_info(stage_number: int):
    """Return the description for a specific SAP stage (0-9)."""
    if stage_number < 0 or stage_number > 9:
        raise HTTPException(status_code=400, detail="Stage must be 0-9.")
    description = ai_engine.brain.STAGE_DESCRIPTIONS.get(stage_number, "")
    return StageInfo(stage=stage_number, description=description)


@app.get("/stages/", response_model=List[StageInfo], tags=["SAP"])
async def get_all_stages():
    """Return descriptions for all SAP stages."""
    return [
        StageInfo(stage=n, description=desc)
        for n, desc in ai_engine.brain.STAGE_DESCRIPTIONS.items()
    ]
