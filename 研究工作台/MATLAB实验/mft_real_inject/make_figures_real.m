function make_figures_real(outdir, figdir)
%MAKE_FIGURES_REAL  One main figure for the measured-background injection case:
%   (a) the measured background spectrum of the selected element on the four
%       windows, with the candidate band marked;
%   (b) the paired eta increment P60 - B2 per window and SNR;
%   (c) a representative trajectory against the injected truth;
%   (d) the compensated spectrum (spectral focusing) for that record.
if nargin < 1, outdir = fullfile(pwd,'results','inject'); end
if nargin < 2, figdir = fullfile(pwd,'results','figures'); end
if ~exist(figdir,'dir'), mkdir(figdir); end
R   = real_config();
cfg = mft_config(); B = cfg.B;
P   = readtable(fullfile(outdir,'real_inject_paired.csv'), 'TextType','string');
SPf = fullfile(pwd,'results','bg','background_spectrum_selected.csv');

fig = figure('Visible','off','Position',[50 50 1280 760]);

%% (a) measured background spectrum
subplot(2,2,1); hold on;
cw = lines(numel(R.win_start_s));
ha = gobjects(0);
if exist(SPf,'file')
    SP = readtable(SPf);
    for w = 1:numel(R.win_start_s)
        % 21-bin moving average in dB, for legibility only
        y = movmean(SP.(sprintf('w%d_db', R.win_start_s(w))), 21);
        ha(end+1) = plot(SP.f_hz, y, '-', 'Color', cw(w,:), 'LineWidth', 0.9); %#ok<AGROW>
    end
end
yl = ylim; pa = patch([R.band(1) R.band(2) R.band(2) R.band(1)], [yl(1) yl(1) yl(2) yl(2)], ...
    [0.9 0.9 0.2], 'FaceAlpha', 0.18, 'EdgeColor','none');
uistack(pa,'bottom');
if ~isempty(ha)
    legend(ha, arrayfun(@(t) sprintf('%d-%d s', t, t+R.win_len_s), R.win_start_s, ...
        'UniformOutput', false), 'Location','south','FontSize',7);
end
ylim(yl); grid on; xlim([-R.keep_hz R.keep_hz]);
xlabel(sprintf('frequency offset from %g Hz (Hz)', R.fref));
ylabel('background PSD (dB, arb., 21-bin smoothed)');
title(sprintf('(a) measured background, HLA North element %d', R.chan_fixed),'FontSize',9);

%% (b) paired eta increment
subplot(2,2,2); hold on;
mk = {'o','s','^','d'};
for w = 1:numel(R.win_start_s)
    r = P(P.method_a=="P60" & P.method_b=="B2" & P.window==w & ~isnan(P.snr_db), :);
    [~,o] = sort(r.snr_db); r = r(o,:);
    errorbar(r.snr_db + 0.08*(w-2.5), r.d_eta_median, r.d_eta_median-r.lo95, ...
        r.hi95-r.d_eta_median, [mk{w} '-'], 'Color', cw(w,:), ...
        'MarkerFaceColor', cw(w,:), 'LineWidth',1.2,'CapSize',4);
end
rp = P(P.method_a=="P60" & P.method_b=="B2" & P.window==0 & ~isnan(P.snr_db), :);
[~,o] = sort(rp.snr_db); rp = rp(o,:);
plot(rp.snr_db, rp.d_eta_median, 'k-', 'LineWidth', 2);
yline(0,'k--'); grid on; xlim([min(R.snr_db)-0.6 max(R.snr_db)+0.6]);
xlabel('nominal injection SNR (dB)'); ylabel('median \Delta\eta  (P60 - B2)');
legend([arrayfun(@(t) sprintf('%d s', t), R.win_start_s, 'UniformOutput', false), {'pooled'}], ...
    'Location','best','FontSize',7);
title('(b) paired coherence increment, same injected record','FontSize',9);

%% representative record: the median-|Delta eta| record of the first window at -18 dB
T = readtable(fullfile(outdir,'real_inject_raw.csv'), 'TextType','string');
qrep = R.snr_db(min(2,numel(R.snr_db)));
A = sortrows(T(T.method=="P60" & T.window==1 & T.snr_db==qrep,:),'inject_id');
Bt= sortrows(T(T.method=="B2"  & T.window==1 & T.snr_db==qrep,:),'inject_id');
d = A.eta_max - Bt.eta_max;
[~, irep] = min(abs(d - median(d)));
rid = A.record_id(irep);  sd = A.seed(irep);

ref = simulate_baseband(cfg, R.scene, qrep, sd, 'eval');
z   = load_real_baseband(R, R.chan_fixed, R.win_start_s(1));
z   = z/sqrt(mean(abs(z).^2));
rec = ref;  rec.y = ref.truth.s_target + ref.truth.intf + z;
res = run_record(rec, cfg, {'B0','B1','B2','P60'});
gt  = rec.truth.gtrue;  t = rec.t;
evalIdx = find(t >= B.eval_s(1) & t < B.eval_s(2));

subplot(2,2,3); hold on;
plot(t(evalIdx), gt(evalIdx), 'k-', 'LineWidth', 2);
cc = [0.47 0.67 0.19; 0.64 0.08 0.18];
nm = {'B2','P60'};
for i = 1:2
    k = find(strcmp({res.method}, nm{i}));
    g = res(k).g + res(k).metrics.nu_peak;
    plot(t(evalIdx), g(evalIdx), '-', 'Color', cc(i,:), 'LineWidth', 1.1);
end
grid on; xlim(B.eval_s); xlabel('time (s)'); ylabel('frequency offset (Hz)');
legend(['injected truth', nm], 'Location','best','FontSize',7);
title(sprintf('(c) representative record %d, %g dB, window %d-%d s', rid, qrep, ...
    R.win_start_s(1), R.win_start_s(1)+R.win_len_s),'FontSize',9);

%% (d) spectral focusing
subplot(2,2,4); hold on;
Ne = numel(evalIdx); nfft = 2^nextpow2(B.fft_pad*Ne);
nu = (0:nfft-1)'*B.fs/nfft; nu(nu >= B.fs/2) = nu(nu >= B.fs/2) - B.fs;
sel = abs(nu) <= 0.6;
[nus, ord] = sort(nu(sel));
base = [];
for i = 1:2
    k = find(strcmp({res.method}, nm{i}));
    phi = 2*pi*cumtrapz(t, res(k).g);
    Zs = abs(fft(rec.y(evalIdx).*exp(-1j*phi(evalIdx)), nfft)).^2;
    Zs = Zs(sel); Zs = Zs(ord);
    if isempty(base), base = max(Zs); end
    plot(nus, 10*log10(Zs/base), '-', 'Color', cc(i,:), 'LineWidth', 1.1);
end
grid on; xlabel('residual frequency (Hz)'); ylabel('compensated spectrum (dB, rel. B2 peak)');
title('(d) spectral focusing on the same measured-background record','FontSize',9);
legend(nm,'Location','best','FontSize',7);

sgtitle(sprintf(['Measured-background injection: real SWellEx-96 S5 background + synthetic ' ...
    'target and interferer (%d windows, %d injections per cell; not a blind test, no P_d claimed)'], ...
    numel(R.win_start_s), R.n_inject), 'FontSize',10);
exportgraphics(fig, fullfile(figdir,'fig5_real_inject.png'),'Resolution',160);
savefig(fig, fullfile(figdir,'fig5_real_inject.fig'));
try, exportgraphics(fig, fullfile(figdir,'fig5_real_inject.pdf'),'ContentType','vector'); catch, end
close(fig);

RP = struct('record_id', rid, 'seed', sd, 'snr_db', qrep, 'window_s', R.win_start_s(1), ...
    'eta_B2', Bt.eta_max(irep), 'eta_P60', A.eta_max(irep), ...
    'd_eta', d(irep), 'd_eta_median_of_cell', median(d));
fid = fopen(fullfile(figdir,'representative_real.json'),'w');
fprintf(fid,'%s', jsonencode(RP,'PrettyPrint',true)); fclose(fid);
fprintf('figure written to %s (representative record %d)\n', figdir, rid);
end
