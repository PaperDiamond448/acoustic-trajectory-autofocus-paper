function make_figure_expA(outdir, figdir)
%MAKE_FIGURE_EXPA  Mechanism figure: the frequency RMSE does not decide the
%   coherent efficiency.  Panels (a) frequency error, (b) integrated frequency
%   error, (c) compensated spectrum.
%
%   Sign convention, stated here and in the caption: e_g(t) = g_true(t) - ghat(t),
%   so the residual phase after compensation is +2*pi*int_0^t e_g(xi) dxi.
%   Panel (b) plots that integral in cycles, which is the integral of e_g
%   itself; the RMSE and eta results are unchanged by an overall sign flip.
%
%   Everything else that describes the construction (deterministic, no noise,
%   no estimator) belongs in the caption, not on the canvas.
if nargin < 1 || isempty(outdir), outdir = fullfile(pwd,'results','expA'); end
if nargin < 2 || isempty(figdir), figdir = fullfile(pwd,'results','figures'); end
if ~exist(figdir,'dir'), mkdir(figdir); end
cfg = mft_config();  B = cfg.B;
C = readtable(fullfile(outdir,'expA_curves.csv'));
T = readtable(fullfile(outdir,'expA_mechanism.csv'), 'TextType','string');

t  = C.t_s;  fs = B.fs;
evalIdx = find(t >= B.eval_s(1) & t < B.eval_s(2));
Ne = numel(evalIdx);  nfft = 2^nextpow2(B.fft_pad*Ne);
nu = (0:nfft-1)'*fs/nfft;  nu(nu >= fs/2) = nu(nu >= fs/2) - fs;

cA = [0.20 0.30 0.70];  cB = [0.85 0.33 0.10];
E  = {C.e_A_hz, C.e_B_hz};  PH = {C.phi_A_rad, C.phi_B_rad};
cols = {cA, cB};

fig = figure('Visible','off','Position',[60 60 1320 400]);

% ---- (a) the two constructed frequency errors; RMSE appears only here ----
subplot(1,3,1); hold on;
h = gobjects(1,2);
for k = 1:2
    h(k) = plot(t(evalIdx), E{k}(evalIdx), 'Color', cols{k}, 'LineWidth', 1.2);
end
yline(0,'k:'); grid on; box on;
xlim(B.eval_s); ylim([-0.0125 0.0175]);        % head-room above the traces for the legend
xlabel('time (s)'); ylabel('frequency error  e_g(t)   (Hz)');
legend(h, {['A:  RMSE = ' num2str(T.rmse_hz(1),'%.4f') ' Hz'], ...
           ['B:  RMSE = ' num2str(T.rmse_hz(2),'%.4f') ' Hz']}, ...
       'Location','north','Orientation','horizontal','FontSize',8,'Box','off');
title('(a) constructed frequency errors','FontSize',9);

% ---- (b) their integral, in cycles ----
subplot(1,3,2); hold on;
for k = 1:2
    plot(t(evalIdx), PH{k}(evalIdx)/(2*pi), 'Color', cols{k}, 'LineWidth', 1.2);
end
yline(0,'k:'); grid on; box on; xlim(B.eval_s); ylim([-0.12 0.72]);
xlabel('time (s)');
ylabel('\int_0^t e_g(\xi) d\xi   (cycles)');
legend({'A','B'},'Location','northwest','FontSize',8,'Box','off');
title('(b) integrated frequency error','FontSize',9);

% ---- (c) compensated spectrum; eta appears only here ----
subplot(1,3,3); hold on;
for k = 1:2
    z = exp(1j*PH{k}(evalIdx));
    S = abs(fft(z, nfft)).^2 / Ne^2;
    [nus, o] = sort(nu);  Ss = S(o);
    m = abs(nus) <= 0.05;
    plot(nus(m), Ss(m), 'Color', cols{k}, 'LineWidth', 1.2);
end
grid on; box on; ylim([0 1.08]); xlim([-0.05 0.05]);
xlabel('residual frequency \nu (Hz)'); ylabel('normalised compensated power');
legend({['A:  \eta_{max} = ' num2str(T.eta_max(1),'%.4f')], ...
        ['B:  \eta_{max} = ' num2str(T.eta_max(2),'%.4f')]}, ...
        'Location','northwest','FontSize',8,'Box','off');
title('(c) compensated spectrum, peak taken over |\nu| \leq 2 Hz','FontSize',9);

exportgraphics(fig, fullfile(figdir,'fig_mechanism.png'),'Resolution',200);
savefig(fig, fullfile(figdir,'fig_mechanism.fig'));
try, exportgraphics(fig, fullfile(figdir,'fig_mechanism.pdf'),'ContentType','vector'); catch, end
close(fig);
fprintf('mechanism figure written to %s\n', figdir);
end
