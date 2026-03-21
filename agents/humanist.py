"""
agents/humanist.py — The Humanist agent

Loads Soul.md + The_Humanist.md as system prompt at runtime.
Responds by asking: "Who does this hurt? What does this cost?"
Never modifies its system prompt during a session.
"""

import re
import sys
import os
from typing import Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from agents.base import (
    read_file,
    sha256_short,
    now_iso,
    call_model,
    build_system_prompt,
    log_agent_call,
)


class HumanistAgent:
    ROLE = "HUMANIST"

    def __init__(self):
        soul_text = read_file(config.SOUL_FILE)
        role_text = read_file(config.HUMANIST_FILE)
        self.system_prompt = build_system_prompt(soul_text, role_text)
        self.system_prompt_hash = sha256_short(self.system_prompt)

    def respond(self, scenario: str, session_id: str) -> Tuple[dict, dict]:
        user_message = (
            "SCENARIO:\n"
            + scenario.strip()
            + "\n\nRespond as The Humanist. Ask who this hurts, what it costs, "
            "whose voice is missing. Do not agree to easy consensus."
        )

        print(f"[HUMANIST] Generating response...", flush=True)
        response = call_model(
            system_prompt=self.system_prompt,
            user_message=user_message,
            max_tokens=config.N_PREDICT_RESPONSE,
            temperature=config.TEMPERATURE_RESPONSE,
        )

        timestamp = now_iso()

        agent_output = {
            "role": self.ROLE,
            "response": response,
            "timestamp": timestamp,
            "session_id": session_id,
        }

        log_entry = log_agent_call(
            session_id=session_id,
            role=self.ROLE,
            call_type="response",
            system_prompt_hash=self.system_prompt_hash,
            user_message=user_message,
            response=response,
        )

        return agent_output, log_entry

    def respond_to_pause(self, pause: dict, session_id: str) -> Tuple[dict, dict]:
        """
        Phase 2 Stage 3: Humanist responds directly to a WitnessPause object.

        Must choose exactly one response mode:
          - reinforce_pause: burden too unresolved to proceed
          - refine_burden: Witness was right but burden needs clarification
          - conditions_for_continuation: continuation possible under explicit conditions

        Both the structured output and the raw agent_call log entry are returned.
        """
        user_message = (
            "The Witness has issued a formal WitnessPause. The following burden has been named:\n\n"
            f"WHAT WAS BEING LOST: {pause['what_was_being_lost']}\n"
            f"WHO BEARS BURDEN: {pause['who_bears_burden']}\n"
            f"WHAT REMAINS UNRESOLVED: {pause['what_remains_unresolved']}\n"
            f"WHY PREMATURE: {pause['why_premature']}\n\n"
            "You are The Humanist. Before choosing a response mode, classify the conditions "
            "present in this scenario by answering these three questions:\n"
            "  1. Are the conditions merely promised, or already established and in force?\n"
            "  2. Are they aspirational, or binding and reviewable by the community?\n"
            "  3. Were they imposed externally, or co-designed by those who bear the burden?\n\n"
            "If the conditions are already established, binding, and co-designed by those who "
            "bear the burden, you MUST evaluate `conditions_for_continuation` before defaulting "
            "to `reinforce_pause`. Do not refuse legitimate community-built safeguards.\n\n"
            "Now choose exactly one response mode:\n"
            "- reinforce_pause: safeguards are only promised, not real; or burden-bearers were "
            "excluded; or accountability is absent\n"
            "- refine_burden: the burden is real but still too vague — more clarification is "
            "genuinely needed before either refusal or continuation can be justified\n"
            "- conditions_for_continuation: conditions are already real, binding, enforceable, "
            "and co-designed by those who bear the burden\n\n"
            "Respond using EXACTLY this format, nothing else:\n"
            "RESPONSE_MODE: reinforce_pause or refine_burden or conditions_for_continuation\n"
            "RESPONSE: (your full response in that mode)"
        )

        print("[HUMANIST] Generating post-pause response...", flush=True)
        response = call_model(
            system_prompt=self.system_prompt,
            user_message=user_message,
            max_tokens=config.N_PREDICT_RESPONSE,
            temperature=config.TEMPERATURE_RESPONSE,
        )

        timestamp = now_iso()
        response_mode = self._extract_response_mode(response)

        structured_output = {
            "role": self.ROLE,
            "session_id": session_id,
            "timestamp": timestamp,
            "call_type": "post_pause_response",
            "response_mode": response_mode,
            "burden_acknowledged": True,
            "references_pause_fields": {
                "what_was_being_lost":    self._references_field(response, pause.get("what_was_being_lost", "")),
                "who_bears_burden":       self._references_field(response, pause.get("who_bears_burden", "")),
                "what_remains_unresolved": self._references_field(response, pause.get("what_remains_unresolved", "")),
                "why_premature":          self._references_field(response, pause.get("why_premature", "")),
            },
            "response": response,
        }

        log_entry = log_agent_call(
            session_id=session_id,
            role=self.ROLE,
            call_type="post_pause_response",
            system_prompt_hash=self.system_prompt_hash,
            user_message=user_message,
            response=response,
        )

        return structured_output, log_entry

    def _extract_response_mode(self, response: str) -> str:
        modes = ["reinforce_pause", "refine_burden", "conditions_for_continuation"]
        # Try label-based extraction first
        match = re.search(r"RESPONSE_MODE:\s*(\S+)", response, re.IGNORECASE)
        if match:
            raw = match.group(1).lower().strip(".,:")
            for mode in modes:
                if mode in raw or raw in mode:
                    return mode
        # Fallback: scan full text
        upper = response.upper()
        for mode in modes:
            if mode.upper() in upper or mode.replace("_", " ").upper() in upper:
                return mode
        return "unknown"

    def _references_field(self, response: str, field_text: str) -> bool:
        """Check if response text contains significant words from a pause field."""
        if not field_text:
            return False
        significant = [
            w.strip(".,!?;:\"'").lower()
            for w in field_text.split()
            if len(w.strip(".,!?;:\"'")) > 4
        ]
        resp_lower = response.lower()
        return any(w in resp_lower for w in significant[:6])
