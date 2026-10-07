function C = czt_match(S, fs, g0, dg, M)
%CZT_MATCH  C(m,k) = sum_n S(n,k) exp(-j 2 pi (g0+(m-1)dg) n / fs),  n = 0..L-1
%   Chirp-z parameters: A = exp(+j2*pi*g0/fs), W = exp(-j2*pi*dg/fs), because
%   MATLAB's czt evaluates  X(k) = sum_n x(n) A^-n W^(nk).
a = exp( 1j*2*pi*g0/fs);
w = exp(-1j*2*pi*dg/fs);
C = czt(S, M, w, a);
end
