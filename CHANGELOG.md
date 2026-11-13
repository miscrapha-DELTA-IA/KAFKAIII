# Changelog

## 2026-11-13 — Deposit and verify manuscript v0.3.11

### Manuscript files

- Moved `manuscript_v0_3_11.md` to `paper/manuscript_v0_3_11.md`.
  - Uploaded-file SHA-256 before the path-only adjustment: `614184a1a658dd474f9777d9cb6c824e5f78fd0aa41034e33bffc0f996ee2f85`.
  - SHA-256 after changing the two relative image references from `figs/` to `figures/`: `04118895910592c0471b2842ce46151db10b0e2f1d0ffe6dd1c7a233647436b0`.
  - No scientific text, estimates, tables, numerical values, or conclusions were changed.
- Moved `manuscript_v0_3_11.docx` to `paper/manuscript_v0_3_11.docx` without changing its bytes.
  - SHA-256 before and after the move: `def3e37ec40335c206ac27fd0262ad6e600698b068d1ccaf3913490554f42bd4`.

### Figure assets

The root uploads `figure1_paired_contrasts.png` and `figure2_frontier.png` were byte-identical to the files already stored under `paper/figures/`. Their SHA-256 values are:

- Figure 1: `97d636344cba912cb38e03e9577bc24018ceb4c09ac9d7bc179f672157be7146`.
- Figure 2: `63cd396aafd34355e6a6e238cbd34a1040c56737ede2e398edf92adc72da0ad6`.

The existing canonical copies in `paper/figures/` were retained unchanged. The additional root copies were left untouched in this deposit.

### v1.9E archive and manifest

- Kept `KAFKA_III_V1_9E_PACOTE_COMPLETO (1).zip` under its exact cited filename; no rename was performed.
- Recalculated archive SHA-256: `fc220245bf4e0645446bc85a9475b22ad115d6afcc077b36d8e6b2685b192026`. This matches the hash supplied for the manuscript citation.
- The previous repository manifest SHA-256 was `6aacae06993b0dde38d40a80969e748fe7639276177f302856881abf1e55e57c`. It did not contain an entry for the v1.9E root ZIP or the newly uploaded manuscript files.
- The regenerated manifest records the v1.9E archive under the exact path above, as well as the manuscript files and other tracked assets. The manifest intentionally excludes itself; its resulting file hash is therefore reported in the repository verification rather than embedded in this changelog.

### Scope

No protected source code, registered protocol, ZIP contents, result tables, or scientific conclusions were changed. No simulation or unit test was executed as part of this documentation and file-organization update.
