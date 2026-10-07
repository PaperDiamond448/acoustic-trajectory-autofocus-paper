function cfg = mft_config()
%MFT_CONFIG  Protocol MFT-W2-v2-20260915-LITE.
%   Receiver definitions (cfg.B, cfg.M) are INHERITED UNCHANGED from
%   mft_week1 (verified source hash 6a0d1168bafc8a9ce0e4968285e3f1a2).
%   Only scheduling, seeds, the two alpha levels and the grid are new.

cfg.protocol_id  = 'MFT-W2-v2-20260915-LITE';
cfg.supersedes   = 'MFT-W2-v1-20260915';
cfg.inherits_from= 'mft_week1 / 6a0d1168bafc8a9ce0e4968285e3f1a2';
cfg.master_seed  = 20260915;

% ================= INHERITED UNCHANGED: complex-baseband receiver =========
B.fs            = 20;
B.T             = 300;
B.N             = 6000;
B.fref          = 100;
B.band          = [-2 2];
B.eval_s        = [5 295];
B.L             = 200;       % 10 s
B.D             = 20;        % 1 s
B.df_fine       = 0.001;
B.coarse_dec    = 5;         % -> 0.005 Hz
B.noise_bands   = [-8 -4; 4 8];
B.fft_pad       = 8;
B.c             = 1500;
B.dc            = 1000;
B.dev_geo       = struct('f0',100,'v',5,'t_cpa_rx',150);
B.eval_geo      = struct('f0',[99.95 100.05],'v',[4 6],'t_cpa_rx',[120 180]);
B.fade          = struct('center_s',150,'plateau_duration_s',16,'edge_duration_s',2,'floor',0.1);
B.intf          = struct('center_s',150,'plateau_duration_s',16,'edge_duration_s',2, ...
                         'df_hz',0.18,'amp',1);
B.track_tol     = 0.05;
B.track_min_cov = 0.80;
B.active_amp    = 0.50;
B.alpha         = [0.05 0.01];          % handled as TWO separate analysis levels
cfg.B = B;

% ================= INHERITED UNCHANGED: methods ===========================
M.B0 = struct('df',0.001,'median_len',5);
M.B1 = struct('df',0.005,'sigma_step',0.01,'max_step',0.02,'median_len',5);
M.B2 = struct('tol_x',1e-5,'radius',0.02,'knot_ds',15,'lambda_F',0.1, ...
              'u_bounds',[-1 1],'band',[-2 2]);
M.P  = struct('h_stages_s',[20 60 290],'lambda_C',1e-3,'max_iter',[60 60 60], ...
              'max_fevals',[250 250 250],'tol_x',1e-6,'tol_opt',1e-6,'label','P60');
cfg.M = M;

% ================= NEW: scheduling, seeds, grid ===========================
cfg.phase_id = struct('budget',21,'h0_calibration',22,'h0_validation',23, ...
                      'h1_test',24,'bootstrap',25);
cfg.scene_code = struct('S0',1,'S1',2,'S2',3,'H0_0',11,'H0_I',12);

% ---- TWO DECLARED DEVIATIONS from MFT-W2-v2-20260915-LITE, user-approved ----
% (D1) H0 restored to the v1 size, 5000 calibration + 5000 validation per null.
%      Reason: the prespecified primary endpoint is S2 at alpha = 0.01, and week 1
%      found P's H0-I upper tail heavier than B1's (p99 20.09 vs 17.17 dB).  The
%      1% threshold sits in that low-density region, so a 1000-record calibration
%      would give a threshold-inclusive interval about 2.2x wider.  Cost ~1.9 h
%      of unattended wall clock.  Nothing else about the null changes.
% (D2) One extra budget-diagnostic variant D180: a SINGLE 290 s stage with the
%      same total budget as P60 (180 iterations, 750 function evaluations), so
%      the staged 20->60->290 schedule can be compared with direct optimisation
%      at equal budget instead of being left as an untested implementation
%      choice.  Cost ~1 min.  D180 never replaces P60 anywhere.
cfg.deviations = {'H0_5000_per_null_instead_of_1000', 'extra_budget_variant_D180_direct_290s'};

cfg.main = struct( ...
    'methods',        {{'B0','B1','B2','P60'}}, ...
    'scenes',         {{'S0','S1','S2'}}, ...
    'snr_db',         [-20 -19 -18 -17 -16 -15], ...
    'h1_per_cell',    200, ...
    'nulls',          {{'H0_0','H0_I'}}, ...
    'h0_cal_per_null',5000, ...
    'h0_val_per_null',5000);

cfg.budget = struct( ...
    'snr_db',         [-20 -18 -15], ...
    'scenes',         {{'S0','S1','S2'}}, ...
    'h1_per_cell',    10, ...
    'h0_per_null',    10);
cfg.budget_variants = { ...
    struct('label','P60' ,'h_stages_s',[20 60 290],'max_iter',[ 60  60  60],'max_fevals',[250 250 250], ...
           'lambda_C',M.P.lambda_C,'tol_x',M.P.tol_x,'tol_opt',M.P.tol_opt), ...
    struct('label','P180','h_stages_s',[20 60 290],'max_iter',[180 180 180],'max_fevals',[750 750 750], ...
           'lambda_C',M.P.lambda_C,'tol_x',M.P.tol_x,'tol_opt',M.P.tol_opt), ...
    struct('label','D180','h_stages_s',290         ,'max_iter',180          ,'max_fevals',750, ...
           'lambda_C',M.P.lambda_C,'tol_x',M.P.tol_x,'tol_opt',M.P.tol_opt)};

cfg.boot_reps = 2000;
cfg.null_for  = struct('S0','H0_0','S1','H0_0','S2','H0_I');
cfg.primary   = struct('comparison','P60_minus_B2','scene','S2','alpha',0.01, ...
    'endpoint','equal_weight_mean_of_associated_detection_over_the_six_prespecified_SNRs');
end
