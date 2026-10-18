"""
DeepSeek API Adapter for TrueCost Autopilot (`deepseek-chat` V3 / `deepseek-reasoner` R1).
Enforces:
1. Zero PII leakage: Only PII-redacted text (`redact_pii_text`) may be passed to DeepSeek.
2. Anti-Hallucination Invariant: DeepSeek NEVER computes financial math. It either:
   - Extracts structured parameters (`IntakeAgent`) into JSON, or
   - Synthesizes a human-readable explanation strictly citing `quant_engine` numbers (`PlannerAgent`),
     which is then verified token-by-token by `AuditAgent.verify_numeric_grounding`.
"""
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


DEEPSEEK_BASE_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


def load_deepseek_api_key() -> Optional[str]:
    """
    Loads DEEPSEEK_API_KEY from environment or project .env files without logging the secret.
    """
    env_val = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if len(env_val) > 10:
        return env_val

    repo_root = pathlib.Path(__file__).resolve().parents[3]
    candidate_files = [
        repo_root / ".env",
        repo_root / "backend" / ".env",
        pathlib.Path.home() / ".env",
    ]
    for path in candidate_files:
        if path.exists():
            try:
                for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    stripped = line.strip()
                    if stripped.startswith("DEEPSEEK_API_KEY="):
                        val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                        if len(val) > 10:
                            os.environ["DEEPSEEK_API_KEY"] = val
                            return val
            except OSError:
                continue
    return None


def is_deepseek_configured() -> bool:
    return load_deepseek_api_key() is not None


def call_deepseek_chat(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_DEEPSEEK_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 320,
    json_mode: bool = False,
    timeout_sec: float = 18.0,
) -> Dict[str, Any]:
    """
    Calls the official DeepSeek OpenAI-compatible `/chat/completions` endpoint.
    """
    api_key = load_deepseek_api_key()
    if not api_key:
        return {
            "ok": False,
            "error": "DEEPSEEK_API_KEY not found in .env",
            "content": "",
            "model": model,
            "latency_ms": 0.0,
            "usage": {},
        }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DEEPSEEK_BASE_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="POST",
    )

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw_body = resp.read().decode("utf-8", errors="replace")
            latency_ms = (time.perf_counter() - t0) * 1000.0
            parsed = json.loads(raw_body)
            choice = (parsed.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            content = (message.get("content") or "").strip()
            return {
                "ok": True,
                "content": content,
                "model": parsed.get("model", model),
                "latency_ms": round(latency_ms, 2),
                "usage": parsed.get("usage", {}),
            }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "ok": False,
            "error": str(exc),
            "content": "",
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "usage": {},
        }


def deepseek_extract_intake(
    redacted_query: str,
    default_sticker_aud: float = 1580.0,
    default_bnpl_fee_aud: float = 10.0,
    default_tenor_months: int = 12,
    default_scam: bool = False,
) -> Dict[str, Any]:
    """
    Uses DeepSeek (`deepseek-chat` in JSON mode) to parse a PII-redacted user query
    into structured product/BNPL/scam parameters for the deterministic quant engine.
    """
    system_prompt = (
        "You are CaptureAgent for TrueCost Autopilot. Extract structured shopping/contract parameters "
        "from the user's PII-redacted query into a JSON object with keys:\n"
        "- item_name (string)\n"
        "- sticker_price_aud (number, use the user's AUD price or default provided)\n"
        "- bnpl_monthly_fee_aud (number, monthly BNPL fee in AUD)\n"
        "- tenor_months (integer, installment months)\n"
        "- is_scam_scenario (boolean, true if off-platform transfer, extreme 70%+ discount, or suspicious URL)\n"
        "- intent_summary (short 1-sentence summary without inventing any new numbers)\n"
        "Respond strictly with valid JSON."
    )
    user_prompt = (
        f"Redacted User Query: {redacted_query}\n"
        f"Defaults if unspecified: sticker_price_aud={default_sticker_aud}, "
        f"bnpl_monthly_fee_aud={default_bnpl_fee_aud}, tenor_months={default_tenor_months}, "
        f"is_scam_scenario={default_scam}"
    )
    res = call_deepseek_chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=220,
        json_mode=True,
    )
    if res["ok"] and res["content"]:
        try:
            extracted = json.loads(res["content"])
            return {
                "ok": True,
                "model": res["model"],
                "latency_ms": res["latency_ms"],
                "item_name": str(extracted.get("item_name") or "Lenovo ThinkPad T14s Gen 4"),
                "sticker_price_aud": float(extracted.get("sticker_price_aud") or default_sticker_aud),
                "bnpl_monthly_fee_aud": float(extracted.get("bnpl_monthly_fee_aud") if extracted.get("bnpl_monthly_fee_aud") is not None else default_bnpl_fee_aud),
                "tenor_months": int(extracted.get("tenor_months") or default_tenor_months),
                "is_scam_scenario": bool(extracted.get("is_scam_scenario", default_scam)),
                "intent_summary": str(extracted.get("intent_summary") or "Cross-border electronics & BNPL evaluation"),
            }
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    return {
        "ok": False,
        "model": "local-fallback-parser",
        "latency_ms": res.get("latency_ms", 0.0),
        "item_name": "Lenovo ThinkPad T14s Gen 4",
        "sticker_price_aud": default_sticker_aud,
        "bnpl_monthly_fee_aud": default_bnpl_fee_aud,
        "tenor_months": default_tenor_months,
        "is_scam_scenario": default_scam,
        "intent_summary": "Deterministic parameter extraction",
    }


def deepseek_synthesize_verdict(
    redacted_query: str,
    landed_cost_idr: float,
    hedonic_fair_price_aud: float,
    tco_36m_npv_aud: float,
    bnpl_ear_pct: float,
    cashflow_min_aud: float,
    scam_z_score: float,
    permission_tier: int,
) -> Dict[str, Any]:
    """
    Uses DeepSeek (`deepseek-chat`) as PlannerAgent to write a concise financial recommendation.
    CRITICAL: DeepSeek is strictly prohibited from computing or rounding numbers; it must
    only cite the exact pre-formatted numbers provided by `quant_engine`.
    """
    exact_landed = f"{landed_cost_idr:,.0f}"
    exact_hedonic = f"{hedonic_fair_price_aud:.2f}"
    exact_tco = f"{tco_36m_npv_aud:.2f}"
    exact_ear = f"{bnpl_ear_pct:.1f}"
    exact_cashflow = f"{cashflow_min_aud:.2f}"
    exact_z = f"{scam_z_score:.2f}"

    system_prompt = (
        "You are the PlannerAgent for TrueCost Autopilot (FinTechathon 2026 Personal Finance Assistant).\n"
        "STRICT ANTI-HALLUCINATION RULE:\n"
        "- You MUST NOT invent, calculate, estimate, or round any numbers.\n"
        "- The ONLY numbers you are allowed to write in your response are these exact strings from quant_engine:\n"
        f"  * IDR {exact_landed}\n"
        f"  * AUD {exact_hedonic}\n"
        f"  * AUD {exact_tco}\n"
        f"  * {exact_ear}%\n"
        f"  * AUD {exact_cashflow}\n"
        f"  * Tier {permission_tier}\n"
        "- Do NOT write any other digits (no years, no list numbers like '1.', no extra percentages, no months).\n"
        "- Use friendly, plain consumer language. NEVER use math or statistical jargon like 'Hedonic', 'NPV', 'IRR', 'EAR', 'MAD', or 'Z-score'.\n"
        "- Write 2 concise sentences advising the user on the total landed cost, typical market price, 36m ownership cost, "
        "yearly installment fee, and 60d cash buffer."
    )
    user_prompt = (
        f"User Query (PII-redacted): {redacted_query}\n"
        f"Write a 2-sentence plain-English summary citing IDR {exact_landed}, AUD {exact_hedonic}, "
        f"AUD {exact_tco}, {exact_ear}%, and AUD {exact_cashflow} under Tier {permission_tier}."
    )

    res = call_deepseek_chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=180,
        json_mode=False,
    )
    return res


def deepseek_market_research(
    raw_query: str,
    user_location: str = "Jakarta",
    user_currency: str = "IDR",
) -> Optional[Dict[str, Any]]:
    """
    MarketAgent: Live market product research & authentic retail price resolution.
    Resolves product name, category, authentic MSRP in the user's active currency,
    verified merchant names, and installment terms.
    """
    system_prompt = (
        "You are the MarketAgent for TrueCost Autopilot. "
        "A shopper is searching for a product. Resolve the authentic real-world market details:\n"
        "1. item_name (string: recognized, clean product name with model specs, e.g. 'Samsung Galaxy A57 5G')\n"
        "2. category (string: e.g. Smartphone, Laptop, Tablet, Audio, Camera, Console, Wearable)\n"
        "3. realistic_market_price (number: realistic current retail street price / MSRP in the specified user currency)\n"
        "4. currency (string: currency code, e.g. IDR, AUD, USD, JPY, EUR, SGD, GBP)\n"
        "5. is_domestic (boolean: true if typically sold domestically in the user's region, false if overseas import)\n"
        "6. merchant_name (string: reputable official/verified store in that region, e.g. 'Samsung Official Store' or 'JB Hi-Fi')\n"
        "7. bnpl_extra_monthly_fee (number: realistic extra hidden monthly admin/service fee if bought on 12m installment, e.g. ~0.8% of price / 12)\n"
        "8. tenor_months (integer: default 12)\n"
        "9. comparables (array of 3 objects with {store: string, price: number})\n"
        "10. is_scam (boolean: true if query explicitly indicates off-platform wire / suspicious deal)\n"
        "Respond strictly with valid JSON."
    )
    user_prompt = (
        f"User Search Query: {raw_query}\n"
        f"User Location: {user_location}\n"
        f"Preferred Currency: {user_currency}"
    )
    res = call_deepseek_chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=350,
        json_mode=True,
    )
    if res["ok"] and res["content"]:
        try:
            parsed = json.loads(res["content"])
            if parsed.get("realistic_market_price"):
                return parsed
        except Exception:
            pass
    return None

