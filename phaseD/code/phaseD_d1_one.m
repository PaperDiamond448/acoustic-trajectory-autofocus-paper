function S=phaseD_d1_one(scene,snr,rid)
[cfg,B,M]=phaseD_setup();[rec,fe,v,idx,times]=phaseD_record(scene,snr,rid);
mV=phaseD_measure(rec,v.g,idx,B); rows={};details={};
for Delta=[60 30 20 15 10 7.5 6]
    arms={'scaled'};if Delta~=15,arms{end+1}='unscaled';end
    for ai=1:numel(arms)
        scaled=strcmp(arms{ai},'scaled');[lc,lf,P]=phaseD_regularization(Delta,300,scaled);
        MC=M.B2;MC.lambda_F=lf;PC=M.P;PC.lambda_C=lc;
        PC.max_iter=repmat(round(240*max(1,P/21)),1,3);PC.max_fevals=repmat(round(1000*max(1,P/21)),1,3);
        timer=tic;fam=build_family_T(rec.t,fe.tc,v.g,MC,Delta,300,1);times.family=toc(timer);
        timer=tic;smr=estimate_b2(fe,fam,MC);times.smr=toc(timer);mS=phaseD_measure(rec,smr.g,idx,B);
        modes={'F02'};if scaled,modes{end+1}='UNB';end
        for mi=1:numel(modes)
            f=fam;if strcmp(modes{mi},'UNB'),f.lb=-Inf(P,1);f.ub=Inf(P,1);end
            timer=tic;o=estimate_proposed_T(rec.y,fe,f,smr.u,idx,PC);secs=toc(timer);
            [dwell,~]=phaseD_dwell(o.u,ones(P,1),fam,rec.t,idx,B.fs);
            a=struct('rounds',0,'triggered',false,'initial_dwell_s',dwell,'m',f.ub);
            rows{end+1}=phaseD_row(rec,rid,Delta,arms{ai},modes{mi},o,fam,mS,mV,secs,times,a,B,idx);
            details{end+1}=struct('Delta',Delta,'arm',arms{ai},'method',modes{mi},'smr',smr,'out',o,'seconds',secs,'bounds',f.ub,'lambda_C',lc,'lambda_F',lf);
        end
    end
end
S=struct('rows',[rows{:}],'details',{details},'record_id',rid,'scene',scene,'snr_db',snr,'input_hash',phaseD_hash(rec.y,'MD5'));
end
