# E0 phase-correction delivery

This folder contains the audit, corrected E0 simulation outputs, unchanged REAL-window table, report, and source snapshots. It covers E0 only. The raw SWellEx file is not included; corrected E0 SIM replay uses frozen simulation seeds and does not need the real recording.

## Reproduction

Run in MATLAB R2023a from `D:\论文集` with the source folders below available (source snapshots are included here):

1. `run_E0_phase_audit.m` — replays only fixed representative record 38 and checks direct/residual phase equivalence.
2. `run_E0_phase_corrected.m` — replays the original 400 SIM/SIM-S2 seeds; checks frequency and error-decomposition results against the frozen pre-fix CSV before calculating corrected coherence metrics.
3. `run_E0_phase_corrected_stratified.m` — paired contrasts and within-scene/estimator correlations from the corrected per-record CSV.
4. `make_E0_phase_corrected_figure.m` — plot-only regeneration.

The source snapshot is under `source_snapshot/mft_week4_module`. The scripts also expect the original project folders and `phaseA/tables/E0_sim_residual_perrecord.csv` at their configured paths. The `tables/legacy_*` files show the pre-fix statistics and should not be combined with corrected values.

## Contents

- `REPORT_E0_phase_correction_20260925.md`: findings, definitions, self-check, corrected results, and limitations.
- `tables/E0_phase_corrected_perrecord.csv`: 800 estimator rows from 400 paired records.
- `tables/E0_phase_corrected_summary.csv`, `*_by_method.csv`, `*_stratified.csv`, and `*_method_correlations.csv`: aggregate statistics.
- `tables/E0_REAL_reference_only.csv`: unchanged 31 overlapping REAL-window rows; reference trajectory is not phase truth.
- `source_snapshot/mft_week4_module`: generator, configuration, front end, estimators, and supporting functions used for SIM replay.
- `legacy/run_E0_paired.m`: historical pre-fix script preserved for audit only.

No A7–A10, BTA, or Phase C work is included in this correction run.
