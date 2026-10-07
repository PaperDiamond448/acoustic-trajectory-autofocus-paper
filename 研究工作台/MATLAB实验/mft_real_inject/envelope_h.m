function h = envelope_h(t, ev)
%ENVELOPE_H  Raised-cosine gate used by the fade (S1) and interference (S2) scenes.
%   ev.center_s, ev.plateau_duration_s, ev.edge_duration_s
%   Default protocol: 0 before 140 s, cosine rise 140-142 s, 1 on 142-158 s,
%   cosine fall 158-160 s, 0 after 160 s.
c0 = ev.center_s; P = ev.plateau_duration_s; E = ev.edge_duration_s;
t1 = c0 - P/2 - E;  t2 = c0 - P/2;  t3 = c0 + P/2;  t4 = c0 + P/2 + E;
h = zeros(size(t));
m = (t >= t1) & (t <  t2);  h(m) = 0.5*(1 - cos(pi*(t(m)-t1)/E));
m = (t >= t2) & (t <= t3);  h(m) = 1;
m = (t >  t3) & (t <= t4);  h(m) = 0.5*(1 + cos(pi*(t(m)-t3)/E));
end
