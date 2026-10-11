function S=phaseE_inject_one(bid,wid,kind,snr,rid)
root='D:\论文集';[F,cfg,B,M]=phaseX_settings(300,false);T=300;
dest=fullfile(root,'phaseE','E5_inject');q=load(fullfile(dest,'background',sprintf('b%d_w%d.mat',bid,wid)),'normalized');
seed=cfg.master_seed+57e6+10000*bid+1000*kind+20*wid+rid;t=(0:5999)'/20;
if kind==1
 rec=simulate_baseband_T(cfg,'S0',snr,seed,'eval',T);phi=rec.truth.phig;gtrue=rec.truth.gtrue;type='GEO';
else
 rs=RandStream('mt19937ar','Seed',seed);offset=-.05+.1*rand(rs);phi0=2*pi*rand(rs);
 ref=readtable(fullfile(root,'当前主线精选_20261003','04_实测数据','表','A4_groundtruth.csv'));
 gtrue=interp1(ref.t_s,ref.f_gps_100,300*wid+t,'linear',NaN)-100+offset;
 assert(all(isfinite(gtrue)),'PhaseE:GPSMissing','GPS reference does not cover this background window.');
 phi=2*pi*cumtrapz(t,gtrue)+phi0;type='GPS';
 rec=struct('t',t,'fs',20,'truth',struct('scene',type,'snr_db',snr,'seed',seed,'offset_hz',offset,'phi0',phi0));
end
signal=10^(snr/20)*exp(1i*phi);rec.y=q.normalized+signal;
rec.truth.gtrue=gtrue;rec.truth.phig=phi;rec.truth.amp=ones(size(t));rec.truth.s_target=signal;rec.truth.has_target=true;
hash=phaseD_hash(rec.y,'MD5');[fe,v,idx,times]=phaseX_front(rec.y,t,B,M);
fv=build_family_T(t,fe.tc,v.g,M.B2,10,T,1);timer=tic;lps=estimate_b2(fe,fv,M.B2);times.smr=toc(timer);
timer=tic;mft=estimate_b0(fe,M.B0);times.mft=toc(timer);
timer=tic;suv=estimate_suvorova_D(rec.y,t,fe.noise_hat,suvorova_config(),idx);times.suv=toc(timer);
dc=jsondecode(fileread(fullfile(root,'phaseE','E2_frontend_ext','DHMM_FROZEN.json')));
assert(strcmp(phaseD_hash(fullfile(root,'phaseE','scripts','estimate_dhmm.m'),'SHA-256',true),dc.implementation_sha256));
timer=tic;dh=estimate_dhmm(fe,dc);times.dhmm=toc(timer);
names={'VS','V0','MFT','SUV','SUV_GRID','DHMM'};
ins={lps.g,v.g,mft.g,suv.g,suv.g_bin,dh.g};anchors={v.g,v.g,mft.g,suv.g,suv.g_bin,dh.g};
checks={fe.tc,fe.tc,fe.tc,.5*(suv.t_block(1:end-1)+suv.t_block(2:end)),suv.t_block,fe.tc};
rows=cell(1,6);details=cell(1,6);
for k=1:6
 fam=build_family_T(t,checks{k},anchors{k},M.B2,10,T,1);
 if k==1,u0=lps.u;else,u0=zeros(fam.P,1);end
 g=ins{k};e=g(idx)-gtrue(idx);usable=mean(abs(e-mean(e))<=.1);mi=phaseD_measure(rec,g,idx,B);
 a=phaseD_ada(rec.y,fe,fam,u0,idx,M.P,t,30,.04,'local','A');mo=phaseD_measure(rec,a.out.g,idx,B);
 rows{k}=struct('band_id',bid,'window_id',wid,'background_start_s',300*wid,'target_kind',kind,'scene',string(type), ...
  'snr_db',snr,'record_id',rid,'seed',seed,'input_hash',string(hash),'frontend',string(names{k}), ...
  'duration_s',T,'phase_id',57,'Delta_s',10,'P',fam.P,'method',string(F.method),'eta_in',mi.eta,'eta_out',mo.eta, ...
  'gain_eta',mo.eta-mi.eta,'peak_in_db',mi.peak_db,'peak_out_db',mo.peak_db,'gain_peak_db',mo.peak_db-mi.peak_db, ...
  'usable_fraction',usable,'input_usable',usable>=.9,'gain_positive',mo.eta>mi.eta, ...
  'runtime_s',a.seconds,'t_round0_s',a.logs{1}.seconds,'t_expansion_s',a.seconds-a.logs{1}.seconds, ...
  'triggered',a.triggered,'expansion_rounds',a.rounds,'initial_dwell_s',a.initial_dwell_s, ...
  'J',a.out.J_best,'J_start',a.out.J_B2,'J_round0',a.logs{1}.J,'hard_fail',a.out.hard_fail, ...
  'budget_cap',any(a.out.iters(:)>=a.out.max_iter(:)|a.out.fevals(:)>=a.out.max_fevals(:)), ...
  'final_bounds',string(jsonencode(a.m)),'exitflags',string(jsonencode(a.out.exitflags)), ...
  'iterations',string(jsonencode(a.out.iters)),'fevals',string(jsonencode(a.out.fevals)), ...
  't_frontend_s',times.frontend,'t_vit_s',times.vit,'t_smr_s',times.smr,'t_mft_s',times.mft, ...
  't_suv_s',times.suv,'t_dhmm_s',times.dhmm);
 details{k}=struct('frontend',names{k},'input_g',g,'output_g',a.out.g,'anchor_g',anchors{k}, ...
  'u_start',u0,'u_final',a.out.u,'ada',a);
end
S=struct('rows',[rows{:}],'details',{details},'truth_g',gtrue,'truth_phase',phi, ...
 'target_random_parameters',rec.truth,'input_hash',hash,'scene',type,'snr_db',snr, ...
 'record_id',rid,'seed',seed,'duration_s',T,'band_id',bid,'window_id',wid,'target_kind',kind);
end
