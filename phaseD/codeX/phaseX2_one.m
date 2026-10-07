function S=phaseX2_one(scene,snr,rid)
[F,cfg,B,M]=phaseX_settings(300,false);
seed=cfg.master_seed+54e6+1e4*cfg.scene_code.(scene)+rid;
rec=simulate_baseband_T(cfg,scene,snr,seed,'eval',300);
[fe,v,idx,times]=phaseX_front(rec.y,rec.t,B,M);
timer=tic;fv=build_family_T(rec.t,fe.tc,v.g,M.B2,10,300,1);times.family=toc(timer);
timer=tic;smr=estimate_b2(fe,fv,M.B2);times.smr=toc(timer);
timer=tic;mft=estimate_b0(fe,M.B0);times.mft=toc(timer);
timer=tic;suv=estimate_suvorova_D(rec.y,rec.t,fe.noise_hat,suvorova_config(),idx);times.suv=toc(timer);
names={'VS','MFT','SUV','V0'};ins={smr.g,mft.g,suv.g,v.g};
anchors={v.g,mft.g,suv.g,v.g};starts={smr.u,zeros(fv.P,1),zeros(fv.P,1),zeros(fv.P,1)};
checks={fe.tc,fe.tc,.5*(suv.t_block(1:end-1)+suv.t_block(2:end)),fe.tc};
rows=cell(1,4);details=cell(1,4);
for k=1:4
    % Compute and record input-only usability before evaluating any output.
    e=ins{k}(idx)-rec.truth.gtrue(idx);usable_fraction=mean(abs(e-mean(e))<=.1);
    mi=phaseD_measure(rec,ins{k},idx,B);
    if k==1||k==4,fam=fv;else,fam=build_family_T(rec.t,checks{k},anchors{k},M.B2,10,300,1);end
    a=phaseD_ada(rec.y,fe,fam,starts{k},idx,M.P,rec.t,30,.04,'local','A');
    mo=phaseD_measure(rec,a.out.g,idx,B);
    r=struct('scene',string(scene),'snr_db',snr,'record_id',rid,'seed',seed,'input_hash',string(phaseD_hash(rec.y,'MD5')),'frontend',string(names{k}),'duration_s',300,'phase_id',54,'Delta_s',10,'P',fam.P,'method',string(F.method),...
       'eta_in',mi.eta,'eta_out',mo.eta,'gain_eta',mo.eta-mi.eta,'peak_in_db',mi.peak_db,'peak_out_db',mo.peak_db,'gain_peak_db',mo.peak_db-mi.peak_db,'usable_fraction',usable_fraction,'input_usable',usable_fraction>=.9,'gain_positive',mo.eta>mi.eta,'runtime_s',a.seconds,'t_round0_s',a.logs{1}.seconds,'t_expansion_s',a.seconds-a.logs{1}.seconds,'triggered',a.triggered,'expansion_rounds',a.rounds,'initial_dwell_s',a.initial_dwell_s,'J',a.out.J_best,'J_start',a.out.J_B2,'J_round0',a.logs{1}.J,'hard_fail',a.out.hard_fail,'fallback',a.out.fallback,'budget_cap',any(a.out.iters(:)>=a.out.max_iter(:)|a.out.fevals(:)>=a.out.max_fevals(:)),'final_bounds',string(jsonencode(a.m)),'exitflags',string(jsonencode(a.out.exitflags)),'iterations',string(jsonencode(a.out.iters)),'fevals',string(jsonencode(a.out.fevals)),'t_frontend_s',times.frontend,'t_vit_s',times.vit,'t_smr_s',times.smr,'t_mft_s',times.mft,'t_suv_s',times.suv);
    rows{k}=r;details{k}=struct('frontend',names{k},'input_g',ins{k},'family',fam,'ada',a,'input_usable_fraction',usable_fraction);
end
S=struct('rows',[rows{:}],'details',{details},'record_id',rid,'scene',scene,'snr_db',snr,'input_hash',phaseD_hash(rec.y,'MD5'),'times',times);
end
