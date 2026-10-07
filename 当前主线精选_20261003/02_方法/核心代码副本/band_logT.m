function [logT, off] = band_logT(M, dg, max_step, sigma_step)
%BAND_LOGT  Row-normalised banded Gaussian transition kernel in log domain.
ns  = round(max_step/dg);
off = (-ns:ns)';
kern= exp(-0.5*((off*dg)/sigma_step).^2);
logT = -inf(M, numel(off));
for i = 1:M
    j = i + off;
    ok = j >= 1 & j <= M;
    kk = kern; kk(~ok) = 0;
    kk = kk / sum(kk);
    logT(i, ok) = log(kk(ok));
end
end
