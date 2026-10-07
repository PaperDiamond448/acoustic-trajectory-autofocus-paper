function make_figure_expB(outdir, figdir)
%MAKE_FIGURE_EXPB  Cross-front-end refinement figure (main text) plus the
%   entry-quality panel, which is written separately for the supplement.
%
%   Main figure:
%     (a) module entry vs module exit coherence efficiency, both branches
%     (b) median entry-to-exit increment per SNR with paired bootstrap CI
%     (c) change in effective frequency RMSE against change in coherence
%         efficiency; the upper-right quadrant is the one experiment A
%         isolates by construction
%
%   Panel (c) is exploratory and its caption says so.  Per-SNR intervals in
%   (b) are within-cell: each cell holds one record per realisation.
if nargin < 1 || isempty(outdir), outdir = fullfile(pwd,'results','expB'); end
if nargin < 2 || isempty(figdir), figdir = fullfile(pwd,'results','figures'); end
if ~exist(figdir,'dir'), mkdir(figdir); end
T  = readtable(fullfile(outdir,'expB_raw.csv'), 'TextType','string');
S1 = readtable(fullfile(outdir,'expB_summary.csv'), 'TextType','string');
DQ = readtable(fullfile(outdir,'expB_rmse_vs_eta_posthoc.csv'), 'TextType','string');

brs   = ["viterbi_b2","suv"];
short = {'Viterbi front end','phase-continuous TBD front end'};
cols  = [0.64 0.08 0.18; 0.20 0.30 0.70];

fig = figure('Visible','off','Position',[60 60 1320 400]);

% ---- (a) entry vs exit ----
subplot(1,3,1); hold on;
h = gobjects(1,2);
for i = 1:2
    R = T(T.branch==brs(i),:);
    h(i) = scatter(R.eta_in, R.eta_out, 9, cols(i,:), 'filled', ...
        'MarkerFaceAlpha',0.35, 'MarkerEdgeColor','none');
end
plot([0 1],[0 1],'k--','LineWidth',0.8);
grid on; box on; axis square; xlim([0 1]); ylim([0 1]);
xlabel('\eta_{max} at module entry'); ylabel('\eta_{max} at module exit');
legend(h, short, 'Location','southeast','FontSize',8,'Box','off');
title('(a) coherence efficiency across the module','FontSize',9);

% ---- (b) per-SNR increment ----
subplot(1,3,2); hold on;
for i = 1:2
    R = S1(S1.branch==brs(i),:);
    [~,o] = sort(R.snr_db); R = R(o,:);
    errorbar(R.snr_db, R.d_eta_median, R.d_eta_median-R.d_eta_lo95, ...
        R.d_eta_hi95-R.d_eta_median, 'o-', 'Color', cols(i,:), ...
        'MarkerFaceColor', cols(i,:), 'LineWidth',1.3, 'CapSize',5);
end
yline(0,'k--'); grid on; box on;
xlim([-18.5 -15.5]); set(gca,'XTick',[-18 -17 -16]); ylim([0 0.26]);
xlabel('baseband SNR (dB)');
ylabel('median \Delta\eta_{max}  (exit - entry)');
legend(short,'Location','northeast','FontSize',8,'Box','off');
title('(b) entry-to-exit increment, 95 % paired interval','FontSize',9);

% ---- (c) the two indicators, four quadrants ----
subplot(1,3,3); hold on;
for i = 1:2
    R = T(T.branch==brs(i),:);
    scatter(1000*(R.rmse_eff_out_hz - R.rmse_eff_in_hz), R.d_eta, 9, cols(i,:), ...
        'filled', 'MarkerFaceAlpha',0.32, 'MarkerEdgeColor','none');
end
xline(0,'k-','LineWidth',0.9); yline(0,'k-','LineWidth',0.9);
grid on; box on; xlim([-10.5 9.5]); ylim([-0.2 0.56]);
xlabel('\Delta RMSE_{eff}  (mHz)'); ylabel('\Delta\eta_{max}');
% Two Viterbi-branch records fall left of the plotted range.  They are kept in
% every statistic; an inset shows where they actually are rather than leaving
% the reader with a bare footnote.
dr_all = 1000*(T.rmse_eff_out_hz - T.rmse_eff_in_hz);
noff = sum(dr_all(T.branch==brs(1)) < -10.5);
txt = cell(1,2);
for i = 1:2
    j = find(DQ.branch == brs(i), 1);
    txt{i} = [short{i} ': ' num2str(100*DQ.frac_rmse_worse_and_eta_better(j),'%.1f') ' %'];
end
text(0.97, 0.965, 'RMSE up, coherence up', 'Units','normalized', ...
     'HorizontalAlignment','right','FontSize',8,'FontWeight','bold');
text(0.97, 0.895, txt{1}, 'Units','normalized','HorizontalAlignment','right', ...
     'FontSize',8,'Color',cols(1,:));
text(0.97, 0.835, txt{2}, 'Units','normalized','HorizontalAlignment','right', ...
     'FontSize',8,'Color',cols(2,:));
title('(c) the two indicators disagree on most records','FontSize',9);

axi = axes('Position',[0.6985 0.213 0.083 0.155]); hold(axi,'on');
for i = 1:2
    m = T.branch==brs(i);
    scatter(axi, dr_all(m), T.d_eta(m), 3, cols(i,:), 'filled', ...
        'MarkerFaceAlpha',0.30, 'MarkerEdgeColor','none');
end
xline(axi,0,'k-','LineWidth',0.6); yline(axi,0,'k-','LineWidth',0.6);
set(axi,'FontSize',6,'Box','on','XTick',[-40 -20 0],'YTick',[0 0.5], ...
    'Color',[1 1 1],'XColor',[0.35 0.35 0.35],'YColor',[0.35 0.35 0.35]);
xlim(axi,[-41 11]); ylim(axi,[-0.22 0.58]);
title(axi,['full range (' num2str(noff) ' off-scale records)'], ...
    'FontSize',6,'FontWeight','normal','Color',[0.35 0.35 0.35]);

exportgraphics(fig, fullfile(figdir,'fig_crossfrontend.png'),'Resolution',200);
savefig(fig, fullfile(figdir,'fig_crossfrontend.fig'));
try, exportgraphics(fig, fullfile(figdir,'fig_crossfrontend.pdf'),'ContentType','vector'); catch, end
close(fig);

% ---- supplement: increment against entry quality -------------------------
figs = figure('Visible','off','Position',[60 60 520 400]);
hold on;
hs = gobjects(1,2);
for i = 1:2
    R = T(T.branch==brs(i),:);
    hs(i) = scatter(R.eta_in, R.d_eta, 9, cols(i,:), 'filled', ...
        'MarkerFaceAlpha',0.22, 'MarkerEdgeColor','none');
    e = 0:0.1:1;                                  % 0.1-wide bins, NOT deciles
    xm = nan(10,1); ym = nan(10,1);
    for k = 1:10
        m = R.eta_in >= e(k) & R.eta_in < e(k+1);
        if sum(m) >= 5, xm(k) = median(R.eta_in(m)); ym(k) = median(R.d_eta(m)); end
    end
    plot(xm, ym, 'o-', 'Color', cols(i,:), 'MarkerFaceColor', cols(i,:), 'LineWidth',1.4);
end
yline(0,'k--'); grid on; box on; xlim([0 1]);
xlabel('\eta_{max} at module entry'); ylabel('\Delta\eta_{max}');
legend(hs, short,'Location','northeast','FontSize',8,'Box','off');
title({'increment against entry quality', ...
       'lines: medians within 0.1-wide entry-efficiency bins'},'FontSize',9);
exportgraphics(figs, fullfile(figdir,'figS_entry_quality.png'),'Resolution',200);
savefig(figs, fullfile(figdir,'figS_entry_quality.fig'));
try, exportgraphics(figs, fullfile(figdir,'figS_entry_quality.pdf'),'ContentType','vector'); catch, end
close(figs);
fprintf('cross-front-end figure and its supplement written to %s\n', figdir);
end
