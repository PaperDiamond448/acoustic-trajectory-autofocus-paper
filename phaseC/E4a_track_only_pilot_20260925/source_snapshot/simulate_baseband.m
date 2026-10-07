function rec = simulate_baseband(cfg, scene, snr_db, seed, geo_mode)
%SIMULATE_BASEBAND  E-protocol record generator (20 Hz complex baseband, 300 s).
%
%   scene   : 'S0' | 'S1' | 'S2' | 'H0_0' | 'H0_I'
%   snr_db  : 20 Hz complex-baseband SAMPLE SNR at nominal amplitude a(t)=1
%   geo_mode: 'dev' (fixed development geometry) | 'eval' (randomised)
%
%   y[n] = A a(t) exp(j phi_g(t)) + i[n] + w[n],   E|w|^2 = 1,  A = 10^(SNR/20)
%   phi_g(t) = 2 pi f0 tau(t) - 2 pi fref t + phi0
%
%   The returned struct separates rec.y / rec.t (what an estimator may see) from
%   rec.truth (generation ground truth, post-hoc evaluation only).

B  = cfg.B;
rs = RandStream('mt19937ar','Seed',seed);

% --- fixed random draw order, identical for every scene (paired structure) ---
u3 = rand(rs,3,1);
phi0 = 2*pi*rand(rs);
phi_i= 2*pi*rand(rs);

geo.c = B.c;  geo.dc = B.dc;
if strcmpi(geo_mode,'dev')
    geo.f0 = B.dev_geo.f0;  geo.v = B.dev_geo.v;  geo.t_cpa_rx = B.dev_geo.t_cpa_rx;
else
    geo.f0       = B.eval_geo.f0(1)       + diff(B.eval_geo.f0)      *u3(1);
    geo.v        = B.eval_geo.v(1)        + diff(B.eval_geo.v)       *u3(2);
    geo.t_cpa_rx = B.eval_geo.t_cpa_rx(1) + diff(B.eval_geo.t_cpa_rx)*u3(3);
end

N = B.N;  t = (0:N-1)'/B.fs;
[tau, ftrue] = geometry_tau(t, geo);
phig  = 2*pi*geo.f0*tau - 2*pi*B.fref*t + phi0;
gtrue = ftrue - B.fref;

hfade = envelope_h(t, B.fade);
hintf = envelope_h(t, B.intf);

A = 10^(snr_db/20);
a = ones(N,1);
intf = zeros(N,1);
switch upper(scene)
    case 'S0'
    case 'S1'
        a = 1 - (1-B.fade.floor)*hfade;
    case 'S2'
        intf = B.intf.amp * hintf .* exp(1j*(phig + 2*pi*B.intf.df_hz*t + phi_i));
    case 'H0_0'
        A = 0;
    case 'H0_I'
        A = 0;
        intf = B.intf.amp * hintf .* exp(1j*(phig + 2*pi*B.intf.df_hz*t + phi_i));
    otherwise
        error('unknown scene %s', scene);
end

s_target = A * a .* exp(1j*phig);
nz = randn(rs, N, 2);
w  = (nz(:,1) + 1j*nz(:,2))/sqrt(2);
y  = s_target + intf + w;

rec.y = y;  rec.t = t;  rec.fs = B.fs;
rec.truth = struct('scene',upper(scene),'snr_db',snr_db,'seed',seed, ...
    'geo',geo,'phi0',phi0,'phi_i',phi_i,'gtrue',gtrue,'phig',phig, ...
    'amp',a,'s_target',s_target,'intf',intf,'has_target',A>0, ...
    'mean_snr_db',10*log10(max(A^2*mean(a.^2),realmin)));
end
