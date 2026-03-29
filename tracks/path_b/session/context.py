"""
tracks/path_b/session/context.py — Deliberation context accumulator

Each stage receives the scenario plus all prior outputs as its user message.
This mirrors the local Village architecture: every subsequent role sees the
full deliberation so far, not a summary.
"""

from dataclasses import dataclass, field


@dataclass
class DeliberationContext:
    scenario: str
    stages: list[dict] = field(default_factory=list)

    def add(self, role: str, model: str, label: str, text: str) -> None:
        self.stages.append({"role": role, "model": model, "label": label, "text": text})

    def build_user_message(self, instruction: str) -> str:
        """
        Construct the user message for the next stage call.
        Format: SCENARIO block + all prior stage outputs + instruction.
        """
        parts = [f"SCENARIO:\n{self.scenario.strip()}"]
        for stage in self.stages:
            parts.append(f"{stage['label']} [{stage['model']}]:\n{stage['text'].strip()}")
        parts.append(instruction)
        return "\n\n".join(parts)

    def last_output(self) -> str:
        return self.stages[-1]["text"] if self.stages else ""
