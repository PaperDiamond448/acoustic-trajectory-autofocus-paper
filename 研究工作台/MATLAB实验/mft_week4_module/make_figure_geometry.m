function make_figure_geometry(figdir)
%MAKE_FIGURE_GEOMETRY  Motion geometry and the resulting Doppler trajectory.
%   (a) plan view: fixed hydrophone, straight constant-speed track, range
%       R(tau), CPA distance dc, radial velocity with its sign convention.
%   (b) received instantaneous frequency against RECEPTION time, crossing the
%       source frequency f0 at t_cpa_rx = tau_c + dc/c.
%
%   The panel deliberately plots the RECEIVED frequency, not the baseband
%   trajectory: at CPA the baseband value is f0 - fref, which is zero only
%   when the reference happens to equal the source frequency.
if nargin < 1 || isempty(figdir), figdir = fullfile(pwd,'results','figures'); end
if ~exist(figdir,'dir'), mkdir(figdir); end
cfg = mft_config();  B = cfg.B;
geo = struct('f0',B.dev_geo.f0,'v',B.dev_geo.v,'c',B.c,'dc',B.dc, ...
             't_cpa_rx',B.dev_geo.t_cpa_rx);
t = (0:B.N-1)'/B.fs;
[tau, ftrue] = geometry_tau(t, geo);
tau_c = geo.t_cpa_rx - geo.dc/geo.c;

fig = figure('Visible','off','Position',[60 60 1120 400]);

% ---------------- (a) plan view ----------------
subplot(1,2,1); hold on; axis equal;
xtrack = geo.v*(tau - tau_c);                       % along-track position, m
plot(xtrack, geo.dc*ones(size(xtrack)), '-', 'Color',[0.45 0.45 0.45], 'LineWidth',1.4);
plot(0, 0, 'kv', 'MarkerSize',9, 'MarkerFaceColor',[0.15 0.15 0.15]);
text(70, -20, 'hydrophone (fixed)', 'HorizontalAlignment','left','FontSize',8);

% CPA point and the closest-approach distance
plot(0, geo.dc, 'o', 'MarkerSize',7, 'MarkerFaceColor',[0.30 0.30 0.30], 'MarkerEdgeColor','none');
plot([0 0],[0 geo.dc], ':', 'Color',[0.30 0.30 0.30], 'LineWidth',1.1);
text(50, geo.dc/2, 'd_c', 'FontSize',11);
text(30, geo.dc+110, 'CPA', 'FontSize',9, 'HorizontalAlignment','left');

% a target position before CPA
xs = -560;  ys = geo.dc;
R  = hypot(xs, ys);
uaway = [xs, ys]/R;                                 % unit vector pointing AWAY from the receiver
plot([0 xs],[0 ys], '-', 'Color',[0.20 0.30 0.70], 'LineWidth',1.3);
text(-880, 620, 'R(\tau)', 'FontSize',11, 'Color',[0.20 0.30 0.70]);
text(-990, 480, 'delay R(\tau)/c', 'FontSize',8, 'Color',[0.20 0.30 0.70]);
plot(xs, ys, 'o', 'MarkerSize',8, 'MarkerFaceColor',[0.64 0.08 0.18], 'MarkerEdgeColor','none');
text(xs-40, ys+250, 'target at emission time \tau', 'FontSize',8, 'HorizontalAlignment','center');

% velocity and its radial component, drawn as the true projection
L = 330;
quiver(xs, ys, L, 0, 0, 'Color',[0.10 0.10 0.10], 'LineWidth',1.5, 'MaxHeadSize',0.9);
text(xs+L/2, ys+100, 'v', 'FontSize',11, 'HorizontalAlignment','center');
vr = geo.v*dot([1 0], uaway);                       % away-positive radial speed, m/s
d  = (vr/geo.v)*L*uaway;                            % drawn at the same scale as v
quiver(xs, ys, d(1), d(2), 0, 'Color',[0.85 0.33 0.10], 'LineWidth',1.5, 'MaxHeadSize',0.9);
plot([xs+L, xs+d(1)],[ys, ys+d(2)], ':', 'Color',[0.55 0.55 0.55], 'LineWidth',1.0);
text(xs+d(1)+70, ys+d(2)-40, ['v_r = ' num2str(vr,'%.2f') ' m/s'], ...
     'FontSize',8, 'Color',[0.85 0.33 0.10]);

xlim([-1050 950]); ylim([-180 1480]); grid on; box on;
set(gca,'YTick',0:250:1250);
xlabel('along-track position (m)'); ylabel('cross-track distance (m)');
title('(a) plan view of the motion geometry','FontSize',9);

% ---------------- (b) received frequency ----------------
subplot(1,2,2); hold on;
plot(t, ftrue, 'Color',[0.64 0.08 0.18], 'LineWidth',1.6);
yline(geo.f0, 'k--', 'LineWidth',0.9);
xline(geo.t_cpa_rx, 'k:', 'LineWidth',0.9);
text(geo.t_cpa_rx-8, geo.f0+0.075, ...
     ['t_{CPA,rx} = \tau_c + d_c/c = ' num2str(geo.t_cpa_rx) ' s'], ...
     'FontSize',8, 'HorizontalAlignment','right');
text(30, geo.f0+0.115, 'approaching:  f_r > f_0', 'FontSize',9, 'Color',[0.2 0.2 0.2]);
text(195, geo.f0-0.125, 'receding:  f_r < f_0', 'FontSize',9, 'Color',[0.2 0.2 0.2]);
text(6, geo.f0+0.013, 'f_0', 'FontSize',10);
grid on; box on; xlim([0 300]); ylim([99.78 100.22]);
xlabel('reception time t (s)'); ylabel('received frequency f_r(t)  (Hz)');
title('(b) received frequency trajectory','FontSize',9);

exportgraphics(fig, fullfile(figdir,'fig_geometry.png'),'Resolution',200);
savefig(fig, fullfile(figdir,'fig_geometry.fig'));
try, exportgraphics(fig, fullfile(figdir,'fig_geometry.pdf'),'ContentType','vector'); catch, end
close(fig);

% numeric companions for the caption
fprintf('geometry: f_r span %.5f .. %.5f Hz, f0 = %.2f Hz\n', min(ftrue), max(ftrue), geo.f0);
fprintf('      f_r(t_cpa_rx) - f0 = %.3e Hz (crossing check)\n', ...
    interp1(t, ftrue, geo.t_cpa_rx) - geo.f0);
fprintf('      total excursion %.4f Hz = %.1f bins of 1/290 s\n', ...
    max(ftrue)-min(ftrue), (max(ftrue)-min(ftrue))*290);
fprintf('geometry figure written to %s\n', figdir);
end
