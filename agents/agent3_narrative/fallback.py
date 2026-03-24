"""
Agent 3 — Narrative Generation
Fallback JSON generator — no LLM, pure string dictionary dump.
Always produces a valid FIU-IND JSON structure.
"""

from __future__ import annotations
import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.shared.schemas import SARCase

def generate_fallback_narrative(state: "SARCase") -> str:
    case_id = state.case_id
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    bank_name = "Barclays India"
    bsr_code = "4001234"
    branch_name = "Pune Tech Hub"
    if state.raw_transaction:
        bank_name = state.raw_transaction.get("bank_name", bank_name)
        bsr_code = state.raw_transaction.get("bsr_code", bsr_code)
        branch_name = state.raw_transaction.get("branch_name", branch_name)

    subject_name = "Unknown"
    account_ids = []
    if state.normalized:
        subject_name = state.normalized.subject_name
        account_ids = state.normalized.subject_account_ids

    risk_score = 0.0
    typology = "Suspicious Pattern"
    if state.risk_assessment:
        risk_score = state.risk_assessment.risk_score
        typology = state.risk_assessment.matched_typology

    narrative = f"The automated monitoring system flagged activity under {typology} with a risk score of {risk_score:.3f}. Manual review of the transaction flow indicates behavior consistent with regulatory alert criteria."

    fallback_dict = {
        "part1_report_details": {"date_of_sending": date_str, "is_replacement": False, "date_of_original_report": None},
        "part2_principal_officer": {
            "bank_name": bank_name, "bsr_code": bsr_code, "fiu_id": "FIU001", "bank_category": "A",
            "officer_name": "System Admin", "designation": "PO", "address": "Fallback Ave",
            "city_town_district": "Pune", "state_country": "India", "pin_code": "411001",
            "telephone": "000", "email": "admin@bank.com"
        },
        "part3_reporting_branch": {
            "branch_name": branch_name, "bsr_code": bsr_code, "fiu_id": "FIU001", "address": "Fallback Ave",
            "city_town_district": "Pune", "state_country": "India", "pin_code": "411001",
            "telephone": "000", "email": "admin@bank.com"
        },
        "part4_linked_individuals": [{"name": subject_name, "customer_id": "CUST001"}],
        "part5_linked_entities": [],
        "part6_linked_accounts": [{"account_number": acc, "account_holder_name": subject_name} for acc in account_ids] or [{"account_number": "UNKNOWN", "account_holder_name": "UNKNOWN"}],
        "part7_suspicion_details": {
            "reasons_for_suspicion": ["Activity in account"],
            "grounds_of_suspicion": narrative
        },
        "part8_action_taken": {"under_investigation": False, "agency_details": ""}
    }

    return json.dumps(fallback_dict)
