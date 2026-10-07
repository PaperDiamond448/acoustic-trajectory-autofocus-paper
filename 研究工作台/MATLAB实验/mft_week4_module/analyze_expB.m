function analyze_expB(outdir, week2_csv, neighbour_csv)
%ANALYZE_EXPB  Summarise the cross-front-end refinement experiment.
%
%   Primary quantity: the per-record module-entry -> module-exit increment
%   d_eta inside each branch.  Reported per SNR with a paired bootstrap CI of
%   the median and the Wilson interval of the improved fraction.
%
%   Two provenance checks are run first:
%     (1) branch 1 against the frozen week-2 B2 / P60 results;
%     (2) branch 2 entry against the frozen week-3 neighbour results.
%   Both should agree to numerical round-off; any deviation is reported, not
%   absorbed.
root = fileparts(pwd);
if nargin < 1 || isempty(outdir), outdir = fullfile(pwd,'results','expB'); end
if nargin < 2 || isempty(week2_csv)
    week2_csv = fullfile(root,'mft_week2','results','main','trial_results.csv');
end
if nargin < 3 || isempty(neighbour_csv)
    neighbour_csv = fullfile(root,'mft_week3_neighbour_fix','results','compare','neighbour_raw.csv');
end
rng(20260918,'twister');                      % per-SNR bootstrap seed, fixed before the run
NB    = 2000;
NBC   = 20000;                                % pooled cluster bootstrap
CSEED = 2026091805;                           % shared with the independent recheck
BTOL  = 1e-6;                                 % |u_p| >= 1 - BTOL counts as an active bound

T = readtable(fullfile(outdir,'expB_raw.csv'), 'TextType','string');
snrs = unique(T.snr_db).';
brs  = ["viterbi_b2","suv"];

% ---------------- provenance check 1: branch 1 vs week 2 ------------------
chk = struct('week2_csv',week2_csv,'neighbour_csv',neighbour_csv);
if exist(week2_csv,'file')
    W = readtable(week2_csv, 'TextType','string');
    W = W(W.phase=="h1_test" & W.scene=="S2" & ismember(W.snr_db, snrs) & ...
          W.record_id <= max(T.record_id) & ismember(W.method,["B2","P60"]), :);
    b1  = T(T.branch=="viterbi_b2",:);
    kin = key(b1.snr_db, b1.record_id);
    WB  = W(W.method=="B2",:);   WP = W(W.method=="P60",:);
    [~, ia, ib] = intersect(kin, key(WB.snr_db, WB.record_id));
    chk.n_matched_b2 = numel(ia);
    chk.max_absdiff_eta_in = max(abs(b1.eta_in(ia) - WB.eta_max(ib)));
    [~, ia, ib] = intersect(kin, key(WP.snr_db, WP.record_id));
    chk.n_matched_p60 = numel(ia);
    chk.max_absdiff_eta_out = max(abs(b1.eta_out(ia) - WP.eta_max(ib)));
else
    chk.n_matched_b2 = 0; chk.n_matched_p60 = 0;
    chk.max_absdiff_eta_in = NaN; chk.max_absdiff_eta_out = NaN;
end

% ---------------- provenance check 2: branch 2 entry vs week 3 ------------
if exist(neighbour_csv,'file')
    S = readtable(neighbour_csv, 'TextType','string');
    S = S(S.phase=="h1_test" & S.scene=="S2" & ismember(S.snr_db, snrs) & ...
          S.record_id <= max(T.record_id), :);
    b2 = T(T.branch=="suv",:);
    [~, ia, ib] = intersect(key(b2.snr_db,b2.record_id), key(S.snr_db,S.record_id));
    chk.n_matched_suv = numel(ia);
    chk.max_absdiff_eta_suv_entry = max(abs(b2.eta_in(ia) - S.eta_max(ib)));
else
    chk.n_matched_suv = 0; chk.max_absdiff_eta_suv_entry = NaN;
end
chk.tolerance = 1e-12;
chk.branch1_reproduces_week2 = chk.max_absdiff_eta_in <= chk.tolerance && ...
                               chk.max_absdiff_eta_out <= chk.tolerance;
chk.branch2_entry_reproduces_week3 = chk.max_absdiff_eta_suv_entry <= chk.tolerance;
fid = fopen(fullfile(outdir,'expB_consistency.json'),'w');
fprintf(fid,'%s', jsonencode(chk,'PrettyPrint',true)); fclose(fid);

% ---------------- per-SNR summary ----------------------------------------
rows = {};
for b = brs
    for q = snrs
        R = T(T.branch==b & T.snr_db==q, :);
        d = R.d_eta;  nrec = height(R);
        bs = zeros(NB,1);
        for k = 1:NB, bs(k) = median(d(randi(nrec, nrec, 1))); end
        kimp = sum(d > 0);
        [wl, wh] = wilson_interval(kimp, nrec);
        rows(end+1,:) = { char(b), q, nrec, ...
            median(R.eta_in), median(R.eta_out), median(d), ...
            pctl(bs,0.025), pctl(bs,0.975), pctl(d,0.25), pctl(d,0.75), ...
            mean(d), kimp/nrec, wl, wh, ...
            median(R.rmse_eff_in_hz), median(R.rmse_eff_out_hz), ...
            median(R.coverage_in), median(R.coverage_out), ...
            mean(R.fallback), mean(R.hard_fail), mean(R.all_stages_capped), ...
            median(R.max_abs_u), median(R.t_refine_s), median(R.t_entry_s) }; %#ok<AGROW>
    end
end
S1 = cell2table(rows, 'VariableNames', {'branch','snr_db','n', ...
    'eta_in_median','eta_out_median','d_eta_median','d_eta_lo95','d_eta_hi95', ...
    'd_eta_q25','d_eta_q75','d_eta_mean','frac_improved','frac_improved_lo95', ...
    'frac_improved_hi95','rmse_eff_in_median_hz','rmse_eff_out_median_hz', ...
    'coverage_in_median','coverage_out_median','fallback_rate','hard_fail_rate', ...
    'all_stages_capped_rate','max_abs_u_median','t_refine_median_s','t_entry_median_s'});
S1.branch = string(S1.branch);
writetable(S1, fullfile(outdir,'expB_summary.csv'));

% ---------------- pooled paired table, CLUSTER bootstrap ------------------
% Post-run statistical correction (2026-09-18): the three SNR levels of one
% record_id are three amplitude versions of ONE realisation, so the pooled
% statistics resample the record_id and carry its versions together.  The
% per-SNR cells above are unaffected.
ids = unique(T.record_id);
SD  = cluster_draws(ids, NBC, CSEED);
prows = {};
for b = brs
    R  = T(T.branch==b, :);
    M  = cluster_map(R.record_id, ids);
    d  = R.d_eta;  nrec = height(R);
    bm = zeros(NBC,1);  bf = zeros(NBC,1);
    for k = 1:NBC
        ix = reshape(M(SD(k,:),:).', [], 1);
        bm(k) = median(d(ix));
        bf(k) = mean(d(ix) > 0);
    end
    % "at least one active amplitude bound", tolerance stated explicitly.
    % This means SOME coefficient reached |u_p| = 1, not that the whole
    % correction sits at +-delta f_max.
    nbound = sum(R.max_abs_u >= 1 - BTOL);
    prows(end+1,:) = {char(b), numel(ids), nrec, median(R.eta_in), median(R.eta_out), ...
        median(d), pctl(bm,0.025), pctl(bm,0.975), sum(d>0)/nrec, ...
        pctl(bf,0.025), pctl(bf,0.975), sum(d<0)/nrec, ...
        nbound, BTOL, sum(R.fallback), sum(R.hard_fail), min(d), ...
        median(R.coverage_in), median(R.coverage_out), ...
        median(R.rmse_eff_in_hz), median(R.rmse_eff_out_hz)}; %#ok<AGROW>
end
P1 = cell2table(prows, 'VariableNames', {'branch','n_clusters','n_snr_versions', ...
    'eta_in_median','eta_out_median','d_eta_median','d_eta_lo95','d_eta_hi95', ...
    'frac_improved','frac_improved_lo95','frac_improved_hi95','frac_worse', ...
    'n_active_bound','bound_tolerance','n_initial_kept','n_hard_fail','d_eta_min', ...
    'coverage_in_median','coverage_out_median','rmse_eff_in_median_hz', ...
    'rmse_eff_out_median_hz'});
P1.branch = string(P1.branch);
writetable(P1, fullfile(outdir,'expB_paired.csv'));

% ---- branch-to-branch comparison of the EXIT coherence, paired on record --
Pv = {};
for q = snrs
    a = T(T.branch=="viterbi_b2" & T.snr_db==q,:);
    c = T(T.branch=="suv"        & T.snr_db==q,:);
    [~, ia, ib] = intersect(a.record_id, c.record_id);
    dd = c.eta_out(ib) - a.eta_out(ia);  m = numel(dd);
    bs = zeros(NB,1);
    for k = 1:NB, bs(k) = median(dd(randi(m, m, 1))); end
    Pv(end+1,:) = {q, m, median(dd), pctl(bs,0.025), pctl(bs,0.975), mean(dd>0)}; %#ok<AGROW>
end
P2 = cell2table(Pv, 'VariableNames', {'snr_db','n','suv_exit_minus_viterbi_exit_median', ...
    'lo95','hi95','frac_suv_exit_higher'});
writetable(P2, fullfile(outdir,'expB_exit_comparison.csv'));

% ---------------- supplementary: increment vs entry quality ---------------
qrows = {};
for b = brs
    R = T(T.branch==b, :);
    e = [0 pctl(R.eta_in,0.25) pctl(R.eta_in,0.50) pctl(R.eta_in,0.75) inf];
    for k = 1:4
        m = R.eta_in >= e(k) & R.eta_in < e(k+1);
        if ~any(m), continue; end
        qrows(end+1,:) = {char(b), k, e(k), e(k+1), sum(m), ...
            median(R.eta_in(m)), median(R.d_eta(m)), mean(R.d_eta(m) > 0), ...
            median(R.coverage_in(m))}; %#ok<AGROW>
    end
end
Q = cell2table(qrows, 'VariableNames', {'branch','entry_quartile','eta_in_lo', ...
    'eta_in_hi','n','eta_in_median','d_eta_median','frac_improved','coverage_in_median'});
writetable(Q, fullfile(outdir,'expB_by_entry_quality.csv'));

fprintf('\n--- provenance checks ---\n');
fprintf('branch 1 vs week 2 : n=%d/%d, max|d eta_in|=%.3e, max|d eta_out|=%.3e -> reproduces=%d\n', ...
    chk.n_matched_b2, chk.n_matched_p60, chk.max_absdiff_eta_in, chk.max_absdiff_eta_out, ...
    chk.branch1_reproduces_week2);
fprintf('branch 2 entry vs week 3 : n=%d, max|d eta|=%.3e -> reproduces=%d\n', ...
    chk.n_matched_suv, chk.max_absdiff_eta_suv_entry, chk.branch2_entry_reproduces_week3);
fprintf('\n--- per SNR ---\n');
disp(S1(:,{'branch','snr_db','n','eta_in_median','eta_out_median','d_eta_median', ...
           'd_eta_lo95','d_eta_hi95','frac_improved'}));
fprintf('\n--- pooled over the three SNRs (cluster bootstrap on record_id) ---\n');
disp(P1(:,{'branch','n_clusters','n_snr_versions','d_eta_median','d_eta_lo95', ...
           'd_eta_hi95','frac_improved','frac_improved_lo95','frac_improved_hi95'}));
cross_check_pooled(P1, outdir);
fprintf('\n--- exit coherence, SUV branch minus Viterbi branch ---\n'); disp(P2);
fprintf('\n--- increment by entry quality ---\n'); disp(Q);
end

function k = key(a, b)
k = a(:)*1e6 + b(:);
end

function cross_check_pooled(P1, outdir)
%CROSS_CHECK_POOLED  Compare the MATLAB cluster bootstrap with the independent
%   Python recheck delivered in CSSP补充实验复核_20260918.  The two use
%   different RNG streams, so the endpoints are expected to agree only to
%   Monte Carlo accuracy; the point estimates must agree exactly.
ref = fullfile(fileparts(fileparts(pwd)), ...
    'CSSP补充实验复核_20260918','pooled_cluster_corrected.csv');
if ~exist(ref,'file')
    fprintf('(reference recheck CSV not found, cross-check skipped)\n'); return
end
R = readtable(ref, 'TextType','string');
R = R(R.metric=="d_eta", :);
rows = {};
for i = 1:height(P1)
    j = find(R.branch == P1.branch(i), 1);
    if isempty(j), continue; end
    rows(end+1,:) = {char(P1.branch(i)), ...
        abs(P1.d_eta_median(i) - R.estimate(j)), ...
        abs(P1.d_eta_lo95(i)   - R.lo95(j)), ...
        abs(P1.d_eta_hi95(i)   - R.hi95(j))}; %#ok<AGROW>
end
C = cell2table(rows,'VariableNames',{'branch','absdiff_estimate','absdiff_lo95','absdiff_hi95'});
writetable(C, fullfile(outdir,'expB_pooled_crosscheck.csv'));
fprintf('\ncross-check vs independent Python recheck (different RNG stream):\n');
disp(C);
end
