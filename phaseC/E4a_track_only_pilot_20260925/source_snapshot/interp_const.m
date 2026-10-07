function y = interp_const(xk, yk, xq)
%INTERP_CONST  Linear interpolation with CONSTANT extension outside [xk(1),xk(end)].
xk = xk(:); yk = yk(:); sz = size(xq); xq = xq(:);
y = interp1(xk, yk, xq, 'linear');
y(xq < xk(1))   = yk(1);
y(xq > xk(end)) = yk(end);
y = reshape(y, sz);
end
