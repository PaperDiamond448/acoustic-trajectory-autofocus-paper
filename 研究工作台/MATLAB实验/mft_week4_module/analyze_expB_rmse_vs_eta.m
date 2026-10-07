function analyze_expB_rmse_vs_eta(outdir)
%ANALYZE_EXPB_RMSE_VS_ETA  POST HOC, exploratory.
%
%   Experiment A shows by construction that a smaller frequency RMSE need not
%   give a higher coherent efficiency.  This script asks whether the two
%   indicators also move in different directions when a real estimator and a
%   real optimiser run on noisy simulated records: per record it compares the
%   change in the effective frequency RMSE with the change in coherence
%   efficiency across the refinement module.
%
%   What it establishes: the two indicators disagree on most records.
%   What it does NOT establish: any quantified mechanism of phase-error
%   redistribution.  The batch stores no per-record trajectory, so no
%   demeaning or temporal-correlation decomposition of the error is possible
%   here, and none is claimed.
%
%   Definitions (as in evaluate_record.m): rmse_eff compares ghat + nu_peak
%   with the truth, where nu_peak is the residual peak chosen on the NOISY
%   observation; eta_max maximises the compensated pure-target component over
%   the residual frequency.
%
%   Pooled intervals resample the record_id, carrying its three SNR versions.
if nargin < 1 || isempty(outdir), outdir = fullfile(pwd,'results','expB'); end
NBC = 20000;  CSEED = 2026091805;

T   = readtable(fullfile(outdir,'expB_raw.csv'), 'TextType','string');
ids = unique(T.record_id);
SD  = cluster_draws(ids, NBC, CSEED);
brs = ["viterbi_b2","suv"];
rows = {};
for b = brs
    R  = T(T.branch==b,:);
    M  = cluster_map(R.record_id, ids);
    dr = R.rmse_eff_out_hz - R.rmse_eff_in_hz;   % Hz, positive = RMSE got worse
    de = R.d_eta;                                 % positive = coherence improved
    both = dr > 0 & de > 0;
    bm = zeros(NBC,1);  bb = zeros(NBC,1);
    for k = 1:NBC
        ix = reshape(M(SD(k,:),:).', [], 1);
        bm(k) = median(dr(ix));
        bb(k) = mean(both(ix));
    end
    rows(end+1,:) = {char(b), numel(ids), height(R), ...
        median(R.rmse_eff_in_hz), median(R.rmse_eff_out_hz), median(dr), ...
        pctl(bm,0.025), pctl(bm,0.975), mean(dr > 0), ...
        mean(both), pctl(bb,0.025), pctl(bb,0.975), ...
        spearman(dr, de)}; %#ok<AGROW>
end
D = cell2table(rows, 'VariableNames', {'branch','n_clusters','n_snr_versions', ...
    'rmse_in_median_hz','rmse_out_median_hz','d_rmse_median_hz','d_rmse_lo95', ...
    'd_rmse_hi95','frac_rmse_worse','frac_rmse_worse_and_eta_better', ...
    'frac_both_lo95','frac_both_hi95','spearman_drmse_deta'});
D.branch = string(D.branch);
writetable(D, fullfile(outdir,'expB_rmse_vs_eta_posthoc.csv'));

fprintf('\n--- POST HOC: the two indicators move in different directions ---\n');
disp(D(:,{'branch','d_rmse_median_hz','d_rmse_lo95','d_rmse_hi95', ...
          'frac_rmse_worse','frac_rmse_worse_and_eta_better','frac_both_lo95','frac_both_hi95'}));
fprintf(['Positive d_rmse means the effective frequency RMSE increased across the\n' ...
         'module while the coherence efficiency improved.  The Spearman value is a\n' ...
         'between-record association, not a within-record mechanism.\n']);
end

function r = spearman(x, y)
%SPEARMAN  Rank correlation with mid-ranks for ties; no toolbox dependency.
rx = midrank(x(:));  ry = midrank(y(:));
rx = rx - mean(rx);  ry = ry - mean(ry);
r  = (rx.'*ry)/sqrt((rx.'*rx)*(ry.'*ry));
end

function r = midrank(v)
n = numel(v);
[s, o] = sort(v);
r = zeros(n,1);
i = 1;
while i <= n
    j = i;
    while j < n && s(j+1) == s(i), j = j + 1; end
    r(o(i:j)) = (i + j)/2;
    i = j + 1;
end
end
