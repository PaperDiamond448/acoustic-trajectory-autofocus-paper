function lof = compute_lofar(z, fs, L, D, nfft)
%COMPUTE_LOFAR  Sliding-window LOFARgram of a complex baseband series.
%   Hann window of length L samples, hop D samples, FFT zero-padded to nfft
%   for display/peak-localisation smoothness only; the physical frequency
%   resolution (mainlobe width) remains fs/L, set by the window, not by the
%   padded grid -- padding only interpolates the same windowed DTFT more
%   densely, it does not add resolution.
%
%   lof = compute_lofar(z, fs, L, D, nfft)
%   Returns struct with fields:
%     tc   : 1 x K frame centre times (s)
%     freq : nfft x 1 baseband frequency axis (Hz), fftshift'ed, ascending
%     P_db : nfft x K power in dB (10*log10 of |STFT|^2 / sum(w.^2))

N = numel(z);
K = floor((N - L)/D) + 1;
w = hann(L, 'symmetric');
sumw2 = sum(w.^2);

freq = ((0:nfft-1)' - floor(nfft/2)) * (fs/nfft);   % fftshift'ed axis, ascending, centred near 0
P_db = zeros(nfft, K);
for k = 1:K
    idx = (k-1)*D + (1:L);
    frame = z(idx) .* w;
    Sf = fft(frame, nfft);
    Sf = fftshift(Sf);
    P_db(:,k) = 10*log10(max(abs(Sf).^2 / sumw2, realmin));
end
tc = ((0:K-1)*D + (L-1)/2) / fs;

lof = struct('tc', tc, 'freq', freq, 'P_db', P_db, 'L', L, 'D', D, 'fs', fs, 'nfft', nfft, ...
    'note', 'physical mainlobe resolution = fs/L Hz; nfft only interpolates the same window DTFT');
end
