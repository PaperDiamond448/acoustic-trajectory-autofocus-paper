function S=phaseC_one(scene,snr,rid,F)
[~,B,M]=phaseD_setup();[rec,fe,v,idx,times]=phaseC_record52(scene,snr,rid);
Delta=F.Delta_s;[lc,lf,P]=phaseD_regularization(Delta,300,true);
assert(lc==F.regularization.lambda_C && lf==F.regularization.lambda_F && P==F.P);
MC=M.B2;MC.lambda_F=lf;PC=M.P;PC.lambda_C=lc;
PC.max_iter=repmat(F.budget_formula.selected_iterations,1,3);PC.max_fevals=repmat(F.budget_formula.selected_fevals,1,3);
timer=tic;fam=build_family_T(rec.t,fe.tc,v.g,MC,Delta,300,1);times.family=toc(timer);
timer=tic;smr=estimate_b2(fe,fam,MC);times.smr=toc(timer);
mS=phaseD_measure(rec,smr.g,idx,B);mV=phaseD_measure(rec,v.g,idx,B);
rows=cell(1,5);details=cell(1,5);names={'F02','F04','UNB'};bounds=[1 2 Inf];
for k=1:3
    f=fam;f.lb=-bounds(k)*ones(P,1);f.ub=bounds(k)*ones(P,1);
    timer=tic;o=estimate_proposed_T(rec.y,fe,f,smr.u,idx,PC);secs=toc(timer);
    if k==1,base=struct('out',o,'seconds',secs);end
    if isfinite(bounds(k)),dw=phaseD_dwell(o.u,f.ub,fam,rec.t,idx,B.fs);else,dw=NaN;end
    a=struct('rounds',0,'triggered',false,'initial_dwell_s',dw,'m',f.ub);
    rows{k+1}=phaseD_row(rec,rid,Delta,'scaled',names{k},o,fam,mS,mV,secs,times,a,B,idx);
    details{k+1}=struct('method',names{k},'out',o,'seconds',secs);
end
a=phaseD_ada(rec.y,fe,fam,smr.u,idx,PC,rec.t,F.ADA.tau_s,F.ADA.cap_hz,F.ADA.mode,F.ADA.rerun,base);
rows{5}=phaseD_row(rec,rid,Delta,'scaled',F.method,a.out,fam,mS,mV,a.seconds,times,a,B,idx);
details{5}=struct('method',F.method,'ada',a);
% SMR has a quadratic-fit exit flag, but no BTA stages or BTA budget.
so=struct('g',smr.g,'u',smr.u,'J_best',base.out.J_B2,'J_B2',base.out.J_B2,...
    'fallback',smr.fit_failed,'hard_fail',smr.fit_failed,'iters',[],...
    'fevals',[],'max_iter',[],'max_fevals',[],'exitflags',smr.exitflag,...
    'stage_seconds',[],'stage_J290',[],'selected','SMR_quadratic_fit');
sd=phaseD_dwell(smr.u,ones(P,1),fam,rec.t,idx,B.fs);
sa=struct('rounds',0,'triggered',false,'initial_dwell_s',sd,'m',ones(P,1));
rows{1}=phaseD_row(rec,rid,Delta,'scaled','SMR',so,fam,mS,mV,times.smr,times,sa,B,idx);
details{1}=struct('method','SMR','smr',smr,'seconds',times.smr);
S=struct('rows',[rows{:}],'details',{details},'record_id',rid,'scene',scene,...
    'snr_db',snr,'input_hash',phaseD_hash(rec.y,'MD5'),'family',fam,'times',times);
end
