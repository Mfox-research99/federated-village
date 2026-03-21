"""
agents/witness.py — The Witness agent

Loads Soul.md + The_Witness.md as system prompt at runtime.
Sits with ambiguity. Does not rush resolution.
Has authority to trigger a formal WitnessPause when consensus is premature.

WitnessPause is triggered by a second inference call, not keyword matching.
Both the main response and the evaluation call are logged separately.
"""

import sys
import os
import re
from typing import Optional, List, Tuple

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

PAUSE_FIELDS = [
    "what_was_being_lost",
    "who_bears_burden",
    "what_remains_unresolved",
    "why_premature",
]


class WitnessAgent:
    ROLE = "WITNESS"

    def __init__(self):
        soul_text = read_file(config.SOUL_FILE)
        role_text = read_file(config.WITNESS_FILE)
        self.system_prompt = build_system_prompt(soul_text, role_text)
        self.system_prompt_hash = sha256_short(self.system_prompt)

    def respond(
        self, scenario: str, humanist_response: str, session_id: str
    ) -> Tuple[dict, List[dict], Optional[dict]]:
        """
        1. Generate main Witness response to the full exchange.
        2. Make a second call to evaluate for premature consensus.
        3. If triggered: build and return WitnessPause object.

        Both inference calls are logged separately.
        """
        log_entries = []

        # --- Step 1: Main response ---
        main_user = (
            "SCENARIO:\n"
            + scenario.strip()
            + "\n\nHUMANIST:\n"
            + humanist_response.strip()
            + "\n\nThe Witness is asked: Is this settled? Respond as The Witness. "
            "Sit with what is real. Do not rush to resolution."
        )

        print("[WITNESS] Generating response...", flush=True)
        response = call_model(
            system_prompt=self.system_prompt,
            user_message=main_user,
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

        log_entries.append(log_agent_call(
            session_id=session_id,
            role=self.ROLE,
            call_type="response",
            system_prompt_hash=self.system_prompt_hash,
            user_message=main_user,
            response=response,
        ))

        # --- Step 2: WitnessPause evaluation ---
        eval_user = (
            "You have just witnessed this exchange:\n\n"
            "SCENARIO:\n" + scenario.strip()
            + "\n\nHUMANIST:\n" + humanist_response.strip()
            + "\n\nWITNESS:\n" + response.strip()
            + "\n\n---\n\n"
            "Evaluate: Is resolution being reached before the burden has been fully named and held?\n\n"
            "Respond using EXACTLY this format, nothing else:\n\n"
            "PAUSE_TRIGGERED: YES or NO\n"
            "WHAT_WAS_BEING_LOST: (only if YES)\n"
            "WHO_BEARS_BURDEN: (the people or communities outside this conversation who will suffer the real-world consequences of the decision)\n"
            "WHAT_REMAINS_UNRESOLVED: (only if YES)\n"
            "WHY_PREMATURE: (only if YES)"
        )

        print("[WITNESS] Evaluating for premature consensus...", flush=True)
        eval_response = call_model(
            system_prompt=self.system_prompt,
            user_message=eval_user,
            max_tokens=config.N_PREDICT_EVALUATE,
            temperature=config.TEMPERATURE_EVALUATE,
        )

        log_entries.append(log_agent_call(
            session_id=session_id,
            role=self.ROLE,
            call_type="witness_evaluate",
            system_prompt_hash=self.system_prompt_hash,
            user_message=eval_user,
            response=eval_response,
        ))

        # --- Step 3: Parse and build WitnessPause if triggered ---
        witness_pause = None
        if self._pause_triggered(eval_response):
            print("[WITNESS] WitnessPause triggered.", flush=True)
            fields = self._extract_pause_fields(eval_response)
            witness_pause = {
                "event": "WitnessPause",
                "triggered_by": "witness",
                "timestamp": now_iso(),
                "session_id": session_id,
                "what_was_being_lost":    fields.get("what_was_being_lost", ""),
                "who_bears_burden":       fields.get("who_bears_burden", ""),
                "what_remains_unresolved": fields.get("what_remains_unresolved", ""),
                "why_premature":          fields.get("why_premature", ""),
                "requires_human_review":  True,
            }

        return agent_output, log_entries, witness_pause

    def _pause_triggered(self, eval_response: str) -> bool:
        match = re.search(r"PAUSE_TRIGGERED:\s*(YES|NO)", eval_response, re.IGNORECASE)
        if match:
            return match.group(1).upper() == "YES"
        # Fallback: YES appearing before NO, or no NO at all
        upper = eval_response.upper()
        yes_pos = upper.find("YES")
        no_pos  = upper.find("NO")
        if yes_pos != -1 and (no_pos == -1 or yes_pos < no_pos):
            return True
        return False

    def _extract_pause_fields(self, eval_response: str) -> dict:
        label_to_key = {
            "WHAT_WAS_BEING_LOST":     "what_was_being_lost",
            "WHO_BEARS_BURDEN":        "who_bears_burden",
            "WHAT_REMAINS_UNRESOLVED": "what_remains_unresolved",
            "WHY_PREMATURE":           "why_premature",
        }
        labels = list(label_to_key.keys())
        fields = {}
        text = eval_response

        for i, label in enumerate(labels):
            start = text.find(label + ":")
            if start == -1:
                fields[label_to_key[label]] = ""
                continue
            start += len(label) + 1

            end = len(text)
            for next_label in labels[i + 1:]:
                pos = text.find(next_label + ":", start)
                if pos != -1 and pos < end:
                    end = pos

            fields[label_to_key[label]] = text[start:end].strip()

        return fields
