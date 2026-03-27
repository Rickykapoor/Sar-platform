"""
Module 6 — PII Stripping Layer (Regulatory Compliance)
Zero PII to external LLMs. Complies with RBI Data Localisation Circular (2018) and DPDP Act 2023.
"""
import re
import hashlib
import json
import datetime
from dataclasses import dataclass, field


@dataclass
class StrippingResult:
    stripped_prompt: str
    token_map: dict                 # {TOKEN: REAL_VALUE} — NEVER sent to LLM
    pii_categories_found: list


# Indian financial PII regex patterns
PATTERNS = {
    "PAN":         r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
    "AADHAAR":     r'\b[2-9]{1}[0-9]{11}\b',
    "IFSC":        r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
    "MOBILE":      r'\b[6-9]\d{9}\b',
    "ACCOUNT_NUM": r'\b\d{9,18}\b',
    "AMOUNT_INR":  r'₹[\d,]+(?:\.\d{2})?|\bINR\s*[\d,]+',
    "EMAIL":       r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
}

# In-memory audit log (production: write to PostgreSQL ui_audit_log)
AUDIT_LOG: list = []


class PIIStripper:

    def strip_and_tokenize(self, prompt: str, case_context: dict = None) -> StrippingResult:
        """
        Replaces all Indian financial PII with opaque tokens before sending to LLM.
        Returns StrippingResult with stripped prompt and token_map (kept server-side).
        """
        case_context = case_context or {}
        token_map  = {}
        stripped   = prompt
        found_cats = []
        counters   = {}

        def _replace(match, prefix: str) -> str:
            counters[prefix] = counters.get(prefix, 0) + 1
            token      = f"[{prefix}_{counters[prefix]:03d}]"
            real_value = match.group(0)
            if token not in token_map:
                token_map[token] = real_value
            return token

        # 1. Named entities from case context
        for i, name in enumerate(case_context.get("customer_names", []), 1):
            token = f"[PERSON_{i:03d}]"
            if name and name in stripped:
                stripped = stripped.replace(name, token)
                token_map[token] = name
                found_cats.append("PERSON")

        # 2. Regex-based structured Indian financial PII
        for category, pattern in PATTERNS.items():
            def replacer(m, cat=category):
                return _replace(m, cat)
            new_stripped = re.sub(pattern, replacer, stripped)
            if new_stripped != stripped:
                found_cats.append(category)
            stripped = new_stripped

        return StrippingResult(
            stripped_prompt=stripped,
            token_map=token_map,
            pii_categories_found=list(set(found_cats)),
        )

    def reinsert_pii(self, llm_response: str, token_map: dict) -> str:
        """Re-inserts real PII values after LLM response is received on-premises."""
        result = llm_response
        for token, real_value in sorted(token_map.items(), key=lambda x: -len(x[0])):
            result = result.replace(token, real_value)
        return result

    def generate_audit_entry(self, result: StrippingResult, case_id: str) -> dict:
        """
        Creates an immutable audit log entry proving PII was stripped before any API call.
        Token map is stored as SHA-256 hash only — not in plain text.
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        token_map_hash = hashlib.sha256(
            json.dumps(result.token_map, sort_keys=True).encode()
        ).hexdigest()
        stripped_hash = hashlib.sha256(result.stripped_prompt.encode()).hexdigest()

        payload = {
            "case_id":               case_id,
            "timestamp":             timestamp,
            "event_type":            "PII_STRIPPED",
            "pii_categories_found":  result.pii_categories_found,
            "token_count":           len(result.token_map),
            "token_map_sha256":      token_map_hash,
            "stripped_prompt_hash":  stripped_hash,
            "entry_hash":            hashlib.sha256(
                f"{case_id}{timestamp}{token_map_hash}".encode()
            ).hexdigest()
        }

        # Append-only audit write
        AUDIT_LOG.append(payload)
        return payload


# Module-level singleton
pii_stripper = PIIStripper()


def log_ui_event(user_id: str, user_role: str, event_type: str, metadata: dict) -> dict:
    """
    Records a UI audit event (page view, case open, SAR approval, etc.)
    Append-only: production stores to PostgreSQL with REVOKE UPDATE/DELETE.
    """
    timestamp = datetime.datetime.utcnow().isoformat()
    payload_str = json.dumps({
        "user_id": user_id, "role": user_role,
        "event": event_type, "metadata": metadata, "timestamp": timestamp,
    }, sort_keys=True)

    entry = {
        "user_id":    user_id,
        "user_role":  user_role,
        "event_type": event_type,
        "metadata":   metadata,
        "timestamp":  timestamp,
        "entry_hash": hashlib.sha256(payload_str.encode()).hexdigest()[:16],
    }
    AUDIT_LOG.append(entry)
    return entry


def get_audit_log(limit: int = 200) -> list:
    """Returns most recent audit entries."""
    return AUDIT_LOG[-limit:][::-1]
