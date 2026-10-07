function [z, info] = load_real_baseband(R, chan, t0_s)
%LOAD_REAL_BASEBAND  One 300 s complex baseband window of measured background.
%
%   [z, info] = load_real_baseband(R, chan, t0_s)
%
%   Reads channel CHAN of the SIO file for the interval
%   [t0_s - guard, t0_s + win_len + guard), selects the DFT bins that lie in
%   fref +- keep_hz, transforms back at R.fs, and drops the guard.  The result
%   is the exact band-limited complex baseband of the recorded pressure on that
%   element: no filter is designed, no rational resampler is used, and no block
%   edge is wrapped into the returned data.
%
%   The returned z is NOT normalised; run_real_inject scales it.

fs0 = R.fs_raw;
Ltot_s = R.win_len_s + 2*R.guard_s;
n0  = round((t0_s - R.guard_s)*fs0);
Ntot= round(Ltot_s*fs0);
assert(abs(Ntot - Ltot_s*fs0) < 1e-6, 'segment must be a whole number of samples');
assert(n0 >= 0 && n0 + Ntot <= R.n_raw, 'segment outside the record');

x = double(sio_read_channel(R.file, chan, n0, Ntot));

% ---- exact band selection ----
df   = fs0/Ntot;                             % = 1/Ltot_s
kc   = R.fref/df;    assert(abs(kc-round(kc))    < 1e-9, 'fref must land on a bin');
kh   = R.keep_hz/df; assert(abs(kh-round(kh))    < 1e-9, 'keep_hz must land on a bin');
kc = round(kc); kh = round(kh);
N2 = 2*kh;                                   % baseband length at R.fs
assert(abs(N2 - Ltot_s*R.fs) < 1e-9, 'baseband length must be an integer');

X = fft(x);
Y = zeros(N2,1);
Y(1:kh)      = X(kc + (0:kh-1) + 1);         % 0 .. +keep_hz-df
Y(kh+1:N2)   = X(kc + (-kh:-1)  + 1);        % -keep_hz .. -df
z = ifft(Y)*(N2/Ntot);

% ---- drop the guard ----
ng = round(R.guard_s*R.fs);
z  = z(ng+1 : ng + round(R.win_len_s*R.fs));

info = struct('chan',chan,'t0_s',t0_s,'n0_raw',n0,'n_raw',Ntot, ...
    'df_hz',df,'bin_centre',kc,'bin_half',kh,'fs',R.fs,'n_out',numel(z), ...
    'clip_max_abs',max(abs(x)), ...
    'inband_power',mean(abs(z).^2), ...
    'band2_power',bandpower_hz(z, R.fs, R.band), ...
    'raw_rms',sqrt(mean(x.^2)));
end

function p = bandpower_hz(z, fs, band)
n = numel(z);
Z = fft(z)/n;
f = (0:n-1)'*fs/n;  f(f >= fs/2) = f(f >= fs/2) - fs;
sel = f >= band(1) & f <= band(2);
p = sum(abs(Z(sel)).^2);        % mean-square contribution of that band
end
