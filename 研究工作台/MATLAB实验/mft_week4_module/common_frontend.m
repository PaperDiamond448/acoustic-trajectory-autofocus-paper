function fe = common_frontend(y, t, fcfg)
%COMMON_FRONTEND  Shared preprocessing for all four methods on one record.
%   fcfg fields: fs, L, D, df_fine, band, coarse_dec, noise_bands
%   Uses only the observation y and its time axis -- no simulator metadata.

fs = fcfg.fs;  L = fcfg.L;  D = fcfg.D;  N = numel(y);
K  = floor((N-L)/D) + 1;
idx = (0:L-1)' + (0:K-1)*D + 1;                 % L x K sample indices (1-based)
w   = hann(L,'symmetric');
S   = y(idx) .* w;                              % L x K windowed frames

fe.fs = fs; fe.L = L; fe.D = D; fe.K = K; fe.N = N;
fe.w = w; fe.sumw2 = sum(w.^2); fe.sumw = sum(w);
fe.S = S;
fe.frame_idx = idx;
fe.tc = (((0:K-1)*D) + (L-1)/2)'/fs;            % frame CENTRE times
fe.nvec = (0:L-1)'/fs;
fe.t = t(:);

% --- fine matching grid (B0) and its 5x decimation (B1) ---
gf  = (fcfg.band(1):fcfg.df_fine:fcfg.band(2))';
fe.g_fine = gf;  fe.df_fine = fcfg.df_fine;
fe.C = czt_match(S, fs, gf(1), fcfg.df_fine, numel(gf));
fe.g_coarse = gf(1:fcfg.coarse_dec:end);
fe.C_coarse = fe.C(1:fcfg.coarse_dec:end, :);
fe.df_coarse= fcfg.df_fine*fcfg.coarse_dec;

% --- background scale from side bands of the whole-record Hann periodogram ---
wN = hann(N,'symmetric');
P  = abs(fft(y(:).*wN)).^2 / sum(wN.^2);
f  = (0:N-1)'*fs/N;  f(f >= fs/2) = f(f >= fs/2) - fs;
sel = false(N,1);
for r = 1:size(fcfg.noise_bands,1)
    sel = sel | (f >= fcfg.noise_bands(r,1) & f <= fcfg.noise_bands(r,2));
end
fe.noise_hat = median(P(sel))/log(2);
fe.noise_bins = sum(sel);
end
