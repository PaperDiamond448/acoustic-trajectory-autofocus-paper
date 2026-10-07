function [lo, hi] = wilson_interval(k, n, z)
%WILSON_INTERVAL  Wilson score interval for a binomial proportion (default 95%).
if nargin < 3, z = 1.959963984540054; end
if n == 0, lo = NaN; hi = NaN; return; end
p  = k/n;
d  = 1 + z^2/n;
ctr= (p + z^2/(2*n))/d;
hw = (z/d)*sqrt(p*(1-p)/n + z^2/(4*n^2));
lo = max(0, ctr - hw);
hi = min(1, ctr + hw);
end
