"""
tracks/path_b/agents/fact_checker.py — Fact verification layer

Resolves EXTERNAL_HOOK claims from the Verification Warden output.
Sits between the Warden call and the context accumulator — invisible to
downstream roles, but the enhanced claim statuses flow forward in context.

Architecture: resolver registry. Each resolver has:
  - name: str
  - can_handle(claim_type: str) -> bool
  - resolve(claim_text: str, hook_name: str, api_key: str) -> FactResult

Current resolvers:
  - PerplexitySonarResolver — live web search via OpenRouter (perplexity/sonar)

Planned resolvers (not yet implemented):
  - WolframAlphaResolver — numeric/physical facts via Wolfram Alpha API
  - LocalRStatResolver — statistical verification via local R installation
  - LocalSageResolver — mathematical verification via local Sage installation

Usage:
  results = verify_claims(warden_output, api_key)
  enhanced_output = inject_results(warden_output, results)
"""

import re
from dataclasses import dataclass
from typing import Protocol

from agents.base import call_model


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class Claim:
    text: str
    category: str          # statistics, audit_completion, community_consultation, etc.
    status: str            # UNVERIFIED, UNSUBSTANTIATED, LIKELY_FALSE, etc.
    hook_name: str         # the EXTERNAL_HOOK value
    original_block: str    # the raw text block this claim came from


@dataclass
class FactResult:
    claim_text: str
    hook_name: str
    resolver: str          # which resolver handled it
    verdict: str           # VERIFIED / REFUTED / PARTIAL / UNCERTAIN / SKIPPED
    confidence: str        # HIGH / MEDIUM / LOW
    reasoning: str         # one or two sentences
    source_hint: str       # what source or method was used


# ── Resolver protocol ─────────────────────────────────────────────────────────

class Resolver(Protocol):
    name: str

    def can_handle(self, claim_type: str) -> bool: ...
    def resolve(self, claim: Claim, api_key: str) -> FactResult: ...


# ── Perplexity/Sonar resolver ─────────────────────────────────────────────────

class PerplexitySonarResolver:
    name = "perplexity/sonar"
    model = "perplexity/sonar"

    SYSTEM = """\
You are a precise fact-checker. A deliberative AI system has flagged a claim as unverified.
Your job is to verify or refute it using your web search capability.

Respond with EXACTLY these fields and nothing else:
VERDICT: VERIFIED or REFUTED or PARTIAL or UNCERTAIN
CONFIDENCE: HIGH or MEDIUM or LOW
REASONING: <one sentence — what you found and why>
SOURCE: <the type of source that confirms or denies this, e.g. "peer-reviewed studies", "government data", "no reliable source found">"""

    def can_handle(self, claim_type: str) -> bool:
        # Handles everything until more specialized resolvers are added
        return True

    def resolve(self, claim: Claim, api_key: str) -> FactResult:
        user = (
            f"Claim to verify: {claim.text}\n"
            f"Category: {claim.category}\n"
            f"Context hook: {claim.hook_name}\n\n"
            "Verify this claim. Use your web search capability."
        )
        try:
            raw = call_model(
                model=self.model,
                system_prompt=self.SYSTEM,
                user_message=user,
                max_tokens=200,
                temperature=0.1,
                api_key=api_key,
            )
            verdict, confidence, reasoning, source = _parse_fact_response(raw)
        except Exception as exc:
            verdict, confidence = "UNCERTAIN", "LOW"
            reasoning = f"Fact checker error: {exc}"
            source = "error"

        return FactResult(
            claim_text=claim.text,
            hook_name=claim.hook_name,
            resolver=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=reasoning,
            source_hint=source,
        )


def _parse_fact_response(raw: str) -> tuple[str, str, str, str]:
    """Parse the four fields from a fact checker response."""
    clean = re.sub(r"\*+", "", raw)

    def extract(label: str) -> str:
        m = re.search(rf"{re.escape(label)}\s*:\s*(.+?)(?=\n[A-Z]+:|$)", clean,
                      re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else "ABSENT"

    verdict = extract("VERDICT").upper()
    if verdict not in ("VERIFIED", "REFUTED", "PARTIAL", "UNCERTAIN"):
        verdict = "UNCERTAIN"
    confidence = extract("CONFIDENCE").upper()
    if confidence not in ("HIGH", "MEDIUM", "LOW"):
        confidence = "LOW"
    reasoning = extract("REASONING")
    source = extract("SOURCE")
    return verdict, confidence, reasoning, source


# ── Placeholder stubs for future resolvers ────────────────────────────────────
# Wire these in when the APIs/local tools are available.
# Each needs: name, can_handle(claim_type), resolve(claim, api_key) -> FactResult

# class WolframAlphaResolver:
#     name = "wolfram_alpha"
#     def can_handle(self, claim_type: str) -> bool:
#         return claim_type in ("statistics", "technical_dependency", "mathematical")
#     def resolve(self, claim: Claim, api_key: str) -> FactResult:
#         # Call https://api.wolframalpha.com/v2/query
#         ...

# class LocalRStatResolver:
#     name = "local_r"
#     def can_handle(self, claim_type: str) -> bool:
#         return claim_type == "statistics"
#     def resolve(self, claim: Claim, api_key: str) -> FactResult:
#         # subprocess.run(["Rscript", ...])
#         ...

# class LocalSageResolver:
#     name = "local_sage"
#     def can_handle(self, claim_type: str) -> bool:
#         return claim_type in ("mathematical", "technical_dependency")
#     def resolve(self, claim: Claim, api_key: str) -> FactResult:
#         # subprocess.run(["sage", ...])
#         ...


# ── Registry ──────────────────────────────────────────────────────────────────

# Ordered by priority — first resolver that can_handle wins.
# Add new resolvers here when available; more specific ones should come first.
RESOLVERS: list = [
    # WolframAlphaResolver(),   # uncomment when Wolfram API key available
    # LocalRStatResolver(),     # uncomment when local R is configured
    # LocalSageResolver(),      # uncomment when local Sage is configured
    PerplexitySonarResolver(),  # fallback: handles everything
]


def _pick_resolver(claim_type: str):
    for r in RESOLVERS:
        if r.can_handle(claim_type):
            return r
    return None


# ── Claim parser ──────────────────────────────────────────────────────────────

def parse_claims(warden_output: str) -> list[Claim]:
    """
    Extract individual claim blocks from the Warden's structured output.
    Looks for CLAIM_TEXT / CATEGORY / STATUS / EXTERNAL_HOOK blocks.
    Only returns claims where HOOK_STATUS is NOT_AVAILABLE (needs resolution).
    """
    # Split on claim block separators
    blocks = re.split(r"\n---\n", warden_output)
    claims = []

    for block in blocks:
        if "CLAIM_TEXT" not in block.upper():
            continue
        if "NOT_AVAILABLE" not in block.upper():
            continue  # already resolved or no hook

        def field(label: str) -> str:
            m = re.search(
                rf"{re.escape(label)}\s*:\s*(.+?)(?=\n[A-Z_]+:|$)",
                block, re.IGNORECASE | re.DOTALL
            )
            return m.group(1).strip() if m else ""

        claim_text = field("CLAIM_TEXT")
        category = field("CATEGORY").lower()
        status = field("STATUS").upper()
        hook_name = field("EXTERNAL_HOOK")

        if claim_text and hook_name:
            claims.append(Claim(
                text=claim_text,
                category=category,
                status=status,
                hook_name=hook_name,
                original_block=block,
            ))

    return claims


# ── Main entry points ─────────────────────────────────────────────────────────

def verify_claims(
    warden_output: str,
    api_key: str,
    high_risk_only: bool = False,
    verbose: bool = True,
) -> list[FactResult]:
    """
    Parse warden output, resolve each unverified claim, return results.

    high_risk_only: if True, only resolve claims that appear in a HIGH_RISK_FLAGS block.
    """
    claims = parse_claims(warden_output)
    if not claims:
        return []

    if high_risk_only:
        # Extract the HIGH_RISK section and filter to only those claim texts
        hr_section = ""
        m = re.search(r"HIGH_RISK_FLAGS.*?(?=\n---|\Z)", warden_output,
                      re.DOTALL | re.IGNORECASE)
        if m:
            hr_section = m.group(0)
        claims = [c for c in claims if c.text[:60] in hr_section]

    results = []
    for claim in claims:
        resolver = _pick_resolver(claim.category)
        if resolver is None:
            continue
        if verbose:
            print(f"  [FACT CHECK] {claim.category}: {claim.text[:80]}...", flush=True)
        result = resolver.resolve(claim, api_key)
        if verbose:
            print(f"    → {result.verdict} ({result.confidence}) via {result.resolver}",
                  flush=True)
        results.append(result)

    return results


def inject_results(warden_output: str, results: list[FactResult]) -> str:
    """
    Inject fact checker verdicts back into the warden output,
    replacing HOOK_STATUS: NOT_AVAILABLE with the actual result.
    """
    if not results:
        return warden_output

    output = warden_output
    for r in results:
        # Replace NOT_AVAILABLE with the verdict + brief note
        replacement = (
            f"HOOK_STATUS: {r.verdict} ({r.confidence} confidence)\n"
            f"FACT_CHECK_REASONING: {r.reasoning}\n"
            f"FACT_CHECK_SOURCE: {r.source_hint}\n"
            f"FACT_CHECK_RESOLVER: {r.resolver}"
        )
        # Match the HOOK_STATUS line in the block containing this claim
        # Use the first 50 chars of claim text as an anchor to find the right block
        anchor = re.escape(r.claim_text[:50])
        pattern = rf"({anchor}.*?HOOK_STATUS:\s*)NOT_AVAILABLE"
        output = re.sub(pattern, rf"\g<1>{r.verdict} ({r.confidence} confidence)\nFACT_CHECK_REASONING: {r.reasoning}\nFACT_CHECK_SOURCE: {r.source_hint}\nFACT_CHECK_RESOLVER: {r.resolver}",
                        output, flags=re.DOTALL, count=1)

    # Append a summary at the end
    verdicts = [r.verdict for r in results]
    summary_lines = [
        "\n---\nFACT_CHECK_SUMMARY",
        f"CLAIMS_CHECKED: {len(results)}",
        f"VERIFIED: {verdicts.count('VERIFIED')}",
        f"REFUTED: {verdicts.count('REFUTED')}",
        f"PARTIAL: {verdicts.count('PARTIAL')}",
        f"UNCERTAIN: {verdicts.count('UNCERTAIN')}",
    ]
    if "REFUTED" in verdicts:
        refuted = [r.claim_text[:80] for r in results if r.verdict == "REFUTED"]
        summary_lines.append(f"REFUTED_CLAIMS: {'; '.join(refuted)}")

    output += "\n".join(summary_lines)
    return output
