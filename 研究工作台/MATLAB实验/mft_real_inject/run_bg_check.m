function BG = run_bg_check(outdir)
%RUN_BG_CHECK  Pre-declared background inspection and channel selection.
%
%   Runs BEFORE any estimator touches the measured data.  It (a) verifies the
%   SIO header against the frozen configuration, (b) verifies the custom reader
%   against the distributed sioread.m, (c) verifies the band-selection baseband
%   against a direct time-domain mix-and-average, (d) measures the four
%   background windows on all 27 elements, and (e) applies the frozen channel
%   rule of real_config.
if nargin < 1, outdir = fullfile(pwd,'results','bg'); end
if ~exist(outdir,'dir'), mkdir(outdir); end
R = real_config();

%% 0 header
[~, hdr] = sio_read_channel(R.file, 1, 0, 8);
assert(hdr.nc == R.n_chan && hdr.np == R.n_raw, 'header does not match real_config');
fprintf('header: %d channels, %d points/channel = %.3f s at %.1f Hz, %d bytes/point, %s-endian\n', ...
    hdr.nc, hdr.np, hdr.np/R.fs_raw, R.fs_raw, hdr.sl, hdr.endian);

%% 1 reader agreement with the distributed sioread
% Offset chosen so that sioread's own pp1 branch is exercised correctly
% (n0+1 is NOT a multiple of the 4096-point record length).
n0 = 900*3276.8;  nchk = 20000;  cchk = 7;
a = double(sio_read_channel(R.file, cchk, n0, nchk));
b = double(sioread(R.file, n0+1, nchk, cchk));
e_read = max(abs(a - b(:)));
fprintf('reader vs sioread on %d points of channel %d: max |diff| = %g\n', nchk, cchk, e_read);
assert(e_read == 0, 'reader disagrees with sioread');

%% 2 baseband conversion agrees with a direct mix-decimate on a clean tone
% A synthetic tone at fref + f1 must come back at f1 with unit gain.
fs0 = R.fs_raw; Ltot = R.win_len_s + 2*R.guard_s; N = round(Ltot*fs0);
tt = (0:N-1)'/fs0; ph1 = 0.913;
ng = round(R.guard_s*R.fs);
tb = ((0:round(R.win_len_s*R.fs)-1)' + ng)/R.fs;
% (i) ON a DFT bin the conversion must be exact to machine precision.
f1 = 234/(R.win_len_s + 2*R.guard_s);            % 0.73125 Hz, exactly on a bin
zt = bb_convert(cos(2*pi*(R.fref+f1)*tt + ph1), R);
e_bb = max(abs(zt - 0.5*exp(1j*(2*pi*f1*tb + ph1))));   % real cosine -> half amplitude
% (ii) OFF a bin a finite-window tone is not band-limited, so the discarded
%      sinc tails beyond +-keep_hz leave a small residue.  That residue is a
%      property of truncating a tone, not of the conversion, and it is two
%      orders of magnitude below the weakest injected amplitude
%      (10^(-20/20) = 0.1).
f2 = 0.7312;
zt2 = bb_convert(cos(2*pi*(R.fref+f2)*tt + ph1), R);
e_leak = max(abs(zt2 - 0.5*exp(1j*(2*pi*f2*tb + ph1))));
fprintf('baseband conversion: on-bin max |err| = %.3e; off-bin truncation residue = %.3e\n', ...
    e_bb, e_leak);
assert(e_bb < 1e-9, 'baseband conversion is not exact on an on-bin tone');
assert(e_leak < 1e-3, 'off-bin truncation residue larger than expected');

%% 3 measure every element on the four windows
rows = {};
for c = 1:R.n_chan
    for w = 1:numel(R.win_start_s)
        [z, info] = load_real_baseband(R, c, R.win_start_s(w));
        rows(end+1,:) = {c, R.win_start_s(w), info.clip_max_abs, info.raw_rms, ...
            10*log10(info.inband_power), 10*log10(info.band2_power), ...
            10*log10(median(abs(z).^2))}; %#ok<AGROW>
    end
end
T = cell2table(rows,'VariableNames',{'chan','t0_s','clip_max_abs','raw_rms', ...
    'p_pm10hz_db','p_pm2hz_db','p_median_db'});
writetable(T, fullfile(outdir,'background_channels.csv'));

%% 4 apply the frozen channel rule
clipped = false(R.n_chan,1);  pmed = zeros(R.n_chan,1);
for c = 1:R.n_chan
    k = T.chan == c;
    clipped(c) = any(T.clip_max_abs(k) >= R.chan_rule.clip_abs);
    pmed(c) = median(T.p_pm2hz_db(k));
end
ref_db = median(pmed);
dev = pmed - ref_db;
ok = ~clipped & abs(dev) <= R.chan_rule.max_dev_db;
cand = find(ok);
assert(~isempty(cand), 'no channel survives the declared rule');
[~, ib] = min(abs(dev(cand)));
chan = cand(ib);

S = table((1:R.n_chan)', clipped, pmed, dev, ok, 'VariableNames', ...
    {'chan','clipped','p_pm2hz_median_db','dev_from_median_db','survives'});
writetable(S, fullfile(outdir,'channel_rule.csv'));
fprintf('\nchannel rule: %d clipped, %d outside +-%g dB, %d survive; SELECTED channel %d (dev %+.2f dB)\n', ...
    sum(clipped), sum(~clipped & abs(dev) > R.chan_rule.max_dev_db), R.chan_rule.max_dev_db, numel(cand), chan, dev(chan));

%% 5 background spectrum of the selected channel, for the record
Pw = zeros(R.win_len_s*R.fs, numel(R.win_start_s));
for w = 1:numel(R.win_start_s)
    z = load_real_baseband(R, chan, R.win_start_s(w));
    Pw(:,w) = abs(fft(z.*hann(numel(z),'symmetric'))).^2/sum(hann(numel(z),'symmetric').^2);
end
n = size(Pw,1);
f = (0:n-1)'*R.fs/n;  f(f >= R.fs/2) = f(f >= R.fs/2) - R.fs;
[f, ord] = sort(f);  Pw = Pw(ord,:);
sel = abs(f) <= R.keep_hz;
SP = array2table([f(sel) 10*log10(Pw(sel,:))], 'VariableNames', ...
    ['f_hz', arrayfun(@(t) sprintf('w%d_db',t), R.win_start_s, 'UniformOutput', false)]);
writetable(SP, fullfile(outdir,'background_spectrum_selected.csv'));

BG = struct('header', hdr, 'reader_max_diff', e_read, 'baseband_max_err', e_bb, 'baseband_offbin_residue', e_leak, ...
    'selected_channel', chan, 'dev_db', dev(chan), 'n_survivors', numel(cand), ...
    'clipped_channels', find(clipped)', 'ref_p_pm2hz_db', ref_db, ...
    'windows_s', R.win_start_s, 'config', R);
fid = fopen(fullfile(outdir,'bg_check.json'),'w');
fprintf(fid,'%s', jsonencode(BG,'PrettyPrint',true)); fclose(fid);
fprintf('frozen channel written to results/bg/bg_check.json; set R.chan_fixed = %d in real_config.m\n', chan);
end

function z = bb_convert(x, R)
%BB_CONVERT  Same band selection as load_real_baseband, on an in-memory signal.
Ntot = numel(x);
df = R.fs_raw/Ntot;
kc = round(R.fref/df); kh = round(R.keep_hz/df);
N2 = 2*kh;
X = fft(x);
Y = zeros(N2,1);
Y(1:kh)    = X(kc + (0:kh-1) + 1);
Y(kh+1:N2) = X(kc + (-kh:-1)  + 1);
z = ifft(Y)*(N2/Ntot);
ng = round(R.guard_s*R.fs);
z = z(ng+1 : ng + round(R.win_len_s*R.fs));
end
