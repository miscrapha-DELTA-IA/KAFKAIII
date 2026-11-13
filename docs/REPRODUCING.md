# Reproducing the computational packages

> **Documentation status:** implementer-prepared source inventory, 2026-11-13. The creator's revised draft was not available in the repository tree or current conversation files. Commands below are copied verbatim from README files actually present in the repository. No command is presented as executed in this documentation stage.

## How to read the records

- **README transcription** means the command is copied from the cited README and has not been executed in this documentation stage.
- **[COMMAND NOT VERIFIED]** means the requested command could not be transcribed from the original package README available to this implementation. No command has been inferred from a script filename.
- No entry below is labelled **reproduced**.
- For every command transcription, execution date, executor, and execution method are recorded as **not applicable / not executed** for this stage. Historical archive-integrity checks are distinguished from running a scientific simulation or test suite.

## README-sourced commands

| Package / task | Command copied verbatim | README source and line | Execution date | Executed by | Method / status |
|---|---|---|---|---|---|
| v0.5C — install dependencies | `python -m pip install numpy scipy` | `v0.5C/source/v0_5c/README.md`, line 18 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v0.5C — full reproduction | `python reproduce_all_v05c.py --full` | `v0.5C/source/v0_5c/README.md`, line 19 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v0.5C — quick test (2 replications) | `python reproduce_all_v05c.py` | `v0.5C/source/v0_5c/README.md`, line 22 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.7-L — L1–L3 audit | `python auditar_L1_L3.py` | `v1.7/source/README.md`, line 8 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.7-L — unit tests | `python -m unittest test_limites.py -v` | `v1.7/source/README.md`, line 9 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.8A — unit tests | `python -m unittest -q test_v18a.py` | `v1.8A/source/README_REPRODUCAO.md`, line 9 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.8A — primary simulation batch | `python kafka_v18a_map.py --reps 400 --seed 18082026 --output outputs_recheck` | `v1.8A/source/README_REPRODUCAO.md`, line 12 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.8A — additional exploratory check | `python kafka_v18a_map.py --reps 400 --seed 18182026 --output outputs_replication_recheck` | `v1.8A/source/README_REPRODUCAO.md`, line 15 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.8A — descriptive post-hoc map | `python posthoc_mapa_zonas.py` | `v1.8A/source/README_REPRODUCAO.md`, line 18 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.9D — enter package directory | `cd kafka_iii_v1_9d` | `v1.9D/source/README.md`, line 22 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.9D — experiment | `python experiment_v1_9d.py > run_log.json` | `v1.9D/source/README.md`, line 23 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.9D — independent tests | `python test_independent.py > independent_tests_log.txt` | `v1.9D/source/README.md`, line 24 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |
| v1.9F — baseline-equivalence audit | `python audit_baseline_v1_9f.py` | `v1.9F/source/README.md`, line 10 | NOT EXECUTED in this stage | Not applicable | Verbatim README transcription only |

## Required v1.9E commands — not verified

The task requests the package README commands for `test_v1_9e.py` and `check_reproducibility.py`. The complete v1.9E ZIP is present at the repository root, but the current `v1.9E/` directory is not expanded. Its tracked README states that the full archive has not been expanded into the directory (see `v1.9E/README.md`, lines 3 and 12–14). The package-internal README could not be inspected from the current tree.

| Requested item | Command field | README origin | Execution date | Executed by | Method / status |
|---|---|---|---|---|---|
| v1.9E test suite (`test_v1_9e.py`) | **[COMMAND NOT VERIFIED]** | Package-internal README not available in the tracked tree; ZIP not expanded for this inspection | NOT VERIFIED | NOT VERIFIED | No command inferred from the filename |
| v1.9E reproducibility check (`check_reproducibility.py`) | **[COMMAND NOT VERIFIED]** | Package-internal README not available in the tracked tree; ZIP not expanded for this inspection | NOT VERIFIED | NOT VERIFIED | No command inferred from the filename |

## Packages with no command verified in an available README

| Package | Source checked | Result |
|---|---|---|
| v0.4 | `v0.4/README.md`, lines 1–8 | No execution command is documented there. **[COMMAND NOT VERIFIED]** |
| Comparison v0.2 | No original package README is present in the current tracked tree | **[COMMAND NOT VERIFIED]**; source README unavailable |

## Working-directory notes taken from the README text

- v0.5C: the README says to enter the `v0_5c` directory (line 15) before running the commands.
- v1.7-L: the README describes commands to execute with Python 3 (line 5); it does not specify an explicit `cd` command.
- v1.8A: the README lists the commands under “Reproduzir”; no additional directory-change command is specified in that section.
- v1.9D: the README explicitly includes `cd kafka_iii_v1_9d` (line 22).
- v1.9F: the README says “Na pasta do pacote” (line 7).

No working directory has been inferred from a script name.

## Execution and verification boundary

No v0.5C, v1.7-L, v1.8A, v1.9D, v1.9E, or v1.9F simulation/test command was run by the implementer on 2026-11-13 as part of creating this file. These rows are README transcriptions, not execution records.

A separate preflight audit file in the conversation records archive-integrity checks on 2026-11-12: ZIP integrity testing with `unzip -t` and SHA-256 comparisons for the supplied archives. Those checks are archive-integrity checks only; they are not evidence that any simulation or test command above was run in this stage. No scientific result was changed or regenerated.
