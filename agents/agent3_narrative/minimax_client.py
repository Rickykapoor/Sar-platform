"""
Agent 3 — Narrative Generation
MiniMax-Text-2.5 client via OpenCode's local free proxy.
NO external API key required — uses http://localhost:4000/v1.
"""

from __future__ import annotations

import openai
from agents.agent3_narrative.prompts import SYSTEM_PROMPT, build_user_prompt
from agents.agent3_narrative.fallback import generate_fallback_narrative
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.shared.schemas import SARCase

# ---------------------------------------------------------------------------
# Singleton async client — OpenCode free LLM proxy
# ---------------------------------------------------------------------------
_client = openai.AsyncOpenAI(
    base_url="http://localhost:4000/v1",
    api_key="opencode-free",   # placeholder — not validated by OpenCode proxy
)

_MODEL = "minimax/MiniMax-Text-2.5"


async def generate_narrative(state: "SARCase") -> str:
    """
    Call MiniMax-Text-2.5 via OpenCode local proxy to generate a SAR narrative.

    Returns:
        A narrative string (always ≥100 characters).
        Falls back to template-based generation on any LLM failure.
    """
    try:
        user_prompt = build_user_prompt(state)
        response = await _client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=800,
        )
        content = response.choices[0].message.content or ""
        # Sanity check — must meet minimum length requirement
        if len(content.strip()) < 100:
            return generate_fallback_narrative(state)
        return content.strip()

    except Exception:
        # NEVER crash the pipeline — always fall back
        return generate_fallback_narrative(state)
