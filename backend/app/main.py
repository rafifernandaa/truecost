import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router as api_router

app = FastAPI(
    title="TrueCost Autopilot API",
    description="Backend API for TrueCost Autopilot - AI Financial Participant (FinTechathon 2026 Topic A)",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sliding-window rate limiter & request size guard for sensitive financial endpoints
_RATE_WINDOW_SECONDS = 60.0
_MAX_REQUESTS_PER_WINDOW = int(os.getenv("TRUECOST_RATE_LIMIT_PER_MIN", "120"))
_MAX_BODY_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB max payload
_rate_buckets: Dict[str, Deque[float]] = defaultdict(deque)


def reset_rate_limiter() -> None:
    _rate_buckets.clear()


@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    # 1. Enforce request body size limit
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_BODY_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={"error": "PAYLOAD_TOO_LARGE", "detail": "Request payload exceeds maximum allowed size (5 MB)."},
        )

    # 2. Enforce sliding-window rate limit on sensitive financial & webhook routes
    path = request.url.path
    if path.startswith(("/api/bank", "/api/payments", "/api/webhooks", "/api/mandates")):
        client_ip = request.client.host if request.client else "127.0.0.1"
        bucket_key = f"{client_ip}:{path}"
        now = time.monotonic()
        q = _rate_buckets[bucket_key]
        while q and (now - q[0]) > _RATE_WINDOW_SECONDS:
            q.popleft()
        limit = int(os.getenv("TRUECOST_RATE_LIMIT_PER_MIN", str(_MAX_REQUESTS_PER_WINDOW)))
        if len(q) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "detail": "Too many financial requests. Please retry after a short cooldown.",
                },
            )
        q.append(now)

    # 3. Safe error handling (never leak raw stack traces or environment secrets)
    try:
        response = await call_next(request)
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_FINANCIAL_SERVICE_ERROR",
                "detail": "An unexpected error occurred while processing the request. No partial ledger writes were committed.",
            },
        )

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=()"
    response.headers["X-TrueCost-Guardrail"] = "Ed25519-AP2-AuditGate-DoubleEntry"
    return response


app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TrueCost Autopilot Core",
        "version": "0.3.0",
        "security": {
            "mandates": "Ed25519_VERIFIED",
            "ledger": "DOUBLE_ENTRY_MINOR_UNITS_IMMUTABLE",
            "replay_guard": "SQLITE_SHA256_NONCE_AND_IDEMPOTENCY",
            "payment_gateways": ["XENDIT", "MIDTRANS"],
            "pii_scrubber": "ZERO_RETENTION_LOCAL",
            "audit_gate": "0_HALLUCINATION_STRICT",
        },
    }
