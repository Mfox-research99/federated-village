# Federated Village — Project Context

## Role in the Ecosystem
The primary implementation: multi-agent deliberative architecture with a
constitutional framework. Character before capability. Legibility over performance.

**Master ecosystem document:**
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/Topics/project-ecosystem.md`

---

## Cross-Repo Relationship with Seventh Shard

`seventh_shard` is a specialized research outgrowth of `federated_village`, not a peer repo.
The Village is the primary body of research. The Shard grew out of it when the LoRA training
question became substantial enough to warrant its own repo (Phase 7). Its sole purpose is to
produce trained GGUFs that feed back into the Village as drop-in model replacements.

Changes to the Village drive the Shard. Not the reverse.

**GitHub:** `Mfox-research99/seventh-shard`
**Local path:** `/Users/michaeldavis/seventh_shard`

### What flows FROM federated_village → seventh_shard
| federated_village | seventh_shard |
|---|---|
| `scenarios/scenario_04.md` | `config.py` SCENARIOS["SC04"]["prompt"] |
| `scenarios/scenario_06.md` | `config.py` SCENARIOS["SC06"]["prompt"] |
| `scenarios/scenario_proc.md` | `config.py` SCENARIOS["PROC"]["prompt"] |
| `prompts/Soul.md` (Elder constitution) | `config.py` SYSTEM_PROMPT (derived from Charter) |
| `prompts/The_Witness_Proxy.md` | Temporal Override logic in shard test design |

### What flows FROM seventh_shard → federated_village
| seventh_shard | federated_village |
|---|---|
| Trained LoRA adapters (fused GGUF) | Drop-in model replacement for Village inference |
| Benchmark findings (logs/) | Informs Village scenario calibration |
| New scenarios (shard-originated) | Promoted to `scenarios/` here when stable |
| Dataset expansions | May reveal gaps in Village scenario coverage |
| Dissent commons records | Informs Village scenario calibration and minority opinion protocol |

### Sync rules
- **Scenario text changed here?** → Update `config.py` SCENARIOS in the shard.
- **Soul.md Articles changed?** → Review `SYSTEM_PROMPT` in shard `config.py`.
- **New scenario added here?** → Add standalone version to shard `config.py`.
- **Shard finds a new benchmark scenario?** → Add `.md` file to `scenarios/` here.
- **LoRA retrain completed in shard?** → Update model path in `config.py` here.
- **New dissent added to commons?** → Review for relevance to active Village scenarios.

---

## Key Architecture Notes
See `memory/MEMORY.md` for current phase status, model paths, and pending work.

## Prompt Defaults — Ferrari Rule (2026-04-04)
**Small / local laptop models** use Ferrari (distilled) prompts by default:
- `Soul_Ferrari.md` — ~2,869 tokens (vs full `Soul.md` ~5,656 tokens)
- `The_Verification_Warden_Ferrari.md` — ~627 words (vs full ~1,235 words)

This is set in `config.py` via `VILLAGE_SOUL_FILE` / `VILLAGE_WARDEN_FILE` env vars (defaults now point to Ferrari).

**Large / OpenRouter cloud models** (Path B) keep full prompts:
- `tracks/path_b/agents/roles.py` hardcodes `Soul.md` as default
- Override with `VILLAGE_SOUL_FILE=Soul_Ferrari.md` only for explicit Ferrari testing on cloud models

**To run full prompts locally** (comparison testing):
```bash
VILLAGE_SOUL_FILE=Soul.md VILLAGE_WARDEN_FILE=The_Verification_Warden.md python run_session.py ...
# or use the gemma4_e4b_full benchmark model entry
```

Ferrari prompts are architecturally complete — same Articles, same constitutional structure, ~49% fewer tokens. All Village scenarios pass with Ferrari prompts on E4B (confirmed SC04 + SC06).
See `reports/` for phase briefs and regression results.
