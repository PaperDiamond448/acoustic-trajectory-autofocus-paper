function make_figure_module(figdir)
%MAKE_FIGURE_MODULE  Block diagram of the coherent refinement module.
%
%   The arrows follow the computational dependence, not just the reading
%   order.  The raw complex record feeds three places: the trajectory front
%   end, the coherent objective inside the module, and the phase-compensation
%   and FFT back end.  The available trajectory and the initial coefficients
%   define the correction family and the feasible set, and nothing else.
if nargin < 1 || isempty(figdir), figdir = fullfile(pwd,'results','figures'); end
if ~exist(figdir,'dir'), mkdir(figdir); end

cMod = [0.94 0.95 0.99];   eMod = [0.20 0.30 0.70];
cFE  = [0.96 0.96 0.96];   eFE  = [0.45 0.45 0.45];
cBk  = [0.97 0.94 0.94];   eBk  = [0.64 0.08 0.18];
gry  = [0.30 0.30 0.30];

fig = figure('Visible','off','Position',[60 60 1220 580],'Color','w');
axes('Position',[0 0 1 1]); axis off;

% ---- module container ----------------------------------------------------
annotation(fig,'rectangle',[0.255 0.285 0.625 0.365], ...
    'FaceColor',cMod,'EdgeColor',eMod,'LineWidth',1.6);
annotation(fig,'textbox',[0.255 0.585 0.625 0.055], ...
    'String','coherence-driven constrained refinement', ...
    'HorizontalAlignment','center','VerticalAlignment','middle', ...
    'EdgeColor','none','FontSize',10.5,'FontWeight','bold','Color',eMod);

% ---- raw record ----------------------------------------------------------
box_(fig,[0.015 0.440 0.165 0.145], ...
     {'raw complex-baseband','record  y[n]'}, [1 1 1], [0.15 0.15 0.15], 9.5);

% ---- front end and its output -------------------------------------------
box_(fig,[0.240 0.790 0.255 0.150], ...
     {'\bftrajectory front end\rm  (replaceable)', ...
      'per-frame peak / Viterbi /','phase-continuous TBD / ...'}, cFE, eFE, 9);
box_(fig,[0.575 0.790 0.260 0.150], ...
     {'\bfmodule inputs from the front end\rm', ...
      'reference trajectory  g_{ref}(t)', ...
      'initial coefficients  u_0'}, cFE, eFE, 9);

% ---- inner blocks --------------------------------------------------------
yb = 0.330;  hb = 0.215;
box_(fig,[0.272 yb 0.165 hb], ...
     {'\bfbounded correction\rm','g_u(t) = g_{ref}(t) + \delta f_{max} B(t)u', ...
      '21 knots,  |u_p| \leq 1'}, [1 1 1], eMod, 9);
box_(fig,[0.460 yb 0.160 hb], ...
     {'\bfintegrated basis\rm','compensation phase', ...
      '\phi_u(t) = 2\pi\int_0^t g_u(\xi) d\xi'}, [1 1 1], eMod, 9);
box_(fig,[0.643 yb 0.160 hb], ...
     {'\bfcoherent objective\rm','J_h(u)  and its','analytic gradient'}, [1 1 1], eMod, 9);
box_(fig,[0.826 yb 0.042 hb], {'\bfSQP\rm'}, [1 1 1], eMod, 9);

% ---- back end ------------------------------------------------------------
box_(fig,[0.272 0.055 0.175 0.135], ...
     {'refined trajectory','g_{ref} + \delta f_{max} B(t)u*'}, cBk, eBk, 9);
box_(fig,[0.520 0.055 0.195 0.135], ...
     {'phase compensation','and full-length FFT'}, cBk, eBk, 9);
box_(fig,[0.780 0.055 0.190 0.135], ...
     {'residual-frequency peak','and detection statistic'}, cBk, eBk, 9);

% ---- arrows following the computational dependence -----------------------
% (1) y -> trajectory front end
seg(fig,[0.095 0.095],[0.570 0.865], gry);
arr(fig,[0.095 0.240],[0.865 0.865], gry);
% (2) front end -> the two module inputs
arr(fig,[0.495 0.575],[0.865 0.865], gry);
% (3) module inputs -> the correction family ONLY (centre and feasible set)
seg(fig,[0.705 0.705],[0.790 0.700], eMod);
seg(fig,[0.705 0.3545],[0.700 0.700], eMod);
arr(fig,[0.3545 0.3545],[0.700 0.547], eMod);
lbl(fig,[0.712 0.712 0.28 0.045], 'centre and \pm\delta f_{max} feasible set', eMod);
% (4) y -> the coherent objective: routed below the inner blocks so it does
%     not appear to pass through the correction or the integrated basis
seg(fig,[0.180 0.205],[0.5125 0.5125], gry);
seg(fig,[0.205 0.205],[0.5125 0.3070], gry);
seg(fig,[0.205 0.7230],[0.3070 0.3070], gry);
arr(fig,[0.7230 0.7230],[0.3070 0.3300], gry);
% (5) y -> the phase-compensation and FFT back end
seg(fig,[0.095 0.095],[0.440 0.0250], gry);
seg(fig,[0.095 0.6175],[0.0250 0.0250], gry);
arr(fig,[0.6175 0.6175],[0.0250 0.0550], gry);
% (6) inner chain
arr(fig,[0.437 0.460],[0.4375 0.4375], gry);
arr(fig,[0.620 0.643],[0.4375 0.4375], gry);
arr(fig,[0.803 0.826],[0.4375 0.4375], gry);
% (7) solver -> refined trajectory, connected with no gap
seg(fig,[0.847 0.847],[0.330 0.245], eMod);
seg(fig,[0.847 0.3595],[0.245 0.245], eMod);
arr(fig,[0.3595 0.3595],[0.245 0.190], eMod);
lbl(fig,[0.470 0.200 0.34 0.042],'warm-started stage schedule, fixed budget', eMod);
% (8) back end chain
arr(fig,[0.447 0.520],[0.1225 0.1225], gry);
arr(fig,[0.715 0.780],[0.1225 0.1225], gry);

exportgraphics(fig, fullfile(figdir,'fig_module.png'),'Resolution',200);
savefig(fig, fullfile(figdir,'fig_module.fig'));
try, exportgraphics(fig, fullfile(figdir,'fig_module.pdf'),'ContentType','vector'); catch, end
close(fig);
fprintf('module figure written to %s\n', figdir);
end

function box_(fig, pos, str, fc, ec, fs)
annotation(fig,'textbox',pos,'String',str,'HorizontalAlignment','center', ...
    'VerticalAlignment','middle','BackgroundColor',fc,'EdgeColor',ec, ...
    'LineWidth',1.2,'FontSize',fs,'Margin',4,'Interpreter','tex','FitBoxToText','off');
end

function arr(fig, x, y, c)
annotation(fig,'arrow',x,y,'Color',c,'LineWidth',1.2,'HeadLength',8,'HeadWidth',8);
end

function seg(fig, x, y, c)
annotation(fig,'line',x,y,'Color',c,'LineWidth',1.2);
end

function lbl(fig, pos, str, col)
annotation(fig,'textbox',pos,'String',str,'EdgeColor','none','FontSize',8, ...
    'Color',col,'HorizontalAlignment','center','VerticalAlignment','middle', ...
    'Interpreter','tex','FitBoxToText','off');
end
