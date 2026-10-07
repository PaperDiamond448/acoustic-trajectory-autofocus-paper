function out = estimate_suvorova_D(y, t, noise_hat, s, evalIdx)
%ESTIMATE_SUVOROVA  Phase-continuous frequency-line track-before-detect.
%   Faithful single-channel implementation of Suvorova et al. (2018).
%   Receives ONLY the observation, its time axis, the shared noise-scale
%   estimate and the frozen neighbour configuration -- no ground truth.
%
%   Chain:  non-overlapping blocks -> complex matched filter per frequency bin
%           -> phase-sensitive amplitude-marginalised emission (Eqs. 22-24)
%           -> phase-wrapped OU transition (Eqs. 3-13) -> Viterbi
%           -> phase-refined frequency read-out -> path-score detection statistic

fs = 1/median(diff(t));
n0 = evalIdx(1);  Ne = numel(evalIdx);
Lb = round(s.Tdrift_s*fs);
NB = floor(Ne/Lb);                                  % whole blocks only
assert(NB >= 4, 'need at least 4 drift blocks');

dfr  = 1/(2*s.Tdrift_s);                            % SRC Sec. II-A Nyquist rule
gvec = (s.band_hz(1):dfr:s.band_hz(2))';
Nf   = numel(gvec);  Np = s.n_phase;
dphi = 2*pi/Np;
phig = (0:Np-1)'*dphi;

% ---------- emission ----------
% X = Re{ S_k(g_i) e^{-j phi_j} } normalised to unit variance under H0.
% For complex noise with E|w|^2 = sigma^2 over Lb samples, E|S|^2 = sigma^2 Lb
% and Var( Re{S e^{-j phi}} ) = sigma^2 Lb / 2.
nrm = sqrt(max(noise_hat*Lb/2, realmin));
nb  = (0:Lb-1)'/fs;
center_local_s = mean(nb);                          % block centre in local time
E   = zeros(Nf, Np, NB);
tb  = zeros(NB,1);
for k = 1:NB
    idx = n0 + (k-1)*Lb + (0:Lb-1);
    yb  = y(idx);
    tb(k) = mean(t(idx));
    S = czt_match(yb, fs, gvec(1), dfr, Nf);        % Nf x 1 complex
    % FIX-B (2026-09-17): czt_match measures local time from the FIRST
    % sample, so arg S(g) = phi(t_centre) - 2 pi g u_centre.  The hidden
    % state phase, the OU transition and the read-out all refer to the
    % block CENTRE tb(k), so the matched coefficients are rotated to that
    % same origin before the emission is formed.  Without it the phase
    % state carried a bin-dependent offset -2 pi g u_centre.
    S = S .* exp(1j*2*pi*gvec*center_local_s);
    % X(i,j) = Re{ S_i e^{-j phi_j} } / nrm
    X = real(S .* exp(-1j*phig.'))/nrm;             % Nf x Np
    E(:,:,k) = log_emission(X);
end

% ---------- transition ----------
tr = suvorova_transition(gvec, s);
ds = tr.ds;  nd = numel(ds);
IDX = mod((0:Np-1) - (0:Np-1)', Np) + 1;            % IDX(j, jp) = (jp - j) mod Np + 1

% ---------- Viterbi ----------
V = E(:,:,1) - log(Nf*Np);                          % uniform prior
ptrF = zeros(Nf, Np, NB, 'int16');
ptrP = zeros(Nf, Np, NB, 'int16');
for k = 2:NB
    best = -inf(Nf, Np);  bF = zeros(Nf, Np); bP = zeros(Nf, Np);
    for a = 1:nd
        d = ds(a);
        ipr = max(1, 1-d):min(Nf, Nf-d);            % source bins with valid target
        if isempty(ipr), continue; end
        for i = ipr
            ip = i + d;
            lf = tr.logPf(i,a);
            if ~isfinite(lf), continue; end
            kern = squeeze(tr.logPphi(i,a,:));      % Np x 1, indexed by (jp-j) mod Np
            % cand(jp) = max_j [ V(i,j) + kern((jp-j) mod Np + 1) ]
            M = V(i,:).' + kern(IDX);               % Np x Np : rows j, cols jp
            [mv, mj] = max(M, [], 1);
            mv = mv + lf;
            upd = mv > best(ip,:);
            if any(upd)
                best(ip,upd) = mv(upd);
                bF(ip,upd)   = i;
                bP(ip,upd)   = mj(upd);
            end
        end
    end
    V = E(:,:,k) + best;
    ptrF(:,:,k) = int16(bF);
    ptrP(:,:,k) = int16(bP);
end

[score, lin] = max(V(:));
[iE, jE] = ind2sub([Nf Np], lin);
pathF = zeros(NB,1); pathP = zeros(NB,1);
pathF(NB) = iE; pathP(NB) = jE;
for k = NB:-1:2
    pf = double(ptrF(pathF(k), pathP(k), k));
    pp = double(ptrP(pathF(k), pathP(k), k));
    if pf < 1 || pp < 1, pf = pathF(k); pp = pathP(k); end
    pathF(k-1) = pf; pathP(k-1) = pp;
end

% ---------- read-out ----------
g_bin = gvec(pathF);
ph    = phig(pathP);
if strcmpi(s.readout, 'phase_refined')
    % Phase continuity refines frequency far below the 0.1 Hz bin width:
    % over one step the true advance is 2 pi fbar tau = wrap(dphi_meas) + 2 pi m,
    % and m is resolved by the bin frequency (|bin error| < 1/(2 tau)).
    tau = s.Tdrift_s;
    dmeas = angle(exp(1j*diff(ph)));
    fbin_mid = 0.5*(g_bin(1:end-1) + g_bin(2:end));
    m = round(fbin_mid*tau - dmeas/(2*pi));
    fbar = (dmeas + 2*pi*m)/(2*pi*tau);
    fbar = min(max(fbar, s.band_hz(1)), s.band_hz(2));
    t_mid = 0.5*(tb(1:end-1) + tb(2:end));
    g_traj = interp_const(t_mid, fbar, t);
    out.g_phase_refined = g_traj;
else
    g_traj = interp_const(tb, g_bin, t);
end
out.g       = g_traj;
out.g_bin   = interp_const(tb, g_bin, t);
out.path_f  = g_bin;
out.path_phi= ph;
out.t_block = tb;
out.score   = score;                                 % ln P(Q*|O), the statistic
out.n_blocks= NB;
out.n_states= Nf*Np;
out.emission_along_path = sum(arrayfun(@(k) E(pathF(k), pathP(k), k), 1:NB));
end

function L = log_emission(X)
%LOG_EMISSION  ln L = X^2/2 + ln[1 + erf(X/sqrt(2))]   (Suvorova Eq. 24)
%
%   Evaluated by branch so that neither term overflows:
%     X >= 0 : 1 + erf lies in [1,2), so the direct form is already stable.
%     X <  0 : 1 + erf(X/sqrt2) = erfc(|X|/sqrt2) = erfcx(|X|/sqrt2) e^{-X^2/2},
%              so ln L = log(erfcx(|X|/sqrt2)) and the X^2/2 terms cancel.
%   The single-branch form log(erfcx(-X/sqrt2)) is algebraically identical but
%   overflows for X greater than about 27, which is reached at 10 dB SNR.
L = zeros(size(X));
p = X >= 0;
L(p)  = X(p).^2/2 + log1p(erf(X(p)/sqrt(2)));
L(~p) = log(erfcx(-X(~p)/sqrt(2)));
end
