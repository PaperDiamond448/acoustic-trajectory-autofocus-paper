function [tau, ftrue, rtau, tau_c] = geometry_tau(t, geo)
%GEOMETRY_TAU  Emission time, received instantaneous frequency and range.
%
%   geo fields: f0 (Hz), v (m/s), c (m/s), dc (m), t_cpa_rx (s, RECEPTION time of CPA)
%
%   Emission-time CPA:   tau_c = t_cpa_rx - dc/c
%   Causal propagation:  t = tau + r(tau)/c,  r(tau) = sqrt(dc^2 + v^2 (tau-tau_c)^2)
%   Closed form (minus root, the causal one):
%       tau(t) = [ c^2 t - v^2 tau_c - sqrt( c^2 v^2 (t-tau_c)^2 + (c^2-v^2) dc^2 ) ] / (c^2-v^2)
%   Received frequency:  f = f0 / (1 + vr/c),  vr = v^2 (tau-tau_c)/r(tau)

c = geo.c; v = geo.v; dc = geo.dc; f0 = geo.f0;
tau_c = geo.t_cpa_rx - dc/c;
den   = c^2 - v^2;
disc  = c^2*v^2*(t - tau_c).^2 + den*dc^2;
tau   = (c^2*t - v^2*tau_c - sqrt(disc)) / den;
rtau  = sqrt(dc^2 + v^2*(tau - tau_c).^2);
vr    = v^2*(tau - tau_c) ./ rtau;
ftrue = f0 ./ (1 + vr/c);
end
