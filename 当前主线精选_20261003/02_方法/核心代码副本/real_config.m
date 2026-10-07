function R = real_config()
%REAL_CONFIG  Frozen configuration of the MEASURED-BACKGROUND INJECTION case.
%
%   What this experiment is:  a known, synthetically generated moving line
%   spectrum (and, for the S2 analogue, a synthetic adjacent-frequency
%   interferer) is added to REAL recorded background taken from SWellEx-96
%   Event S5, HLA North.  The background keeps its own propagation and
%   non-stationary structure; the injected target does NOT automatically
%   acquire real multipath, so nothing here demonstrates coherence loss of a
%   real propagating target.
%
%   What it is NOT:  it is not a blind test, not four independent sea trials,
%   and not a false-alarm benchmark.  The four 300 s background windows come
%   from ONE event, inside intervals that have already been inspected in
%   earlier rounds of this project, and neighbouring windows are not
%   automatically independent.  No Pd at a fixed alpha is claimed.
%
%   Everything below is fixed BEFORE any estimator is run.  No algorithm
%   parameter is re-tuned for the measured background.

R.label     = 'REAL-INJECT-S5-HLAN-20260917';
R.event     = 'SWellEx-96 Event S5, HLA North (element list below), J1312340';
R.file      = 'D:\论文集\J1312340.hla.north.sio\J1312340.hla.north.sio';
R.file_sha256 = '0f663c14efab00b16500e82d56936cf95b4931c1ea1a2a4bcb815d93b56b66d3';
R.file_bytes  = 530849792;

% ---- raw record, from the SIO header (verified, not assumed) ----
R.fs_raw    = 3276.8;      % Hz
R.n_chan    = 27;
R.n_raw     = 9830400;     % samples per channel = 3000.000 s
R.sample_fmt= 'int16 big-endian, SIO record length 8192 bytes = 4096 points';

% ---- band and baseband conversion (identical to the simulation) ----
% The centre frequency and the +-2 Hz candidate band are NOT chosen by looking
% at algorithm gain.  They are the frozen simulation values, and they are
% admissible here because the official SWellEx-96 S5 projector tone lists
%   deep  (54 m): 49 64 79 94 112 130 148 166 201 235 283 338 388 Hz
%   shallow (9 m): 109 127 145 163 198 232 280 335 385 Hz
% place NO transmitted project tone inside 98-102 Hz; the nearest are 94 and
% 109 Hz.  Whatever else is present there (ship tonals, ambient) is background.
R.fref      = 100;         % Hz, centre of the retained band
R.fs        = 20;          % Hz, complex baseband rate (as in the simulation)
R.band      = [-2 2];      % Hz, candidate band (as in the simulation)
R.keep_hz   = 10;          % Hz, half-width actually retained (= fs/2)
R.guard_s   = 10;          % s of guard discarded at each end of a window
R.method    = ['exact band selection in the DFT of a (300 + 2*guard) s segment, ' ...
               'inverse transform at 20 Hz, guard removed; no filter design, ' ...
               'no rational resampler, block edges not wrapped into the data'];

% ---- background windows ----
% Four non-overlapping 300 s windows inside the two intervals this project has
% already inspected (900-1540 s and 1800-2440 s).  Declared as background cases
% from one event, not as independent trials.
R.win_start_s = [900 1200 1800 2100];
R.win_len_s   = 300;
R.win_note    = ['non-overlapping within one event; 900-1200 and 1200-1500 are ' ...
                 'adjacent, and adjacency does not imply independence'];

% ---- channel selection rule, declared before any estimator is run ----
% (1) drop a channel with any |sample| >= 32000 in any window (clipping);
% (2) drop a channel whose median in-band (98-102 Hz) power over the four
%     windows differs from the across-channel median by more than 6 dB;
% (3) among the survivors take the channel whose median in-band power is
%     CLOSEST to the across-channel median, i.e. the most typical element.
% The rule uses only the recorded background; it never sees a trajectory
% estimate or a detection score.
R.chan_rule = struct('clip_abs', 32000, 'max_dev_db', 6, ...
                     'pick', 'closest_to_median_in_band_power');
R.chan_fixed = 9;          % frozen by run_bg_check: all 27 elements healthy, channel 9 is the exact median

% ---- injection ----
% The target and the interferer come from the UNCHANGED phase generator
% simulate_baseband: phi_g(t) = 2 pi f0 tau(t) - 2 pi fref t + phi0 with the
% frozen evaluation geometry.  Only the additive noise term is replaced.
%
% SNR convention.  Each background window is scaled so that its mean complex
% baseband sample power over the retained +-10 Hz equals 1, exactly the
% simulator's E|w|^2 = 1.  The injected amplitude is then A = 10^(SNR/20) as in
% the simulation.  This equalises TOTAL in-band power only: the measured
% background is coloured and non-stationary, so the same nominal SNR is not the
% same detection difficulty as in the white-noise simulation, and the numbers
% are not interchangeable with the simulated Pd tables.
R.scene      = 'S2';       % target + synthetic adjacent-frequency interferer
R.scene_name = 'real background + synthetic target and interferer';
R.snr_db     = [-20 -18 -16];
R.n_inject   = 20;         % independent geometries / initial phases per cell
R.phase_id   = 31;         % disjoint from every simulation phase id (21-28)
R.methods    = {'B0','B1','B2','P60'};
R.primary    = 'paired eta increment P60 - B2, per background window and pooled';
R.boot_reps  = 2000;

R.n_h1 = numel(R.win_start_s)*numel(R.snr_db)*R.n_inject;
R.not_claimed = {'no Pd at a fixed false-alarm rate', ...
                 'no independent H0 background', ...
                 'no real-target multipath decoherence', ...
                 'no blind test'};
end
