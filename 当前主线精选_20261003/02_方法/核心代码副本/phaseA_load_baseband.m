function [z, info] = phaseA_load_baseband(file, chan, fref, fs, keep_hz, fs_raw, n_raw, t0_s, win_len_s, guard_lo_s, guard_hi_s)
%PHASEA_LOAD_BASEBAND  Generalised version of mft_real_inject/load_real_baseband.m.
%
%   Same exact-DFT-bin band selection and inverse transform, but:
%   (1) fref may be any value that lands on a bin (not fixed at 100 Hz);
%   (2) the two guards may be unequal and either may be 0, so windows that
%       touch the absolute start (t=0) or end (t=3000 s) of the record can be
%       requested without violating load_real_baseband's symmetric-guard
%       assertion.
%
%   This function is NEW CODE (declared deviation, see REPORT.md): it exists
%   because load_real_baseband.m is frozen to exactly R.win_len_s=300 s with
%   a symmetric 10 s guard and R.fref=100 Hz, and cannot cover t0_s in
%   {0, 2700} (edge windows) or fref=94 (route-1 tracking) without editing a
%   frozen file. The band-selection algorithm itself is copied unchanged from
%   load_real_baseband.m; equivalence is checked in run_A3_visibility.m
%   against load_real_baseband.m's own output on one of its frozen windows.
%
%   [z, info] = phaseA_load_baseband(file, chan, fref, fs, keep_hz, ...
%                                     fs_raw, n_raw, t0_s, win_len_s, ...
%                                     guard_lo_s, guard_hi_s)

n0   = round((t0_s - guard_lo_s)*fs_raw);
Ntot = round((win_len_s + guard_lo_s + guard_hi_s)*fs_raw);
assert(abs(Ntot - (win_len_s+guard_lo_s+guard_hi_s)*fs_raw) < 1e-6, 'segment must be a whole number of raw samples');
assert(n0 >= 0 && n0 + Ntot <= n_raw, 'segment [%g,%g) s outside the record', t0_s-guard_lo_s, t0_s+win_len_s+guard_hi_s);

x = double(sio_read_channel(file, chan, n0, Ntot));

df = fs_raw/Ntot;
kc = fref/df;    assert(abs(kc-round(kc)) < 1e-9, 'fref must land on a bin of this segment length');
kh = keep_hz/df; assert(abs(kh-round(kh)) < 1e-9, 'keep_hz must land on a bin of this segment length');
kc = round(kc); kh = round(kh);
N2 = 2*kh;
assert(mod(N2, 1) == 0, 'baseband length must be an integer');

X = fft(x);
Y = zeros(N2,1);
Y(1:kh)    = X(kc + (0:kh-1) + 1);
Y(kh+1:N2) = X(kc + (-kh:-1)  + 1);
z = ifft(Y)*(N2/Ntot);

ng_lo = round(guard_lo_s*fs);
n_out = round(win_len_s*fs);
z = z(ng_lo+1 : ng_lo+n_out);

info = struct('chan',chan,'fref',fref,'t0_s',t0_s,'win_len_s',win_len_s, ...
    'guard_lo_s',guard_lo_s,'guard_hi_s',guard_hi_s,'n0_raw',n0,'n_raw_read',Ntot, ...
    'df_hz',df,'bin_centre',kc,'bin_half',kh,'fs',fs,'n_out',numel(z), ...
    'clip_max_abs',max(abs(x)),'inband_power',mean(abs(z).^2));
end
