function out = estimate_b0(fe, mcfg)
%ESTIMATE_B0  Source-paper tracker: per-frame max matching, per-frame max
%   normalisation, 5-frame moving median, linear interpolation.
S = abs(fe.C);
mx = max(S, [], 1);
zerof = (mx <= 0);
Sn = S ./ max(mx, realmin);
Sn(:, zerof) = 0;
[~, im] = max(Sn, [], 1);
gk = fe.g_fine(im);
gk(zerof) = 0;                                    % explicit all-zero frame rule
out.g_raw = gk(:);
out.g_frame = medfilt1(out.g_raw, mcfg.median_len, [], 1, 'omitnan', 'truncate');
out.g = interp_const(fe.tc, out.g_frame, fe.t);
out.zero_frames = sum(zerof);
end
