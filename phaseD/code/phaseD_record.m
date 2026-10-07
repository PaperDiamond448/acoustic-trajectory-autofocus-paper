function [rec,fe,v,idx,times]=phaseD_record(scene,snr,rid)
[cfg,B,M]=phaseD_setup();seed=cfg.master_seed+51e6+1e4*cfg.scene_code.(scene)+rid;
rec=simulate_baseband_T(cfg,scene,snr,seed,'eval',300);
fcfg=struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine,'band',B.band,'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
timer=tic;fe=common_frontend(rec.y,rec.t,fcfg);times.frontend=toc(timer);
timer=tic;v=estimate_b1(fe,M.B1);times.vit=toc(timer);idx=find(rec.t>=5&rec.t<295);
end
