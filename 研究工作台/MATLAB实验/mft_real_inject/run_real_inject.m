function T = run_real_inject(outdir, nworkers)
%RUN_REAL_INJECT  Measured-background injection case.
%
%   y = s_target + interferer + w_real
%
%   s_target and the adjacent-frequency interferer come from the UNCHANGED
%   simulate_baseband phase generator with the frozen evaluation geometry; only
%   the additive term is replaced by a real 300 s complex baseband window of
%   SWellEx-96 S5 HLA North, scaled to unit mean in-band power.
%
%   Four background windows x three nominal injection SNRs x twenty independent
%   geometries / initial phases = 240 H1 records.  Within one window all sixty
%   records share the SAME background realisation: twenty injections are twenty
%   draws of the target, not twenty draws of ocean noise.  There is no H0 here
%   and no false-alarm rate is claimed.
if nargin < 1, outdir = fullfile(pwd,'results','inject'); end
if nargin < 2, nworkers = 8; end
if ~exist(outdir,'dir'), mkdir(outdir); end
R   = real_config();
cfg = mft_config(); B = cfg.B;
assert(R.chan_fixed >= 1, 'run run_bg_check first and freeze R.chan_fixed');
code = cfg.scene_code.(R.scene);

% ---- load and freeze the four background windows ----
nw = numel(R.win_start_s);
W  = cell(nw,1);  bginfo = cell(nw,1);
for w = 1:nw
    [z, info] = load_real_baseband(R, R.chan_fixed, R.win_start_s(w));
    assert(numel(z) == B.N, 'background window must be %d samples', B.N);
    scale = sqrt(mean(abs(z).^2));
    W{w}  = z/scale;
    info.scale = scale;
    info.pm2_over_pm10_db = 10*log10(info.band2_power/info.inband_power);
    bginfo{w} = info;
    fprintf('window %4d-%4d s : raw rms %.1f, +-2 Hz share %.2f dB of +-10 Hz\n', ...
        R.win_start_s(w), R.win_start_s(w)+R.win_len_s, info.raw_rms, info.pm2_over_pm10_db);
end

% ---- job list ----
jobs = struct('w',{},'t0_s',{},'snr_db',{},'inject_id',{},'record_id',{},'seed',{});
for w = 1:nw
    for q = R.snr_db
        for r = 1:R.n_inject
            rid = (w-1)*100 + r;              % geometry/phase paired across SNR
            jobs(end+1) = struct('w',w,'t0_s',R.win_start_s(w),'snr_db',q, ...
                'inject_id',r,'record_id',rid, ...
                'seed', cfg.master_seed + 1000000*R.phase_id + 10000*code + rid); %#ok<AGROW>
        end
    end
end
n = numel(jobs);
assert(n == R.n_h1, 'job count must match the plan');
fprintf('measured-background injection: %d H1 records on %d background windows\n', n, nw);

ensure_pool(nworkers);
rows = cell(n,1);
t0 = tic;
parfor i = 1:n
    j = jobs(i);
    ref = simulate_baseband(cfg, R.scene, j.snr_db, j.seed, 'eval');
    rec = ref;
    rec.y = ref.truth.s_target + ref.truth.intf + W{j.w};    % REAL background
    res = run_record(rec, cfg, R.methods);
    loc = cell(numel(res), 14);
    for k = 1:numel(res)
        m = res(k).metrics;
        loc(k,:) = {j.w, j.t0_s, j.snr_db, j.inject_id, j.record_id, j.seed, ...
            res(k).method, m.eta_max, m.rmse_eff, m.coverage_active, ...
            double(m.track_success), m.Z_db, m.nu_peak, res(k).t_chain};
    end
    rows{i} = loc;
end
el = toc(t0);
T = cell2table(vertcat(rows{:}), 'VariableNames', {'window','t0_s','snr_db', ...
    'inject_id','record_id','seed','method','eta_max','rmse_eff_hz', ...
    'coverage_active','track_success','Z_db','nu_peak','t_chain_s'});
T.method = string(T.method);
writetable(T, fullfile(outdir,'real_inject_raw.csv'));
fprintf('%d records x %d methods in %.1f s (%d workers)\n', n, numel(R.methods), el, nworkers);

meta = struct('config', R, 'seconds', el, 'workers', nworkers, ...
    'n_records', n, 'n_windows', nw, 'background', {bginfo}, ...
    'timestamp', datestr(now,'yyyy-mm-dd HH:MM:SS')); %#ok<TNOW1,DATST>
fid = fopen(fullfile(outdir,'real_inject_meta.json'),'w');
fprintf(fid,'%s', jsonencode(meta,'PrettyPrint',true)); fclose(fid);
end
