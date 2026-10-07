function analyze_expB_matched(outdir, lo, hi)
%ANALYZE_EXPB_MATCHED  POST HOC, exploratory, kept in the supplement only.
%
%   The two branches enter the module at different trajectory quality, so this
%   restricts both to a common entry band and recomputes the increment there.
%
%   Two cautions that the table must carry with it:
%     * this is NOT entry-quality matching.  Inside the band the two entry
%       medians are still different and the two record sets are different, so
%       no share of the branch difference may be attributed to entry quality.
%     * the band was chosen after seeing the entry distributions.
%
%   Resampling: record_ids are drawn FIRST, carrying all three SNR versions,
%   and the [lo,hi] condition is applied to the drawn versions afterwards.
%   Resampling the already-filtered rows would treat selection as fixed.
if nargin < 1 || isempty(outdir), outdir = fullfile(pwd,'results','expB'); end
if nargin < 2 || isempty(lo), lo = 0.45; end
if nargin < 3 || isempty(hi), hi = 0.75; end
NBC = 20000;  CSEED = 2026091805;

T   = readtable(fullfile(outdir,'expB_raw.csv'), 'TextType','string');
ids = unique(T.record_id);
SD  = cluster_draws(ids, NBC, CSEED);
brs = ["viterbi_b2","suv"];
rows = {};
for b = brs
    R = T(T.branch==b,:);
    M = cluster_map(R.record_id, ids);
    sel = R.eta_in >= lo & R.eta_in <= hi;
    d = R.d_eta;
    bm = nan(NBC,1);
    for k = 1:NBC
        ix = reshape(M(SD(k,:),:).', [], 1);
        ix = ix(sel(ix));                       % condition applied AFTER the draw
        if ~isempty(ix), bm(k) = median(d(ix)); end
    end
    bm = bm(isfinite(bm));
    nsel = sum(sel);
    rows(end+1,:) = {char(b), lo, hi, nsel, height(R), ...
        numel(unique(R.record_id(sel))), ...
        median(R.eta_in(sel)), median(R.eta_out(sel)), median(d(sel)), ...
        pctl(bm,0.025), pctl(bm,0.975), mean(d(sel)>0), ...
        median(R.coverage_in(sel))}; %#ok<AGROW>
end
M2 = cell2table(rows, 'VariableNames', {'branch','eta_in_lo','eta_in_hi', ...
    'n_versions','n_total','n_clusters_with_selected_rows','eta_in_median', ...
    'eta_out_median','d_eta_median','d_eta_lo95','d_eta_hi95','frac_improved', ...
    'coverage_in_median'});
M2.branch = string(M2.branch);
writetable(M2, fullfile(outdir,'expB_matched_entry_posthoc.csv'));

fprintf('\n--- POST HOC (supplement): both branches restricted to eta_in in [%.2f, %.2f] ---\n', lo, hi);
disp(M2(:,{'branch','n_versions','n_clusters_with_selected_rows','eta_in_median', ...
           'd_eta_median','d_eta_lo95','d_eta_hi95','frac_improved'}));
fprintf(['Entry medians inside the band still differ (%.3f vs %.3f) and the record\n' ...
         'sets differ, so this is a common-band description, not quality matching.\n'], ...
         M2.eta_in_median(1), M2.eta_in_median(2));
end
