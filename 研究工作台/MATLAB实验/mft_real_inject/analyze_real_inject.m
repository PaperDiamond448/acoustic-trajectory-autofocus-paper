function out = analyze_real_inject(outdir)
%ANALYZE_REAL_INJECT  Paired eta increments on the measured-background case.
%   Reports per background window and pooled.  No detection probability at a
%   fixed false-alarm rate is produced: this case has no H0 background.
if nargin < 1, outdir = fullfile(pwd,'results','inject'); end
R = real_config();
T = readtable(fullfile(outdir,'real_inject_raw.csv'), 'TextType','string');

%% ---- per cell summary ----
rows = {};
for w = 1:numel(R.win_start_s)
    for q = R.snr_db
        for m = R.methods
            k = T.window==w & T.snr_db==q & T.method==m{1};
            rows(end+1,:) = {R.win_start_s(w), q, m{1}, sum(k), ...
                median(T.eta_max(k)), median(T.rmse_eff_hz(k)), ...
                mean(T.track_success(k)), median(T.Z_db(k))}; %#ok<AGROW>
        end
    end
end
S = cell2table(rows,'VariableNames',{'t0_s','snr_db','method','n','eta_median', ...
    'rmse_eff_median_hz','track_success_rate','Z_median_db'});
writetable(S, fullfile(outdir,'real_inject_summary.csv'));

%% ---- paired increments, same record, P60 - B2 (and B2 - B1) ----
rs = RandStream('mt19937ar','Seed', 20260917);
prow = {};
pairs = {{'P60','B2'}, {'B2','B1'}, {'P60','B1'}};
for p = 1:numel(pairs)
    a = pairs{p}{1}; b = pairs{p}{2};
    for w = [0 1:numel(R.win_start_s)]            % 0 = pooled over windows
        for q = [NaN R.snr_db]                    % NaN = pooled over SNR
            kA = T.method==a; kB = T.method==b;
            if w > 0, kA = kA & T.window==w; kB = kB & T.window==w; end
            if ~isnan(q), kA = kA & T.snr_db==q; kB = kB & T.snr_db==q; end
            A = sortrows(T(kA,:), {'window','snr_db','inject_id'});
            Bt= sortrows(T(kB,:), {'window','snr_db','inject_id'});
            if isempty(A) || height(A) ~= height(Bt), continue; end
            assert(isequal(A.record_id, Bt.record_id) && isequal(A.snr_db, Bt.snr_db), ...
                'pairing must be by record and SNR');
            d = A.eta_max - Bt.eta_max;
            nn = numel(d);
            bi = randi(rs, nn, nn, R.boot_reps);
            bm = median(d(bi),1);
            prow(end+1,:) = {a, b, w, q, nn, median(d), pctl(bm,0.025), pctl(bm,0.975), ...
                mean(d > 0), mean(d < 0)}; %#ok<AGROW>
        end
    end
end
P = cell2table(prow,'VariableNames',{'method_a','method_b','window','snr_db','n', ...
    'd_eta_median','lo95','hi95','frac_a_better','frac_b_better'});
P.method_a = string(P.method_a); P.method_b = string(P.method_b);
writetable(P, fullfile(outdir,'real_inject_paired.csv'));

fprintf('\n--- measured background, paired eta increment P60 - B2 (positive = P60 better) ---\n');
fprintf('%8s %7s %5s %10s %22s %8s\n','window','snr','n','median','95%% CI','P60>B2');
for w = [1:numel(R.win_start_s) 0]
    for q = [R.snr_db NaN]
        r = P(P.method_a=="P60" & P.method_b=="B2" & P.window==w & ...
              ((isnan(q) & isnan(P.snr_db)) | P.snr_db==q), :);
        if isempty(r), continue; end
        if w == 0, wl = 'pooled'; else, wl = sprintf('%d s', R.win_start_s(w)); end
        if isnan(q), ql = 'all'; else, ql = sprintf('%g', q); end
        fprintf('%8s %7s %5d %10.4f   [%+.4f, %+.4f] %7.2f\n', wl, ql, r.n, ...
            r.d_eta_median, r.lo95, r.hi95, r.frac_a_better);
    end
end

out = struct('summary',S,'paired',P);
fid = fopen(fullfile(outdir,'real_inject_analysis.json'),'w');
fprintf(fid,'%s', jsonencode(struct( ...
    'not_claimed', {R.not_claimed}, ...
    'n_background_windows', numel(R.win_start_s), ...
    'n_injections_per_cell', R.n_inject, ...
    'background_realisations_per_window', 1, ...
    'pooled_P60_minus_B2', struct( ...
        'median', P.d_eta_median(P.method_a=="P60" & P.method_b=="B2" & P.window==0 & isnan(P.snr_db)), ...
        'lo95',   P.lo95(P.method_a=="P60" & P.method_b=="B2" & P.window==0 & isnan(P.snr_db)), ...
        'hi95',   P.hi95(P.method_a=="P60" & P.method_b=="B2" & P.window==0 & isnan(P.snr_db))) ...
    ),'PrettyPrint',true)); fclose(fid);
end
