function out = estimate_b2(fe, fam, mcfg)
%ESTIMATE_B2  Conventional continuous refinement: bounded per-frame CW power
%   maximisation around g_A, then a constrained smooth correction fitted in the
%   SHARED family (same knots, same 21 coefficients, same bounds as P).
K = fe.K;  r = fam.r;  P = fam.P;
gAc = interp_const(fe.t, fam.gA, fe.tc);
gloc = zeros(K,1);
opt = optimset('TolX', mcfg.tol_x);
for k = 1:K
    sk = fe.S(:,k);
    c0 = gAc(k);
    lo = max(c0 - mcfg.radius, mcfg.band(1));
    hi = min(c0 + mcfg.radius, mcfg.band(2));
    f = @(g) -abs(sum(sk .* exp(-1j*2*pi*g*fe.nvec)))^2;
    if hi > lo
        gs = fminbnd(f, lo, hi, opt);
    else
        gs = c0;
    end
    cand = [gs; lo; hi; c0];
    vals = arrayfun(f, cand);
    [~, ib] = min(vals);
    gloc(k) = cand(ib);
end
out.g_local = gloc;

% constrained quadratic fit inside the shared family
b  = (gloc - gAc)/r;
A  = fam.Btc;
lamF = mcfg.lambda_F;
Cq = [A/sqrt(K); sqrt(lamF/(P-2))*fam.D2];
dq = [b/sqrt(K); zeros(P-2,1)];
o  = optimoptions('lsqlin','Display','off','Algorithm','interior-point');
[u, ~, ~, exitflag] = lsqlin(Cq, dq, fam.Aineq, fam.bineq, [], [], fam.lb, fam.ub, zeros(P,1), o);
if isempty(u) || exitflag <= 0
    u = zeros(P,1);
    out.fit_failed = true;
else
    out.fit_failed = false;
end
out.u = u(:);
out.exitflag = exitflag;
out.resid = A*out.u - b;
out.g = fam.gA + r*(fam.Bt*out.u);
end
