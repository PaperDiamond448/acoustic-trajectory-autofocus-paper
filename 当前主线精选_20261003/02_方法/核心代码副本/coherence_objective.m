function [f, grad] = coherence_objective(u, ctx)
%COHERENCE_OBJECTIVE  f = -J_h(u),  J_h = Q_h - lambda_C ||D2 u||^2/(P-2)
%   Q_h(u) = sum_b |R_b(u)|^2 / N_b  /  E,   R_b = sum_{n in block b} z_u[n]
%   z_u[n] = y[n] exp(-j (phiA[n] + H(n,:) u))   on the evaluation interval only.
u = u(:);
ph = ctx.phiA + ctx.H*u;
z  = ctx.y .* exp(-1j*ph);
Q  = 0;  G = zeros(ctx.P,1);
for b = 1:numel(ctx.blk)
    ix = ctx.blk{b};
    Rb = sum(z(ix));
    nb = numel(ix);
    Q  = Q + (abs(Rb)^2)/nb;
    Gb = -1j*(ctx.H(ix,:).' * z(ix));            % d R_b / d u_p
    G  = G + (2/nb)*real(conj(Rb)*Gb);
end
Q = Q/ctx.E;   G = G/ctx.E;
DtD = ctx.DtD;
reg  = ctx.lambda*(u.'*DtD*u)/(ctx.P-2);
regg = 2*ctx.lambda*(DtD*u)/(ctx.P-2);
f = -(Q - reg);
if nargout > 1
    grad = -G + regg;
end
end
