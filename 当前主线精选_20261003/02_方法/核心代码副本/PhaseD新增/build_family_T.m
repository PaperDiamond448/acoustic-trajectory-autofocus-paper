function fam = build_family_T(t, tc, gA, mcfg, Delta, T, ubvec)
%BUILD_FAMILY  The single continuous correction family shared by B2 and P.
%
%   g_u(t) = gA(t) + r * B(t) * u,   r = mcfg.radius,  -1 <= u_p <= 1
%   B  : piecewise-linear partition of unity on knots 0:knot_ds:300 (21 knots)
%   Band constraint -2 <= g_u(t) <= 2 imposed at the union of frame centres,
%   correction knots and the two record end times (both g_A and B are piecewise
%   linear, so the union of breakpoints certifies every interior point).

t = t(:); tc = tc(:); gA = gA(:);
assert(abs(T/Delta-round(T/Delta))<1e-10);
knots = (0:Delta:T)';
P = numel(knots);
fam.knots = knots;  fam.P = P;  fam.r = 0.02;
fam.Bt  = hat_basis(t , knots);
fam.Btc = hat_basis(tc, knots);
fam.D2  = second_difference_matrix(P);

tchk = unique([tc; knots; t(1); t(end)]);
tchk = tchk(tchk >= t(1) & tchk <= t(end));
Bchk = hat_basis(tchk, knots);
gAchk= interp_const(t, gA, tchk);
fam.tchk = tchk;  fam.Bchk = Bchk;  fam.gAchk = gAchk;
fam.Aineq = [ fam.r*Bchk; -fam.r*Bchk ];
fam.bineq = [ mcfg.band(2)-gAchk ; gAchk-mcfg.band(1) ];
if isscalar(ubvec), ubvec=ubvec*ones(P,1); end
assert(numel(ubvec)==P && all(ubvec>=0));
fam.lb = -ubvec(:);
fam.ub = ubvec(:);

fam.gA   = gA;
fam.phiA = 2*pi*cumtrapz(t, gA);
fam.H    = 2*pi*fam.r*cumtrapz(t, fam.Bt);       % N x P phase basis
end

function B = hat_basis(x, knots)
x = x(:); knots = knots(:); P = numel(knots);
B = zeros(numel(x), P);
for p = 1:P
    if p > 1
        m = x >= knots(p-1) & x < knots(p);
        B(m,p) = (x(m)-knots(p-1))/(knots(p)-knots(p-1));
    end
    if p < P
        m = x >= knots(p) & x < knots(p+1);
        B(m,p) = (knots(p+1)-x(m))/(knots(p+1)-knots(p));
    end
end
m = x >= knots(end);  B(m,:) = 0;  B(m,P) = 1;     % right end
m = x <  knots(1);    B(m,:) = 0;  B(m,1) = 1;     % left  end
end
