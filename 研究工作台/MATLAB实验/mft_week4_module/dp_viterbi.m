function [path, score, V] = dp_viterbi(LL, logT, off)
%DP_VITERBI  Banded max-product Viterbi.
%   LL   : M x K observation log-scores
%   logT : M x nOff, logT(i,o) = log T(i, i+off(o))   (-Inf where infeasible)
%   V_1(j) = LL(j,1) - log M ;  V_k(j) = LL(j,k) + max_i [ V_{k-1}(i) + logT(i,j) ]
[M, K] = size(LL);
off = off(:);  nO = numel(off);
V = LL(:,1) - log(M);
ptr = zeros(M, K, 'int32');
for k = 2:K
    cand = -inf(M, nO);
    for o = 1:nO
        d = off(o);
        j = max(1, 1+d):min(M, M+d);
        i = j - d;
        cand(j, o) = V(i) + logT(i, o);
    end
    [best, bo] = max(cand, [], 2);
    V = LL(:,k) + best;
    ptr(:,k) = int32((1:M)' - off(bo));
end
[score, je] = max(V);
path = zeros(K,1); path(K) = je;
for k = K:-1:2, path(k-1) = double(ptr(path(k), k)); end
end
