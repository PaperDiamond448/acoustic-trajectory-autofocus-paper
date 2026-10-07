%RUN_B1_REALTONE Phase B, first real-line-spectrum experiment (100 Hz).
% Uses the frozen MFT/SMR/BTA estimator functions without changing them.
% The only duration-specific family mapping for 600 s is described in the
% accompanying README: 21 coefficients span the complete accumulation window.

thisFile = mfilename('fullpath');
outDir = fileparts(thisFile);
phaseADir = fileparts(fileparts(outDir));
projectDir = fileparts(phaseADir);
injectDir = fullfile(projectDir, '研究工作台', 'MATLAB实验', 'mft_real_inject');
addpath(fullfile(phaseADir, 'code'));
addpath(injectDir);

R = real_config();
cfg = mft_config();
assert(exist(R.file, 'file') == 2, 'Raw SIO file not found: %s', R.file);
assert(exist(fullfile(phaseADir, 'exp', 'A_visibility', 'A3_state.mat'), 'file') == 2, ...
    'Phase A state file is missing.');
assert(exist(fullfile(phaseADir, 'tables', 'A4_groundtruth.csv'), 'file') == 2, ...
    'Phase A reference-track table is missing.');

% Phase B frozen record choices.  Each requested interval is extracted once
% from the original continuous SIO stream, with 10 s guards on both sides.
starts = [900 900];
durations = [300 600];
for q = 1:numel(durations)
    run_duration(R, cfg, outDir, starts(q), durations(q));
end

% The original Phase A LOFAR and both independently constructed references
% are shown for the prespecified 900-1200 s primary interval.
make_primary_figure(phaseADir, outDir);
fprintf('Phase B first-round runs complete. Outputs: %s\n', outDir);

function run_duration(R, cfg, outDir, start_s, T)
fs = R.fs;
fref = R.fref;
guard_s = R.guard_s;
B = cfg.B;
M = cfg.M;

% Prespecified Phase-B candidate band from the experiment plan.  The
% estimator source and correction-radius settings remain frozen.
B.band = [-1.5 1.5];
B.eval_s = [5 T-5];
B.T = T;
B.N = round(T*fs);
M.B2.band = B.band;

% Exact-DFT-bin extraction, in one continuous raw-record read for each T.
[y, extract] = phaseA_load_baseband(R.file, R.chan_fixed, fref, fs, ...
    R.keep_hz, R.fs_raw, R.n_raw, start_s, T, guard_s, guard_s);
assert(numel(y) == B.N, 'Unexpected baseband sample count for %d s.', T);
t = (0:B.N-1)'/fs;

fcfg = struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine, ...
    'band',B.band,'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
evalIdx = find(t >= B.eval_s(1) & t < B.eval_s(2));
assert(~isempty(evalIdx), 'Empty evaluation interval.');

% The original MFT implementation is estimate_b0.  SMR uses the original
% Viterbi initialization (estimate_b1) followed by estimate_b2.  BTA starts
% from that exact SMR coefficient vector and uses estimate_proposed.
tic; fe = common_frontend(y, t, fcfg); t_frontend = toc;
tic; oMFT = estimate_b0(fe, M.B0); t_MFT = toc;
tic; oInit = estimate_b1(fe, M.B1); t_VIT = toc;

tic;
if T == 300
    fam = build_family(t, fe.tc, oInit.g, M.B2);
else
    % build_family is frozen for 300 s.  Rescale its time coordinates so its
    % 21 unchanged hat functions span the complete 600 s observation.  This
    % is equivalent to knots 0:30:600 and preserves the same coefficient count.
    scale = T/300;
    fam = build_family(t/scale, fe.tc/scale, oInit.g, M.B2);
    fam.knots = fam.knots*scale;
    fam.tchk = fam.tchk*scale;
    fam.phiA = fam.phiA*scale;
    fam.H = fam.H*scale;
end
oSMR = estimate_b2(fe, fam, M.B2);
t_SMRest = toc;

% BTA objective uses y, phase basis, and family constraints; the large
% matching arrays are no longer needed after SMR and are released first.
fe.C = []; fe.C_coarse = []; fe.S = []; fe.frame_idx = [];
tic; oBTA = estimate_proposed(y, fe, fam, oSMR.u, evalIdx, M.P); t_BTA = toc;

tracks = struct();
tracks.Periodogram = nan(size(t));
tracks.MFT = oMFT.g(:) + fref;
tracks.Initial_VIT = oInit.g(:) + fref;
tracks.SMR = oSMR.g(:) + fref;
tracks.BTA = oBTA.g(:) + fref;

% Rectangular, unsmoothed, full-record periodograms with a common FFT grid.
% Power is |FFT(x)|^2/N.  Every curve is divided by the Periodogram peak
% within the common candidate band; no curve smoothing is applied.
nfft = 2^nextpow2(8*numel(y));
freq = (-nfft/2:nfft/2-1)'*fs/nfft;
fAbs = fref + freq;
signals = cell(5,1);
labels = {'Periodogram';'MFT';'SMR';'BTA'};
signals{1} = y;
signals{2} = compensate(y, t, tracks.MFT, fref);
signals{3} = compensate(y, t, tracks.SMR, fref);
signals{4} = compensate(y, t, tracks.BTA, fref);
signals{5} = compensate(y, t, tracks.Initial_VIT, fref);
P = zeros(nfft,5);
fftRuntime = zeros(5,1);
for k = 1:5
    fftTimer = tic;
    P(:,k) = abs(fftshift(fft(signals{k}, nfft))).^2/numel(y);
    fftRuntime(k) = toc(fftTimer);
end
commonBand = abs(fAbs-fref) <= 1.5;
refPeak = max(P(commonBand,1));
Pnorm = P/refPeak;
Pdb = 10*log10(max(Pnorm, realmin));

% Compare estimated frequency paths with both Phase-A references.  These
% are reference-track discrepancies, not receive-phase errors or truth RMSE.
refs = readtable(fullfile(fileparts(fileparts(outDir)), 'tables', 'A4_groundtruth.csv'));
tg = start_s + t;
fRoute = interp1(refs.t_s, refs.f_pred_100, tg, 'linear', NaN);
fGPS = interp1(refs.t_s, refs.f_gps_100, tg, 'linear', NaN);
methodTracks = {[], tracks.MFT, tracks.SMR, tracks.BTA};
runtime = [fftRuntime(1), t_MFT, t_VIT+t_SMRest, t_VIT+t_SMRest+t_BTA, t_VIT];
pipeline = [fftRuntime(1), t_frontend+t_MFT, t_frontend+t_VIT+t_SMRest, ...
    t_frontend+t_VIT+t_SMRest+t_BTA, t_frontend+t_VIT];

summary = table('Size',[4 12], 'VariableTypes', ...
    {'string','double','double','double','double','double','double','double','double','double','double','double'}, ...
    'VariableNames', {'method','peak_frequency_Hz','spectral_prominence_dB', ...
    'bw_3dB_Hz','method_runtime_s','pipeline_runtime_s', ...
    'rmse_vs_selfconsistent_Hz','coverage_selfconsistent_0p05', ...
    'rmse_vs_GPS_Hz','coverage_GPS_0p05','peak_power_relative_Periodogram_dB', ...
    'BTA_selected_stage_code'});
for k = 1:4
    summary.method(k) = string(labels{k});
    [fp, prom, bw, pk] = spectrum_metrics(fAbs, P(:,k), fref, B.band);
    summary.peak_frequency_Hz(k) = fp;
    summary.spectral_prominence_dB(k) = prom;
    summary.bw_3dB_Hz(k) = bw;
    summary.peak_power_relative_Periodogram_dB(k) = 10*log10(pk/refPeak);
    summary.method_runtime_s(k) = runtime(k);
    summary.pipeline_runtime_s(k) = pipeline(k);
    if ~isempty(methodTracks{k})
        g = methodTracks{k};
        valid = isfinite(g) & isfinite(fRoute);
        summary.rmse_vs_selfconsistent_Hz(k) = sqrt(mean((g(valid)-fRoute(valid)).^2));
        summary.coverage_selfconsistent_0p05(k) = mean(abs(g(valid)-fRoute(valid)) <= 0.05);
        valid = isfinite(g) & isfinite(fGPS);
        summary.rmse_vs_GPS_Hz(k) = sqrt(mean((g(valid)-fGPS(valid)).^2));
        summary.coverage_GPS_0p05(k) = mean(abs(g(valid)-fGPS(valid)) <= 0.05);
    else
        summary{k, 7:10} = [NaN NaN NaN NaN];
    end
    summary.BTA_selected_stage_code(k) = NaN;
end
% Stage selection is algorithm bookkeeping, not a spectral metric.
summary.BTA_selected_stage_code(strcmp(summary.method,'BTA')) = ...
    find(strcmp(oBTA.selected, {'B2','stage1','stage2','stage3'}),1)-1;

% Supporting comparator: the common, unrefined VIT initial trajectory.
[fInit, promInit, bwInit, pkInit] = spectrum_metrics(fAbs, P(:,5), fref, B.band);
initialMetrics = table("Initial_VIT",fInit,promInit,bwInit, ...
    10*log10(pkInit/refPeak),t_VIT,t_frontend+t_VIT, ...
    'VariableNames',{'comparator','peak_frequency_Hz','spectral_prominence_dB', ...
    'bw_3dB_Hz','peak_power_relative_Periodogram_dB','estimator_runtime_s','pipeline_runtime_s'});
compNames = {'Initial_VIT';'MFT';'SMR'};
compIdx = [5 2 3];
compRows = cell(3,1);
for j = 1:3
    [fc, pc, wc, kc] = spectrum_metrics(fAbs,P(:,compIdx(j)),fref,B.band);
    compRows{j} = {T,compNames{j},fc,10*log10(kc/refPeak),pc,wc, ...
        summary.peak_frequency_Hz(4),summary.peak_power_relative_Periodogram_dB(4), ...
        summary.spectral_prominence_dB(4),summary.bw_3dB_Hz(4), ...
        summary.peak_power_relative_Periodogram_dB(4)-10*log10(kc/refPeak), ...
        summary.spectral_prominence_dB(4)-pc,wc/summary.bw_3dB_Hz(4), ...
        pipeline(compIdx(j)),pipeline(4),pipeline(4)-pipeline(compIdx(j))};
end
increment = cell2table(vertcat(compRows{:}), 'VariableNames', ...
    {'duration_s','comparator','comparator_peak_frequency_Hz', ...
    'comparator_peak_relative_Periodogram_dB','comparator_prominence_dB', ...
    'comparator_bw_3dB_Hz','BTA_peak_frequency_Hz', ...
    'BTA_peak_relative_Periodogram_dB','BTA_prominence_dB','BTA_bw_3dB_Hz', ...
    'BTA_peak_increment_dB','BTA_prominence_increment_dB', ...
    'comparator_over_BTA_bw_ratio','comparator_pipeline_runtime_s', ...
    'BTA_pipeline_runtime_s','BTA_extra_pipeline_runtime_s'});

tag = sprintf('%ds',T);
writetable(summary, fullfile(outDir, ['B1_summary_' tag '.csv']));
specTab = table(fAbs, P(:,1),P(:,2),P(:,3),P(:,4),P(:,5), ...
    Pdb(:,1),Pdb(:,2),Pdb(:,3),Pdb(:,4),Pdb(:,5), ...
    'VariableNames', {'frequency_Hz','power_Periodogram','power_MFT','power_SMR','power_BTA', ...
    'power_initial_VIT','relative_dB_Periodogram','relative_dB_MFT','relative_dB_SMR', ...
    'relative_dB_BTA','relative_dB_initial_VIT'});
writetable(specTab, fullfile(outDir, ['B1_spectra_' tag '.csv']));
writetable(initialMetrics,fullfile(outDir,['B1_initial_track_' tag '.csv']));
writetable(increment,fullfile(outDir,['B1_increments_' tag '.csv']));
trackTab = table(tg, tracks.MFT, tracks.Initial_VIT, tracks.SMR, tracks.BTA, fRoute, fGPS, ...
    'VariableNames', {'time_s','MFT_Hz','initial_VIT_Hz','SMR_Hz','BTA_Hz', ...
    'reference_selfconsistent_Hz','reference_GPS_Hz'});
writetable(trackTab, fullfile(outDir, ['B1_tracks_' tag '.csv']));

fig = figure('Visible','off','Position',[100 100 1250 650]);
plot(fAbs(commonBand), Pdb(commonBand,1), 'k-', 'LineWidth',1.15); hold on;
plot(fAbs(commonBand), Pdb(commonBand,2), 'Color',[0.1 0.45 0.85], 'LineWidth',1.0);
plot(fAbs(commonBand), Pdb(commonBand,3), 'Color',[0.85 0.35 0.1], 'LineWidth',1.0);
plot(fAbs(commonBand), Pdb(commonBand,4), 'Color',[0.15 0.6 0.25], 'LineWidth',1.0);
grid on; xlim([fref+B.band(1),fref+B.band(2)]);
xlabel('Frequency (Hz)'); ylabel('Power relative to Periodogram peak (dB)');
title(sprintf('SWellEx-96 S5, element %d, %d s continuous record, rectangular unsmoothed spectra',R.chan_fixed,T));
legend(labels,'Location','best'); set(gca,'FontSize',11);
print(fig, fullfile(outDir, ['B1_spectra_' tag '.png']), '-dpng','-r300');
close(fig);

provenance = struct('record','SWellEx-96 Event S5, HLA North', ...
    'input_file',R.file,'input_bytes',R.file_bytes,'input_sha256',R.file_sha256, ...
    'channel',R.chan_fixed, ...
    'raw_sample_rate_Hz',R.fs_raw,'raw_samples_per_channel',R.n_raw, ...
    'raw_time_origin_s',0,'window_start_s',start_s,'window_end_s',start_s+T, ...
    'window_duration_s',T,'baseband_rate_Hz',fs,'baseband_center_Hz',fref, ...
    'evaluation_interval_local_s',B.eval_s, ...
    'retained_baseband_halfwidth_Hz',R.keep_hz,'guard_s_each_side',guard_s, ...
    'baseband_extraction','single continuous raw-record DFT extraction; exact bins; 10 s guards discarded', ...
    'baseband_samples',numel(y),'channel_source','real_config.chan_fixed (frozen element 9)', ...
    'candidate_search_band_Hz',B.band,'correction_radius_Hz',M.B2.radius, ...
    'family_coefficients',21,'family_knot_spacing_s',T/20, ...
    'frontend_frame_s',B.L/fs,'frontend_hop_s',B.D/fs, ...
    'MFT_grid_step_Hz',M.B0.df,'MFT_median_frames',M.B0.median_len, ...
    'VIT_grid_step_Hz',B.df_fine*B.coarse_dec, ...
    'VIT_sigma_step_Hz',M.B1.sigma_step,'VIT_max_step_Hz_per_hop',M.B1.max_step, ...
    'VIT_median_frames',M.B1.median_len, ...
    'SMR_local_radius_Hz',M.B2.radius,'SMR_knot_spacing_s',M.B2.knot_ds*T/300, ...
    'SMR_lambda_F',M.B2.lambda_F,'SMR_u_bounds',M.B2.u_bounds,'SMR_tol_x',M.B2.tol_x, ...
    'BTA_block_stages_s',M.P.h_stages_s,'BTA_lambda_C',M.P.lambda_C, ...
    'BTA_optimizer','SQP with analytic objective gradient', ...
    'BTA_step_tolerance',M.P.tol_x,'BTA_optimality_tolerance',M.P.tol_opt, ...
    'BTA_stage_max_iterations',M.P.max_iter,'BTA_stage_max_function_evaluations',M.P.max_fevals, ...
    'MFT_definition','estimate_b0', 'SMR_definition','estimate_b1 then estimate_b2', ...
    'BTA_definition','estimate_proposed initialized from estimate_b2.u', ...
    'spectral_power','abs(FFT(x))^2/N; rectangular window; one common FFT grid; no smoothing', ...
    'spectral_normalization','all spectra divided by Periodogram peak in candidate band', ...
    'track_reference_caveat','reported discrepancies vs Phase-A references are not true receive-phase errors', ...
    'matlab_version',version,'extraction_info',extract, ...
    'MFT_runtime_s',t_MFT,'VIT_initialization_runtime_s',t_VIT, ...
    'SMR_runtime_including_family_s',t_SMRest,'BTA_incremental_runtime_s',t_BTA, ...
    'frontend_runtime_s',t_frontend,'BTA_selected_candidate',oBTA.selected, ...
    'BTA_exitflags',oBTA.exitflags,'BTA_iterations',oBTA.iters, ...
    'BTA_function_evaluations',oBTA.fevals,'BTA_stage_J290',oBTA.stage_J290, ...
    'BTA_hard_fail',oBTA.hard_fail,'BTA_fallback',oBTA.fallback, ...
    'BTA_all_stages_hit_iteration_cap',oBTA.all_stages_capped, ...
    'Periodogram_fft_runtime_s',fftRuntime(1));
fid = fopen(fullfile(outDir, ['B1_config_' tag '.json']),'w');
fwrite(fid, jsonencode(provenance,'PrettyPrint',true),'char'); fclose(fid);
save(fullfile(outDir, ['B1_raw_' tag '.mat']), 'y','t','extract','-v7.3');
save(fullfile(outDir, ['B1_estimates_' tag '.mat']), 'tracks','summary','oMFT','oInit','oSMR','oBTA','fam','-v7.3');
fprintf('%d s complete: MFT %.2fs, SMR chain %.2fs, BTA increment %.2fs, selected %s\n', ...
    T,t_MFT,t_VIT+t_SMRest,t_BTA,oBTA.selected);
end

function z = compensate(y, t, fHz, fref)
g = fHz(:)-fref;
phi = 2*pi*cumtrapz(t(:),g);
z = y(:).*exp(-1i*phi);
end

function [fpeak, prominence_dB, width3_dB, peakPower] = spectrum_metrics(f, P, fref, band)
use = f >= fref+band(1) & f <= fref+band(2);
fu = f(use); pu = P(use);
[peakPower, im] = max(pu);
fpeak = fu(im);
offset = abs(fu-fpeak);
floorMask = offset >= 0.5 & offset <= 1.5;
if any(floorMask)
    floorPower = median(pu(floorMask));
    prominence_dB = 10*log10(peakPower/max(floorPower,realmin));
else
    prominence_dB = NaN;
end
db = 10*log10(max(pu,realmin));
target = db(im)-3;
il = find(db(1:im) <= target,1,'last');
ir0 = find(db(im:end) <= target,1,'first');
if isempty(il) || isempty(ir0)
    width3_dB = NaN;
else
    ir = im+ir0-1;
    fl = interp1(db([il il+1]),fu([il il+1]),target,'linear');
    fr = interp1(db([ir-1 ir]),fu([ir-1 ir]),target,'linear');
    width3_dB = fr-fl;
end
end

function make_primary_figure(phaseADir, outDir)
S = load(fullfile(phaseADir,'exp','A_visibility','A3_state.mat'),'lof','R');
refs = readtable(fullfile(phaseADir,'tables','A4_groundtruth.csv'));
tracks = readtable(fullfile(outDir,'B1_tracks_300s.csv'));
lof = S.lof;
timeSel = lof.tc >= 900 & lof.tc < 1200;
freqSel = S.R.fref + lof.freq >= 98.5 & S.R.fref + lof.freq <= 101.5;
fig = figure('Visible','off','Position',[100 100 1350 760]);
imagesc(lof.tc(timeSel), S.R.fref+lof.freq(freqSel), lof.P_db(freqSel,timeSel));
axis xy; hold on; colormap(parula); colorbar;
idx = tracks.time_s >= 900 & tracks.time_s < 1200;
hInit = plot(tracks.time_s(idx),tracks.initial_VIT_Hz(idx),'w--','LineWidth',1.2);
hBTA = plot(tracks.time_s(idx),tracks.BTA_Hz(idx),'r-','LineWidth',1.5);
rr = refs.t_s >= 900 & refs.t_s < 1200;
hRoute = plot(refs.t_s(rr),refs.f_pred_100(rr),'c:','LineWidth',1.5);
hGPS = plot(refs.t_s(rr),refs.f_gps_100(rr),'y-.','LineWidth',1.5);
xlim([900 1200]); ylim([98.5 101.5]);
xlabel('Time (s)'); ylabel('Frequency (Hz)');
title('100 Hz line spectrum, original LOFAR with initial/BTA tracks and Phase-A references');
legend([hInit hBTA hRoute hGPS], ...
    {'Initial VIT trajectory','BTA trajectory','Self-consistent reference','GPS reference'}, ...
    'Location','southoutside','Orientation','horizontal');
set(gca,'FontSize',11);
print(fig,fullfile(outDir,'B1_lofar_trajectory_900_1200.png'),'-dpng','-r300');
close(fig);
end
