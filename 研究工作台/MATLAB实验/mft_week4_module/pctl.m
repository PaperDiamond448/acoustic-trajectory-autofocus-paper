function q = pctl(x, p)
%PCTL  Linear-interpolated percentile, independent of the Statistics Toolbox.
%   Matches MATLAB's quantile() midpoint convention.
x = sort(x(:));
n = numel(x);
if n == 0, q = NaN; return; end
if n == 1, q = x; return; end
pos = n*p + 0.5;
if pos <= 1, q = x(1); return; end
if pos >= n, q = x(n); return; end
lo = floor(pos); fr = pos - lo;
q = x(lo)*(1-fr) + x(lo+1)*fr;
end
