function S=phaseX3_one(tone,start_s,T,fullcase)
[F,~,B,M]=phaseX_settings(T,true);root='D:\论文集\phaseD\X3_real';R=real_config();
if T==300
 file=fullfile(root,'screen_inputs',sprintf('f%d_s%d.mat',tone,start_s));q=load(file,'y','extract');y=q.y;extract=q.extract;
else
 [y,extract]=phaseA_load_baseband(R.file,9,tone,20,10,R.fs_raw,R.n_raw,start_s,T,10*(start_s>0),10*(start_s+T<3000));
end
t=(0:numel(y)-1)'/20;[fe,v,idx,times]=phaseX_front(y,t,B,M);
timer=tic;fv=build_family_T(t,fe.tc,v.g,M.B2,10,T,1);times.family=toc(timer);
timer=tic;smr=estimate_b2(fe,fv,M.B2);times.smr=toc(timer);
timer=tic;o2=estimate_proposed_T(y,fe,fv,smr.u,idx,M.P);secs2=toc(timer);
ada=phaseD_ada(y,fe,fv,smr.u,idx,M.P,t,30,.04,'local','A',struct('out',o2,'seconds',secs2));
names={'SMR','F02','VS_FM'};gs={smr.g,o2.g,ada.out.g};outs={[],o2,ada};fams={fv,fv,fv};secs=[times.smr secs2 ada.seconds];
if fullcase
 fu=fv;fu.lb=-Inf(fv.P,1);fu.ub=Inf(fv.P,1);timer=tic;ou=estimate_proposed_T(y,fe,fu,smr.u,idx,M.P);secsu=toc(timer);
 timer=tic;mft=estimate_b0(fe,M.B0);times.mft=toc(timer);
 fm=build_family_T(t,fe.tc,mft.g,M.B2,10,T,1);am=phaseD_ada(y,fe,fm,zeros(fm.P,1),idx,M.P,t,30,.04,'local','A');
 sc=suvorova_config();sc.band_hz=[-1.5 1.5];timer=tic;suv=estimate_suvorova_D(y,t,fe.noise_hat,sc,idx);times.suv=toc(timer);
 tc=.5*(suv.t_block(1:end-1)+suv.t_block(2:end));fsu=build_family_T(t,tc,suv.g,M.B2,10,T,1);as=phaseD_ada(y,fe,fsu,zeros(fsu.P,1),idx,M.P,t,30,.04,'local','A');
 names=[names {'UNB','MFT','MFT_FM','SUV','SUV_FM'}];gs=[gs {ou.g,mft.g,am.out.g,suv.g,as.out.g}];outs=[outs {ou,[],am,[],as}];fams=[fams {fu,[],fm,[],fsu}];secs=[secs secsu times.mft am.seconds times.suv as.seconds];
end
refs=readtable('D:\论文集\phaseA\tables\A4_groundtruth.csv');gps=tone*interp1(refs.t_s,refs.f_gps_100,start_s+t,'linear',NaN)/100;
[period,f,p0]=phaseX3_metrics(y,t,zeros(size(t)),tone,gps,idx);rows=cell(1,numel(names));spectra=zeros(numel(f),numel(names));metrics=cell(1,numel(names));
for k=1:numel(names),[metrics{k},~,spectra(:,k)]=phaseX3_metrics(y,t,gs{k},tone,gps,idx);end
inputhash=phaseD_hash(y,'MD5');
for k=1:numel(names)
 met=metrics{k};a=outs{k};rounds=0;trigger=false;dw=NaN;j=NaN;jstart=NaN;j0=NaN;fail=false;cap=false;bounds='';round0=0;expand=0;
 if any(strcmp(names{k},{'VS_FM','MFT_FM','SUV_FM'}))
  rounds=a.rounds;trigger=a.triggered;dw=a.initial_dwell_s;j=a.out.J_best;jstart=a.out.J_B2;j0=a.logs{1}.J;bounds=jsonencode(a.m);round0=a.logs{1}.seconds;expand=a.seconds-round0;
  for z=1:numel(a.logs),o=a.logs{z}.out;fail=fail||o.hard_fail;cap=cap||any(o.iters(:)>=o.max_iter(:)|o.fevals(:)>=o.max_fevals(:));end
 elseif any(strcmp(names{k},{'F02','UNB'}))
  j=a.J_best;jstart=a.J_B2;j0=j;fail=a.hard_fail;cap=any(a.iters(:)>=a.max_iter(:)|a.fevals(:)>=a.max_fevals(:));bounds=jsonencode(fams{k}.ub);round0=secs(k);
  if strcmp(names{k},'F02'),dw=phaseD_dwell(a.u,ones(fv.P,1),fv,t,idx,20);end
 elseif strcmp(names{k},'SMR'),fail=smr.fit_failed;end
 rows{k}=struct('tone_hz',tone,'segment_start_s',start_s,'segment_end_s',start_s+T,'duration_s',T,'input_hash',string(inputhash),'method',string(names{k}),'frozen_method',string(F.method),'Delta_s',10,'P',T/10+1,'peak_relative_periodogram_db',10*log10(met.peak_power/period.peak_power),'peak_frequency_hz',met.peak_frequency_hz,'prominence_db',met.prominence_db,'width_3db_hz',met.width_3db_hz,'gps_mean_offset_hz',met.gps_mean_offset_hz,'gps_demeaned_rms_hz',met.gps_demeaned_rms_hz,'gps_samples',met.gps_samples,'runtime_s',secs(k),'t_round0_s',round0,'t_expansion_s',expand,'t_frontend_s',times.frontend,'t_vit_s',times.vit,'t_smr_s',times.smr,'triggered',trigger,'expansion_rounds',rounds,'initial_dwell_s',dw,'J',j,'J_start',jstart,'J_round0',j0,'hard_fail',fail,'budget_cap',cap,'final_bounds',string(bounds),'competing_ridge',tone==103&&start_s==900,'gain_peak_vs_SMR_db',10*log10(met.peak_power/metrics{1}.peak_power),'gain_prominence_vs_SMR_db',met.prominence_db-metrics{1}.prominence_db);
end
use=abs(f-tone)<=1.5;tag=sprintf('f%d_s%d_T%d',tone,start_s,T);
if ~fullcase,tag=[tag '_duration'];end
spec=array2table([f(use) p0(use) spectra(use,:)],'VariableNames',[{'frequency_Hz','Periodogram'} names]);writetable(spec,fullfile(root,'spectra',[tag '.csv']));
tracks=array2table([start_s+t gps cell2mat(cellfun(@(g)tone+g(:),gs,'UniformOutput',false))],'VariableNames',[{'time_s','GPS_Hz'} names]);writetable(tracks,fullfile(root,'tracks',[tag '.csv']));
S=struct('rows',[rows{:}],'tone_hz',tone,'start_s',start_s,'duration_s',T,'input_hash',inputhash,'names',{names},'tracks',{gs},'outs',{outs},'families',{fams},'times',times,'extract',extract,'periodogram',period);
end
