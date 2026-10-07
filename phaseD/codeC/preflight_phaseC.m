function preflight_phaseC()
phaseD_setup();addpath('D:\论文集\phaseD\codeC','-begin');[cfg,B,M]=phaseD_setup();
% Validate the new interface against the independently constructed phase-52 path.
for scene={'S0','S2'}
    [r,f,v,idx,~]=phaseC_record52(scene{1},-17,1);
    seed=cfg.master_seed+52e6+1e4*cfg.scene_code.(scene{1})+1;
    q=simulate_baseband_T(cfg,scene{1},-17,seed,'eval',300);
    fc=struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine,'band',B.band,'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
    fq=common_frontend(q.y,q.t,fc);vq=estimate_b1(fq,M.B1);
    assert(isequal(r,q) && isequal(f,fq) && isequal(v,vq) && isequal(idx,find(q.t>=5&q.t<295)));
    assert(seed==20260915+52e6+(1+2*strcmp(scene{1},'S2'))*1e4+1);
end
names={'phaseC_record52','phaseC_one','run_phaseC_confirm'};
for k=1:numel(names),a=checkcode(which(names{k}),'-id');fprintf('%s: %d static diagnostics\n',names{k},numel(a));for j=1:numel(a),fprintf('%s\n',a(j).message);end,end
phaseD_json('D:\论文集\phaseD\C_confirm\PREFLIGHT.json',struct('status','PASS','phase_id',52,'scope','Interface equivalence and frozen settings; no confirmation optimizer results inspected','matlab_release',version('-release')));
end
