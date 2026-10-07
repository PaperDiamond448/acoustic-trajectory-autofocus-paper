function s = suvorova_config()
%SUVOROVA_CONFIG  Fixed configuration of the phase-continuous frequency-line
%   track-before-detect neighbour (Suvorova et al., IEEE TSP 66(24), 2018).
%
%   Every field here is either taken from the paper (marked SRC) or is a
%   declared adaptation to the single-channel passive-sonar task (marked ADAPT).
%   See NEIGHBOUR_IMPLEMENTATION.md for the formula-by-formula mapping.
%
%   REVISION 2026-09-17 (directory mft_week3_neighbour_fix).  Three located
%   implementation/derivation defects of the first neighbour run are corrected:
%     FIX-A  suvorova_transition.m: the phase residual is reduced to the
%            principal branch before the Eq. (7) wrap sum is truncated.
%     FIX-B  estimate_suvorova.m: the matched coefficients are rotated to the
%            block CENTRE, the same instant the state phase and the read-out use.
%     FIX-C  this file: the admissible Tdrift range under Eq. (2) is recomputed
%            from the frozen motion parameters and the development sweep is
%            extended to its true upper end.
s.label       = 'SUV';
s.reference   = 'Suvorova, Melatos, Evans, Moran, Clearwater, Sun, IEEE TSP 66(24):6434-6442, 2018';
s.revision    = 'fix-ABC-20260917';

% ---- block / drift time scale ----
% SRC Sec. II-A: f(t) must stay in one frequency bin for a whole step,
%   \int_{t_{n-1}}^{t_{n-1}+Tdrift} |df/dt| dt < Delta f            (Eq. 2)
% ADAPT: with Delta f = 1/(2 Tdrift), Eq. (2) admits Tdrift < 1/sqrt(2 max|df/dt|).
%   FIX-C: the frozen evaluation geometry is v in [4,6] m/s, f0 in [99.95,100.05]
%   Hz, d_c = 1000 m, c = 1500 m/s.  For the straight-line constant-speed
%   RECEIVE-time model of geometry_tau.m the whole-record derivative bound is
%       max |df_r/dt| = f0 v^2 / (c d_c) * [1 - (v/c)^2]^(-3/2)
%                     = 2.40126e-3 Hz/s   at f0 = 100.05 Hz, v = 6 m/s,
%   which gives Tdrift < 14.43 s.  The 6.7e-3 Hz/s figure used in the first run
%   does not correspond to these parameters, so "8 s is already the upper end"
%   was not a valid reason.  The fixed development sweep therefore covers
%   {2.5, 5, 8, 12, 14} s; see results/dev/ for the selection.
s.drift_bound = struct('max_abs_dfdt_hz_per_s', 2.401257629952597e-3, ...
                       'T_admissible_s', 14.429976481017288, ...
                       'formula', 'f0*v^2/(c*dc)*(1-(v/c)^2)^(-3/2)');
s.Tdrift_s    = 8;                 % ADAPT, frozen from the fixed development sweep {2.5,5,8,12,14} s
s.df_rule     = '1/(2*Tdrift)';    % SRC Sec. II-A (Nyquist choice)
s.band_hz     = [-2 2];            % ADAPT, same candidate band as B0/B1/B2/P60

% ---- phase quantisation ----
% SRC Sec. II-A: "We take Delta phi = pi/16 typically as a good compromise
%   between accuracy and processing speed."
s.n_phase     = 32;                % SRC, Delta phi = 2*pi/32 = pi/16

% ---- phase-wrapped Ornstein-Uhlenbeck parameters ----
% SRC Eqs. (3)-(4):  df/dt = -gamma*f + sigma*xi(t),  dphi/dt = 2*pi*f
% ADAPT: gamma is a mean reversion towards f = 0.  A moving tone has no such
%   restoring force, so gamma is set small enough that the step is effectively
%   a random walk in frequency plus an integrated random walk in phase
%   (the gamma -> 0 limit of Eqs. 10-12, verified numerically in run_checks_w3).
%   gamma and sigma are NOT swept with Tdrift: they are held at the values frozen
%   before the first run, so the only development variable is Tdrift and the
%   read-out.  sigma*sqrt(Tdrift) is therefore 0.035 / 0.050 / 0.063 / 0.078 /
%   0.084 Hz at Tdrift = 2.5 / 5 / 8 / 12 / 14 s, and the +-max_bin_step band is
%   +-3/(2 Tdrift) Hz = +-0.600 / 0.300 / 0.188 / 0.125 / 0.107 Hz.  Both are
%   reported with the development result rather than retuned.
s.gamma       = 1e-3;              % ADAPT, 1/s
s.sigma       = 0.0224;            % ADAPT, Hz/sqrt(s)
s.n_wrap      = 2;                 % kept +-m terms of Eq. (7) AFTER the residual
                                   % is reduced to the principal branch (FIX-A)
s.max_bin_step= 3;                 % banded frequency transition, +-3 bins

% ---- emission ----
% SRC Eqs. (22)-(24) with constant beam patterns, amplitude marginalised over a
%   uniform prior on w in (0, inf):
%       ln L  ∝  X^2/2 + ln[1 + erf(X/sqrt(2))]
%   evaluated by branch so that neither term overflows.
%   FIX-B: X = Re{ S_k(g) e^{-j phi} } uses S_k referred to the BLOCK CENTRE.
s.emission    = 'amplitude_marginalised_F_statistic_scalar_case';
s.phase_origin= 'block_centre';    % FIX-B, shared by emission, transition, read-out

% ---- trajectory read-out ----
% ADAPT: the Viterbi bin sequence has resolution Delta f = 1/(2 Tdrift), coarser
%   than the 0.05 Hz association tolerance shared by all methods.  Using the
%   tracked PHASE to refine the frequency between steps is this task's read-out
%   adaptation of the paper's phase-continuous state; it is not a step the paper
%   prescribes verbatim.
s.readout     = 'phase_refined';   % ADAPT, frozen from the fixed development

% ---- detection statistic ----
% ADAPT (permitted by the task letter): the neighbour uses its own statistic,
%   the maximised Viterbi path score ln P(Q*|O), independently calibrated on the
%   same null types.  It is NOT compared against a P60/B2 threshold.
s.statistic   = 'viterbi_path_score';
end
