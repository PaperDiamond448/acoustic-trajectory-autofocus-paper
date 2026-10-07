function jobs = make_jobs(cfg, phase, scenes, snrs, ids)
%MAKE_JOBS  Build the job list for one week-2 phase.
%   scenes : cellstr of scene names ('S0','S1','S2','H0_0','H0_I')
%   snrs   : SNR levels (for null scenes any value works, A is forced to 0)
%   ids    : record_id vector
%   Within one scene, one record_id uses ONE seed for every SNR, so the levels
%   are paired on geometry, initial phase and noise.
n = numel(scenes)*numel(snrs)*numel(ids);
jobs = repmat(struct('phase','','scene','','scene_code',0,'snr_db',0, ...
                     'seed',0,'record_id',0), n, 1);
k = 0;
for si = 1:numel(scenes)
    sc   = scenes{si};
    code = cfg.scene_code.(sc);
    for ti = 1:numel(ids)
        sd = mft_seed(cfg, phase, code, ids(ti));
        for qi = 1:numel(snrs)
            k = k + 1;
            jobs(k) = struct('phase',phase,'scene',sc,'scene_code',code, ...
                'snr_db',snrs(qi),'seed',sd,'record_id',ids(ti));
        end
    end
end
jobs = jobs(1:k);
end
