function run_expB_crossfrontend(outdir, nworkers, ids, snrs)
%RUN_EXPB_CROSSFRONTEND  Cross-front-end test of the coherent refinement module.
%
%   Protocol MFT-W4-MODULE-20260918, section 2 of PREREGISTRATION_W4.md.
%   Prespecified records: scene S2, SNR {-18,-17,-16} dB, record_id 1:100,
%   phase h1_test -- the SAME observations as the week-2 main batch and the
%   week-3 neighbour batch (identical seed formula, identical generator).
%
%   Two branches share ONE optimiser (estimate_refine.m, budget cfg.M.P) but
%   differ in what defines the feasible neighbourhood and where it starts:
%
%     branch 1 (existing) : centre = B1 (Viterbi) trajectory, u0 = u_B2
%     branch 2 (new)      : centre = SUV trajectory,          u0 = 0
%
%   The two feasible sets are NOT the same and this is not claimed anywhere.
%   The primary quantity is the per-record module-entry -> module-exit
%   increment of the coherence efficiency inside each branch.
if nargin < 1 || isempty(outdir),   outdir   = fullfile(pwd,'results','expB'); end
if nargin < 2 || isempty(nworkers), nworkers = 8; end
if ~exist(outdir,'dir'), mkdir(outdir); end
cfg = mft_config();  B = cfg.B;  M = cfg.M;
s   = suvorova_config();
ensure_pool(nworkers);

scene = 'S2';
if nargin < 3 || isempty(ids),  ids  = 1:100;        end   % PREREGISTERED
if nargin < 4 || isempty(snrs), snrs = [-18 -17 -16]; end   % PREREGISTERED
jobs = make_jobs(cfg, 'h1_test', {scene}, snrs, ids);
n = numel(jobs);
fprintf('exp B plan: %s, SNR %s dB, record_id 1:%d -> %d records, 2 branches\n', ...
    scene, mat2str(snrs), numel(ids), n);

fcfg = struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine,'band',B.band, ...
              'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
rows = cell(n,1);
t0 = tic;
parfor i = 1:n
    j   = jobs(i);
    rec = simulate_baseband(cfg, j.scene, j.snr_db, j.seed, 'eval');
    y = rec.y;  t = rec.t;
    evalIdx = find(t >= B.eval_s(1) & t < B.eval_s(2));
    tic; fe = common_frontend(y, t, fcfg); t_fe = toc;

    % ---------------- branch 1: Viterbi -> continuous init -> refinement -----
    tic; o1 = estimate_b1(fe, M.B1); t_b1 = toc;
    tic; fam1 = build_family(t, fe.tc, o1.g, M.B2); t_fam1 = toc;
    tic; o2 = estimate_b2(fe, fam1, M.B2); t_b2 = toc;
    tic; r1 = estimate_refine(y, fe, fam1, o2.u, evalIdx, M.P); t_r1 = toc;
    m_in1  = evaluate_record(y, t, o2.g, evalIdx, fe.noise_hat, rec.truth, B);
    m_out1 = evaluate_record(y, t, r1.g, evalIdx, fe.noise_hat, rec.truth, B);

    % ---------------- branch 2: SUV -> same refinement ----------------------
    tic; oS = estimate_suvorova(y, t, fe.noise_hat, s, evalIdx); t_suv = toc;
    % The SUV read-out is piecewise linear on the MID-points between block
    % centres (estimate_suvorova.m, 'phase_refined' branch), with constant
    % extension outside.  Those are the breakpoints that must enter the band
    % constraint, not the Viterbi frame centres.
    tb    = oS.t_block(:);
    tcS   = 0.5*(tb(1:end-1) + tb(2:end));
    tic; fam2 = build_family(t, tcS, oS.g, M.B2); t_fam2 = toc;
    u0    = zeros(fam2.P,1);
    tic; r2 = estimate_refine(y, fe, fam2, u0, evalIdx, M.P); t_r2 = toc;
    m_in2  = evaluate_record(y, t, oS.g, evalIdx, fe.noise_hat, rec.truth, B);
    m_out2 = evaluate_record(y, t, r2.g, evalIdx, fe.noise_hat, rec.truth, B);

    base = {j.record_id, j.scene, j.snr_db, j.seed, rec.truth.mean_snr_db, fe.noise_hat};
    rows{i} = [ ...
        [base, {'viterbi_b2', 'B1', 'u_B2'}, brow(m_in1,m_out1,r1,fam1), ...
         {t_fe, t_b1+t_fam1+t_b2, t_r1, NaN}] ; ...
        [base, {'suv',        'SUV','zero'}, brow(m_in2,m_out2,r2,fam2), ...
         {t_fe, t_suv+t_fam2, t_r2, oS.score}] ];
end
el = toc(t0);

C = vertcat(rows{:});
T = cell2table(C, 'VariableNames', expB_columns());
for v = {'scene','branch','centre','init'}, T.(v{1}) = string(T.(v{1})); end
T.selected = string(T.selected);
writetable(T, fullfile(outdir,'expB_raw.csv'));

meta = struct('protocol','MFT-W4-MODULE-20260918','scene',scene,'snr_db',snrs, ...
    'record_ids',[ids(1) ids(end)],'n_records',n,'n_rows',height(T), ...
    'seconds',el,'seconds_per_record',el/n,'workers',nworkers, ...
    'solver_config',M.P,'family_config',M.B2,'suvorova_config',s, ...
    'branch1','centre = B1 Viterbi trajectory, u0 = u_B2 (unchanged from the main experiment)', ...
    'branch2','centre = SUV phase-refined trajectory, u0 = 0, breakpoints = SUV block mid-points', ...
    'note','feasible sets differ between branches by construction; the optimiser is the same function');
fid = fopen(fullfile(outdir,'expB_meta.json'),'w');
fprintf(fid,'%s', jsonencode(meta,'PrettyPrint',true)); fclose(fid);
fprintf('exp B: %d records x 2 branches in %.1f s (%.2f s per record, %d workers)\n', ...
    n, el, el/n, nworkers);
end

function c = brow(min_, mout_, r, fam)
%BROW  Entry / exit metrics of one branch on one record.
c = {min_.eta_max, mout_.eta_max, mout_.eta_max - min_.eta_max, ...
     min_.rmse_eff, mout_.rmse_eff, min_.coverage_active, mout_.coverage_active, ...
     min_.Z_db, mout_.Z_db, min_.nu_peak, mout_.nu_peak, ...
     r.selected, double(r.fallback), double(r.hard_fail), ...
     r.J_init, r.J_best, double(r.all_stages_capped), ...
     max(abs(r.u)), fam.r};
end

function c = expB_columns()
c = {'record_id','scene','snr_db','seed','mean_snr_db','noise_hat', ...
     'branch','centre','init', ...
     'eta_in','eta_out','d_eta','rmse_eff_in_hz','rmse_eff_out_hz', ...
     'coverage_in','coverage_out','Z_db_in','Z_db_out','nu_peak_in','nu_peak_out', ...
     'selected','fallback','hard_fail','J_init','J_best','all_stages_capped', ...
     'max_abs_u','radius_hz','t_frontend_s','t_entry_s','t_refine_s','suv_score'};
end
