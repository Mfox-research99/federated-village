# Federated Village — Project Context

## Role in the Ecosystem
The primary implementation: multi-agent deliberative architecture with a
constitutional framework. Character before capability. Legibility over performance.

**Master ecosystem document:**
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/Topics/project-ecosystem.md`

---

## Cross-Repo Relationship with Seventh Shard

`federated_village` and `seventh_shard` are companion repositories.
Changes in one may need to be reflected in the other.

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
See `reports/` for phase briefs and regression results.
