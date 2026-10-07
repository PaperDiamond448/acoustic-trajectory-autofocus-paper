function out = estimate_b1(fe, mcfg)
%ESTIMATE_B1  Fixed-transition banded HMM/DP reference tracker.
%   score   R_k(m) = |C_k(g_m)|^2 / (sigma_hat^2 * sum w^2),  l = log(1+R)
%   transition: |dg| <= max_step per 1 s hop, N(0,sigma_step) kernel, row-normalised
%   V_1 = l_1 - log M ;  V_k(j) = l_k(j) + max_i [ V_{k-1}(i) + log T(i,j) ]
g  = fe.g_coarse;  M = numel(g);  K = fe.K;  dg = fe.df_coarse;
R  = abs(fe.C_coarse).^2 / max(fe.noise_hat*fe.sumw2, realmin);
LL = log1p(R);

[logT, off] = band_logT(M, dg, mcfg.max_step, mcfg.sigma_step);
[path, out.dp_score] = dp_viterbi(LL, logT, off);
out.path = path;
out.g_raw = g(path);
out.g_frame = medfilt1(out.g_raw, mcfg.median_len, [], 1, 'omitnan', 'truncate');
out.g = interp_const(fe.tc, out.g_frame, fe.t);
end
