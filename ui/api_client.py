"""
ui/api_client.py
Owned by: Anshul

One function per FastAPI endpoint (10 total).
All functions use `requests` (synchronous — compatible with Streamlit).
All functions: catch ConnectionError / exceptions → return None + log error.
NEVER crash the UI.

Base URL: http://localhost:8000
"""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
TIMEOUT = 10  # seconds


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get(path: str, **kwargs) -> Optional[dict]:
    """Safe GET helper — returns parsed JSON or None."""
    try:
        response = requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        logger.error("API offline: GET %s — backend not reachable at %s", path, BASE_URL)
        return None
    except requests.exceptions.Timeout:
        logger.error("API timeout: GET %s took longer than %ds", path, TIMEOUT)
        return None
    except requests.exceptions.HTTPError as exc:
        logger.error("API HTTP error: GET %s → %s", path, exc)
        return None
    except Exception as exc:
        logger.error("API unexpected error: GET %s → %s", path, exc)
        return None


def _post(path: str, json: Optional[dict] = None, **kwargs) -> Optional[dict]:
    """Safe POST helper — returns parsed JSON or None."""
    try:
        response = requests.post(
            f"{BASE_URL}{path}", json=json, timeout=TIMEOUT, **kwargs
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        logger.error("API offline: POST %s — backend not reachable at %s", path, BASE_URL)
        return None
    except requests.exceptions.Timeout:
        logger.error("API timeout: POST %s took longer than %ds", path, TIMEOUT)
        return None
    except requests.exceptions.HTTPError as exc:
        logger.error("API HTTP error: POST %s → %s", path, exc)
        return None
    except Exception as exc:
        logger.error("API unexpected error: POST %s → %s", path, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. POST /submit-transaction
# ─────────────────────────────────────────────────────────────────────────────

def submit_transaction(transaction_data: dict) -> Optional[dict]:
    """
    Submit a raw transaction dict to the backend.
    The backend will score it, create a SARCase, and run the pipeline if RED.

    Args:
        transaction_data: Raw transaction dict (account_id, amount_usd, etc.)

    Returns:
        SARCase dict on success, or None if backend is unreachable.
    """
    result = _post("/submit-transaction", json=transaction_data)
    if result:
        logger.info("submit_transaction: case created → %s", result.get("case_id"))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET /cases
# ─────────────────────────────────────────────────────────────────────────────

def get_all_cases() -> Optional[list]:
    """
    Fetch list of all SARCase objects from the backend.

    Returns:
        List of SARCase dicts, or None.
    """
    return _get("/cases")


# ─────────────────────────────────────────────────────────────────────────────
# 3. GET /case/{id}
# ─────────────────────────────────────────────────────────────────────────────

def get_case(case_id: str) -> Optional[dict]:
    """
    Fetch a single SARCase by its case_id.

    Returns:
        SARCase dict, or None (404 or backend offline).
    """
    return _get(f"/case/{case_id}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. POST /case/{id}/run-pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(case_id: str) -> Optional[dict]:
    """
    Trigger the full 6-agent LangGraph pipeline on a stored case.

    Returns:
        Updated SARCase dict after pipeline completes, or None.
    """
    return _post(f"/case/{case_id}/run-pipeline")


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /case/{id}/pipeline-status
# ─────────────────────────────────────────────────────────────────────────────

def get_pipeline_status(case_id: str) -> Optional[dict]:
    """
    Get which agents have completed (have non-None output) for a case.

    Returns:
        Dict with agent completion status, or None.
    """
    return _get(f"/case/{case_id}/pipeline-status")


# ─────────────────────────────────────────────────────────────────────────────
# 6. POST /case/{id}/generate-narrative
# ─────────────────────────────────────────────────────────────────────────────

def generate_narrative(case_id: str) -> Optional[dict]:
    """
    Trigger Agent 3 only — generate the SAR narrative for a specific case.
    Used by the 'Generate Narrative' button on the SAR Review page.

    Returns:
        Updated SARCase dict (with narrative populated), or None.
    """
    return _post(f"/case/{case_id}/generate-narrative")


# ─────────────────────────────────────────────────────────────────────────────
# 7. POST /case/{id}/approve
# ─────────────────────────────────────────────────────────────────────────────

def approve_case(case_id: str, analyst_name: str) -> Optional[dict]:
    """
    Approve and file a SAR case — triggers Agent 6 logic.
    Sets status to FILED and records analyst attribution.

    Args:
        case_id:       ID of the case to approve
        analyst_name:  Name of the approving analyst

    Returns:
        Updated SARCase dict (status=FILED), or None.
    """
    return _post(f"/case/{case_id}/approve", json={"analyst_name": analyst_name})


# ─────────────────────────────────────────────────────────────────────────────
# 8. POST /case/{id}/dismiss
# ─────────────────────────────────────────────────────────────────────────────

def dismiss_case(case_id: str) -> Optional[dict]:
    """
    Dismiss a SAR case — sets status to DISMISSED.

    Returns:
        Updated SARCase dict (status=DISMISSED), or None.
    """
    return _post(f"/case/{case_id}/dismiss")


# ─────────────────────────────────────────────────────────────────────────────
# 9. GET /case/{id}/graph
# ─────────────────────────────────────────────────────────────────────────────

def get_case_graph(case_id: str) -> Optional[dict]:
    """
    Fetch nodes and edges for pyvis graph visualisation of a case.

    Returns:
        {"nodes": [...], "edges": [...]} dict, or None.
    """
    return _get(f"/case/{case_id}/graph")


# ─────────────────────────────────────────────────────────────────────────────
# 10. GET /health
# ─────────────────────────────────────────────────────────────────────────────

def health_check() -> bool:
    """
    Check whether the FastAPI backend is reachable.

    Returns:
        True if backend is up, False otherwise.
    """
    result = _get("/health")
    return result is not None and result.get("status") == "ok"
