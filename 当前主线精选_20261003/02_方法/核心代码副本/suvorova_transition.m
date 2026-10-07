function tr = suvorova_transition(gvec, s)
%SUVOROVA_TRANSITION  Phase-wrapped Ornstein-Uhlenbeck transition kernel.
%
%   Implements Suvorova et al. (2018) Eqs. (3)-(13).  From Eqs. (3)-(4)
%       df/dt = -gamma f + sigma xi(t),      dphi/dt = 2 pi f
%   the forward solution over one step tau = Tdrift, starting from (f, phi), is
%   jointly Gaussian with
%       E[f']   = f e^{-gamma tau}
%       E[phi'] = phi + 2 pi f (1 - e^{-gamma tau}) / gamma
%       Var(f')      = sigma^2 (1 - e^{-2 gamma tau}) / (2 gamma)          (Eq.10)
%       Cov(f',phi') = 2 pi sigma^2 (1 - e^{-gamma tau})^2 / (2 gamma^2)   (Eq.11)
%       Var(phi')    = (2 pi)^2 sigma^2 [2 gamma tau - 3 + 4 e^{-gamma tau}
%                                        - e^{-2 gamma tau}] / (2 gamma^3) (Eq.12)
%   and phi' is wrapped modulo 2 pi, i.e. the sum over the integer m in Eq. (7).
%
%   NOTE ON THE PRINTED EQUATIONS.  The text available to us renders Eq. (9) as
%   "phi(t_{n+1}) - 2 pi m + f(t_{n+1})[1 - exp(-gamma tau)]/2" and gives
%   Eqs. (11)-(12) without the 2 pi factors.  Those forms are not dimensionally
%   consistent with dphi/dt = 2 pi f, so the expressions above are re-derived
%   from Eqs. (3)-(4) and the 2 pi factors restored.  The gamma -> 0 limits
%   (Var f -> sigma^2 tau, Cov -> 2 pi sigma^2 tau^2/2, Var phi ->
%   (2 pi)^2 sigma^2 tau^3/3) are checked numerically in run_checks_w3.
%
%   Because the joint law factorises as p(f') p(phi'|f'), the kernel is stored as
%       tr.logPf(i, d)        frequency part, source bin i, bin step d
%       tr.logPphi(i, d, k)   wrapped phase part, phase-bin difference k-1
%   which is what makes the Viterbi step a max-plus circular convolution.

tau = s.Tdrift_s;  g = s.gamma;  sg = s.sigma;
Nf  = numel(gvec);  Np = s.n_phase;
dphi = 2*pi/Np;
df   = gvec(2) - gvec(1);

e1 = exp(-g*tau);  e2 = exp(-2*g*tau);
Vff = sg^2*(1 - e2)/(2*g);
Cfp = 2*pi*sg^2*(1 - e1)^2/(2*g^2);
Vpp = (2*pi)^2*sg^2*(2*g*tau - 3 + 4*e1 - e2)/(2*g^3);

ds = -s.max_bin_step:s.max_bin_step;
nd = numel(ds);
tr.ds = ds(:);
tr.logPf   = -inf(Nf, nd);
tr.logPphi = -inf(Nf, nd, Np);
tr.Vff = Vff; tr.Cfp = Cfp; tr.Vpp = Vpp;

% conditional phase law given f':   N( mu_p + (Cfp/Vff)(f' - mu_f),  Vpp - Cfp^2/Vff )
Vcond = max(Vpp - Cfp^2/Vff, eps);
kvec  = (0:Np-1)'*dphi;                       % candidate wrapped phase increments
wraps = (-s.n_wrap:s.n_wrap)*2*pi;

for i = 1:Nf
    f   = gvec(i);
    muf = f*e1;
    mup = 2*pi*f*(1 - e1)/g;                  % mean phase advance over the step
    for a = 1:nd
        ip = i + ds(a);
        if ip < 1 || ip > Nf, continue; end
        fp = gvec(ip);
        % frequency part: bin probability approximated by density x bin width
        tr.logPf(i,a) = -0.5*log(2*pi*Vff) - (fp - muf)^2/(2*Vff) + log(df);
        % phase part: wrapped Gaussian on the phase-bin difference
        mc = mup + (Cfp/Vff)*(fp - muf);
        % FIX-A (2026-09-17): reduce the phase residual to the principal
        % branch BEFORE truncating the wrap sum.  With tau = Tdrift and
        % |f| <= 2 Hz the mean advance mc reaches +-16 turns, so keeping
        % m = -n_wrap..n_wrap around ZERO discarded the dominant mass and
        % row normalisation could only rescale the wrong shape.
        d  = mod(kvec - mc + pi, 2*pi) - pi;   % Np x 1, principal branch
        dd = d + wraps;                        % Np x (2*n_wrap+1)
        lp = -0.5*log(2*pi*Vcond) - (dd.^2)/(2*Vcond) + log(dphi);
        tr.logPphi(i,a,:) = logsumexp_rows(lp);
    end
end

% normalise each source state so the outgoing kernel is a proper distribution
for i = 1:Nf
    tot = -inf;
    for a = 1:nd
        if ~isfinite(tr.logPf(i,a)), continue; end
        tot = logaddexp(tot, tr.logPf(i,a) + logsumexp_rows(squeeze(tr.logPphi(i,a,:))'));
    end
    if isfinite(tot)
        tr.logPf(i,:) = tr.logPf(i,:) - tot;
    end
end
end

function y = logsumexp_rows(x)
m = max(x, [], 2);
y = m + log(sum(exp(x - m), 2));
y(~isfinite(m)) = -inf;
end

function c = logaddexp(a, b)
if ~isfinite(a), c = b; return; end
if ~isfinite(b), c = a; return; end
m = max(a,b);
c = m + log(exp(a-m) + exp(b-m));
end
