function S=phaseX1_one(scene,snr,rid,T)
[F,cfg,B,M]=phaseX_settings(T,false);
seed=cfg.master_seed+53e6+1e4*cfg.scene_code.(scene)+rid;
rec=simulate_baseband_T(cfg,scene,snr,seed,'eval',T);
[fe,v,idx,times]=phaseX_front(rec.y,rec.t,B,M);
timer=tic;fam=build_family_T(rec.t,fe.tc,v.g,M.B2,F.Delta_s,T,1);times.family=toc(timer);
timer=tic;smr=estimate_b2(fe,fam,M.B2);times.smr=toc(timer);
mS=phaseD_measure(rec,smr.g,idx,B);mV=phaseD_measure(rec,v.g,idx,B);
timer=tic;o2=estimate_proposed_T(rec.y,fe,fam,smr.u,idx,M.P);secs2=toc(timer);
base=struct('out',o2,'seconds',secs2);
a=phaseD_ada(rec.y,fe,fam,smr.u,idx,M.P,rec.t,30,.04,'local','A',base);
fu=fam;fu.lb=-Inf(fam.P,1);fu.ub=Inf(fam.P,1);
timer=tic;ou=estimate_proposed_T(rec.y,fe,fu,smr.u,idx,M.P);secsu=toc(timer);
so=struct('g',smr.g,'u',smr.u,'J_best',o2.J_B2,'J_B2',o2.J_B2,'fallback',smr.fit_failed,'hard_fail',smr.fit_failed,'iters',[],'fevals',[],'max_iter',[],'max_fevals',[],'exitflags',smr.exitflag,'stage_seconds',[],'stage_J290',[],'selected','SMR_quadratic_fit');
dw=phaseD_dwell(o2.u,ones(fam.P,1),fam,rec.t,idx,B.fs);
sa=struct('rounds',0,'triggered',false,'initial_dwell_s',dw,'m',ones(fam.P,1));
ua=sa;ua.initial_dwell_s=NaN;ua.m=Inf(fam.P,1);
rows=[phaseD_row(rec,rid,10,'scaled','SMR',so,fam,mS,mV,times.smr,times,sa,B,idx),...
 phaseD_row(rec,rid,10,'scaled','F02',o2,fam,mS,mV,secs2,times,sa,B,idx),...
 phaseD_row(rec,rid,10,'scaled','UNB',ou,fam,mS,mV,secsu,times,ua,B,idx),...
 phaseD_row(rec,rid,10,'scaled',F.method,a.out,fam,mS,mV,a.seconds,times,a,B,idx)];
for k=1:4,rows(k).duration_s=T;rows(k).phase_id=53;rows(k).t_round0_s=secs2;rows(k).t_expansion_s=a.seconds-secs2;end
S=struct('rows',rows,'record_id',rid,'scene',scene,'snr_db',snr,'duration_s',T,'family',fam,'smr',smr,'F02',o2,'UNB',ou,'ada',a,'times',times,'input_hash',phaseD_hash(rec.y,'MD5'));
end
