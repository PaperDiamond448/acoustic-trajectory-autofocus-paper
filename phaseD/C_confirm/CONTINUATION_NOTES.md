# FINAL — Confirmation complete; STOP POINT 2

All 2,800 phase-52 records / 14,000 method rows completed. C-A1: P1/P2/P3/S1 all PASS. Primary method ADA_local_c04_t30_A. DO NOT rerun the numerical batch and DO NOT start X1–X3 without later explicit user release of stop point 2. All former exec sessions have completed.

Read CONFIRM_REPORT.md, CONFIRM_DECISION.json, FINAL_STATUS.json and audits. All inputs, old development outputs and protected sources unchanged. Native reconstruction max metric/track difference 0; CSV/MAT reconciliation max difference 4.97e-14; independent bootstrap decisions PASS; both Nature figures automatic and visual QA PASS.

Numerical MATLAB process reported heap corruption AFTER all chunks, CSV and final config were saved. Separate read-only native processes exited normally; no optimizer retries. Incident fully disclosed and validated in ENVIRONMENT_EXIT_INCIDENT.json. S0 still has an eta cost relative to UNB; P2 passed on the preregistered pooled unit.

Final archive: phaseD/PhaseD_停止点2_核对包_20261004.zip. Full MATLAB chunks stay local under C_confirm/chunks.

---

Historical in-progress notes below are retained for traceability and are superseded by the final state above.

# Phase C ongoing handoff

User independently audited stop point 1 and explicitly authorized confirmation C on 2026-10-04. Run C to completion, deliver `CONFIRM_REPORT.md`, then stop at stop point 2. Do NOT run X1–X3.

Scientific run is active in exec session **77390** (PowerShell launching MATLAB R2023a). Six Processes workers, chunk size 10. Poll via write_stdin with 50,000 ms and concise output; use at most 60-second waits, maintain Chinese progress commentary. State is `C_confirm/run_status.json`; numerical chunks under `C_confirm/chunks`.

At first handoff writing, 230/2800 records finished (~855 seconds). Estimated total about 3 hours, varying by scene. Do not analyze intermediate gains or change methods.

New files are `codeC/phaseC_record52.m`, `phaseC_one.m`, `run_phaseC_confirm.m`, `preflight_phaseC.m`. Preflight PASS, interfaces bitwise equivalent to independently generated phase-52 inputs. Source manifest `codeC/SOURCE_MANIFEST_C_sha256.csv` is immutable during numerical run and includes original 120 dependencies plus new numeric interfaces, authorization, figure contract, stop-1 audit and gates. It does not include subsequently written postprocess scripts. All stop-1 outputs protected in `C_confirm/PROTECTED_STOP1_sha256.csv`.

Frozen method exact SHA ff63f32c38fc17e99620faa074025c337df247bf823be4fa4b40e74860c0a89f. Method ADA_local_c04_t30_A; Delta=10, P=31; lambda_C=.005151315789473684, lambda_F=.5151315789473684; budgets 354/1476 each of three stages 20/60/290; local .04 cap, 30-s trigger, full rerun A. New phase52 records: S0/S2 × -20:-14 dB × ids1:200; each has SMR/F02/F04/UNB/FM. F02 reused exactly for ADA round0; other solves start same SMR. Original numerical code, D_dev and FROZEN_METHOD remain unchanged.

Postprocessing prepared but not yet run:
- `codeC/audit_phaseC_saved.m`: read-only native audit regenerates all inputs, recomputes all metrics, checks objective candidates, bounds, budgets, local support expansion, previous candidate and no-trigger identity. Writes SAVED_OUTPUTS_AUDIT.json, C_ADA_rounds.csv, C_final_solver_stages.csv. Static check has only array-growth efficiency suggestions. Run MATLAB with addpath original code + codeC; entry `audit_phaseC_saved`.
- `codeC/analyze_phaseC.py`: all primary rules, NumPy PCG64 seed20261052, 2000 replicates, 2×2000×200 clustered arrays carrying7SNR, then14 cell arrays. Writes statistics CSVs, draws.npz, CONFIRM_DECISION.json. Explicit binary masks, no previous CSV bug.
- `codeC/audit_phaseC.py`: independent raw-eta endpoint/bootstrap/cell checks, seed exclusion for dev and E4a (E4a phase33), immutable file hashes; needs native audit JSON. Protects old884, source120, C manifest, allstop1outputs.
- `codeC/plot_phaseC.py`: Nature Figure2.8.0 / Python, two preregistered evidence layouts, exports600dpi PNG/PDF/SVG, strict1.5pt alignment. No development statistics used. Source preflight PASS20, WARN1 TIFF notprovided as optionalformat, zeroFAIL.
- `codeC/audit_phaseC_figures.py`: native Nature font/collision/source/alignment checks with PyMuPDF under phaseD/runtime. Writes qa/FIGURE_QA.json with visual_review pending. MUST view both final PNGs, then set visual_review PASS only after review. If layout collisions fail, fix output layout and re-run plot+QA, document exact output-only change without altering numeric source.
- `codeC/write_confirm_report.py`: needs allabove includingvisualPASS. Writes report rules/numbers/CI/decisions first, then byscene,S1all14cells,FM−SMReta+peakmeanmedianIQR95CIpositivefractions, allmethodgain/harm, secondaries, timing, diagnostics, audit; marks stop2. Handles ambiguous branch “介于两者之间”. Read machineJSON with utf-8-sig.
- `codeC/package_phaseC.py`: compact stop2ZIP andSHA including allCSV/draws/QA/figs/code/scientificdependencies, excludes hugeMATchunks (keptlocal). Refuses overwrite.

Before postprocessing, refresh `codeC/POSTPROCESS_MANIFEST_sha256.csv` to final pre-analysis script SHA values (one read-only E4a seed check was added after its first writing). Preserve new manifest during analysis; if an actual scientific input/rule deviation appears, stop and report user. Routine output-only formatting corrections may proceed with clear record/proof.

Native MATLAB warning at launch: toolbox stats/resources/settingsInfo.json invalid JSON. Do not modify system file. Interface audit passed. Logged as environment warning in IMPLEMENTATION_NOTES.md; no numerical retries or tuning.

Machine saved C_confirm/MACHINE.json: Intel i5-1235U,10 cores12logical,16.8GBRAM,6workers. D free ~78GB. Sourcepath consolelogs may show encoding garble through tools, logfile UTF8 fine.

Skills already reviewed and updated previous turn: Nature pinned commit84880815fb37317b3766bff2c2abba395b8993c3; Figure2.8.0 Python preference. No skill update again, no web, no subagents unless explicitly asked. exec_command requires require_escalated because default Windows sandbox setup fails; all scoped requests accepted. apply_patch writes work despite {} return. Do not ask user for approval again for C; authorization explicit. User currently expects actual completion.

Latest progress update: 2,220/2,800 records; elapsed about 5,923 s. S0 all 1,400 finished; S2 -20/-19/-18/-17 finished; -16 in progress. Active session remains 77390; no scientific result/endpoint has been inspected.

Postprocess manifest was finalized after two BEFORE-ANALYSIS output/audit clarifications: native audit sets maxNumCompThreads(1), recomputes floating metrics/track at 1e-12 tolerance and records actual max differences (saved ADA/F02 identity and input hash still bitwise); plot rows share scene y scales, with harm lower limit applied after both scenes. Original manifests preserved under C_confirm/qa. POSTPROCESS_MANIFEST_sha256.csv now matches all current codeC .m/.py; independent auditor verifies it. Do not refresh or alter it without a precise documented reason.

After numerical session exits successfully, launch native audit and Python analysis independently (can batch calls). Python plot/figure QA follows analysis; independent Python audit follows native audit. View both final PNGs then mark visual_review PASS in qa/FIGURE_QA.json. Generate report and stop2 status, package compact ZIP and validate CRC; final answer must give actual branch, report and ZIP links and clearly stop before X1-X3.
