function S=phaseD_d2_one(scene,snr,rid,Delta,stage,rerun)
[cfg,B,M]=phaseD_setup();[rec,fe,v,idx,times]=phaseD_record(scene,snr,rid);
[lc,lf,P]=phaseD_regularization(Delta,300,true);MC=M.B2;MC.lambda_F=lf;PC=M.P;PC.lambda_C=lc;
PC.max_iter=repmat(round(240*max(1,P/21)),1,3);PC.max_fevals=repmat(round(1000*max(1,P/21)),1,3);
timer=tic;fam=build_family_T(rec.t,fe.tc,v.g,MC,Delta,300,1);times.family=toc(timer);
timer=tic;smr=estimate_b2(fe,fam,MC);times.smr=toc(timer);
mS=phaseD_measure(rec,smr.g,idx,B);mV=phaseD_measure(rec,v.g,idx,B);
rows={};details={};
% Reuse the exact D1 F02/UNB solves at the selected Delta; no re-optimisation.
folder=fullfile('D:\论文集','phaseD','D_dev','D1_chunks');tag=sprintf('%s_%+03ddB_chunk_%03d.mat',scene,snr,ceil(rid/10));
C=load(fullfile(folder,tag),'results');r=find([C.results.record_id]==rid);d=C.results(r).details;
assert(strcmp(C.results(r).input_hash,phaseD_hash(rec.y,'MD5')),'D1/D2 input differs.');
for k=1:numel(d)
    if d{k}.Delta==Delta && strcmp(d{k}.arm,'scaled')
        if strcmp(d{k}.method,'F02'),assert(isequal(smr.u,d{k}.smr.u),'SMR start differs.');base=struct('out',d{k}.out,'seconds',d{k}.seconds);end
        if strcmp(d{k}.method,'UNB'),unb=d{k};end
    end
end
if strcmp(stage,'fixed')
    for k=1:5
        names={'F01','F02','F04','F08','UNB'};bounds=[0.5 1 2 4 Inf];f=fam;f.lb=-bounds(k)*ones(P,1);f.ub=bounds(k)*ones(P,1);
        if k==2,o=base.out;secs=base.seconds;
        elseif k==5,o=unb.out;secs=unb.seconds;
        else,timer=tic;o=estimate_proposed_T(rec.y,fe,f,smr.u,idx,PC);secs=toc(timer);end
        if isfinite(bounds(k)),[dw,~]=phaseD_dwell(o.u,f.ub,fam,rec.t,idx,B.fs);
        else,dw=NaN;end
        a=struct('rounds',0,'triggered',false,'initial_dwell_s',dw,'m',f.ub);
        rows{end+1}=phaseD_row(rec,rid,Delta,'scaled',names{k},o,fam,mS,mV,secs,times,a,B,idx);
        details{end+1}=struct('method',names{k},'out',o,'seconds',secs);
    end
elseif strcmp(stage,'rerunA') || strcmp(stage,'rerunB')
    re=stage(end);a=phaseD_ada(rec.y,fe,fam,smr.u,idx,PC,rec.t,20,0.08,'global',re,base);
    name=['ADA_AB_' re];rows{1}=phaseD_row(rec,rid,Delta,'scaled',name,a.out,fam,mS,mV,a.seconds,times,a,B,idx);
    details{1}=struct('method',name,'ada',a);
elseif strcmp(stage,'grid')
    globalChain=phaseD_ada(rec.y,fe,fam,smr.u,idx,PC,rec.t,10,0.08,'global',rerun,base);
    for mode={'global','local'}
        for tau=[10 15 20 30 45]
            if strcmp(mode{1},'global'),chain=globalChain;
            else,chain=phaseD_ada(rec.y,fe,fam,smr.u,idx,PC,rec.t,tau,0.08,'local',rerun,base);end
            for cap=[0.04 0.08]
                name=sprintf('ADA_%s_c%02d_t%02d_%s',mode{1},round(cap*100),tau,rerun);
                a=phaseD_ada_prefix(chain,tau,cap);
                rows{end+1}=phaseD_row(rec,rid,Delta,'scaled',name,a.out,fam,mS,mV,a.seconds,times,a,B,idx);
                details{end+1}=struct('method',name,'ada',a);
            end
        end
    end
else,error('Unknown development stage.');end
S=struct('rows',[rows{:}],'details',{details},'record_id',rid,'scene',scene,'snr_db',snr,'input_hash',phaseD_hash(rec.y,'MD5'));
end
