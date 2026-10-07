function S=phaseE_ext_one(stage,scene,snr,rid,T)
root='D:\论文集';[F,cfg,B,M]=phaseX_settings(T,false);
if strcmp(stage,'C'),phase=53;else,phase=54;end
seed=cfg.master_seed+phase*1e6+1e4*cfg.scene_code.(scene)+rid;
rec=simulate_baseband_T(cfg,scene,snr,seed,'eval',T);hash=phaseD_hash(rec.y,'MD5');
if phase==54
 old=readtable(fullfile(root,'phaseD','X2_frontend','X2_records.csv'),'TextType','string');
 old=old(old.scene==string(scene)&old.snr_db==snr&old.record_id==rid,:);
else
 old=readtable(fullfile(root,'phaseD','X1_duration','X1_records.csv'),'TextType','string');
 old=old(old.scene==string(scene)&old.snr_db==snr&old.record_id==rid&old.duration_s==T,:);
end
assert(height(old)>0&&all(old.input_hash==string(hash)),'PhaseE:InputMismatch','Input does not match archived X1/X2.');
[fe,v,idx,times]=phaseX_front(rec.y,rec.t,B,M);
timer=tic;suv=estimate_suvorova_D(rec.y,rec.t,fe.noise_hat,suvorova_config(),idx);times.suv=toc(timer);
times.smr=0;times.mft=0;times.dhmm=0;
if strcmp(stage,'B_reg')
 fam=build_family_T(rec.t,fe.tc,v.g,M.B2,10,T,1);
 timer=tic;lps=estimate_b2(fe,fam,M.B2);times.smr=toc(timer);
 names={'VS','SUV'};ins={lps.g,suv.g};anchors={v.g,suv.g};
 checks={fe.tc,.5*(suv.t_block(1:end-1)+suv.t_block(2:end))};
 starts={lps.u,zeros(fam.P,1)};
elseif strcmp(stage,'B')
 file=fullfile(root,'phaseE','E2_frontend_ext','DHMM_FROZEN.json');dc=jsondecode(fileread(file));
 assert(strcmp(phaseD_hash(fullfile(root,'phaseE','scripts','estimate_dhmm.m'),'SHA-256',true),dc.implementation_sha256));
 timer=tic;dh=estimate_dhmm(fe,dc);times.dhmm=toc(timer);
 names={'SUV_GRID','DHMM','ORACLE'};ins={suv.g_bin,dh.g,rec.truth.gtrue};anchors=ins;
 checks={suv.t_block,fe.tc,fe.tc};starts={[],[],[]};
else
 assert(strcmp(stage,'C'));names={'SUV','ORACLE'};ins={suv.g,rec.truth.gtrue};anchors=ins;
 checks={.5*(suv.t_block(1:end-1)+suv.t_block(2:end)),fe.tc};starts={[],[]};
end
rows=cell(1,numel(names));details=cell(1,numel(names));regcheck=cell(1,numel(names));
for k=1:numel(names)
 g=ins{k};fam=build_family_T(rec.t,checks{k},anchors{k},M.B2,10,T,1);
 if isempty(starts{k}),u0=zeros(fam.P,1);else,u0=starts{k};end
 e=g(idx)-rec.truth.gtrue(idx);usable=mean(abs(e-mean(e))<=.1);mi=phaseD_measure(rec,g,idx,B);
 a=phaseD_ada(rec.y,fe,fam,u0,idx,M.P,rec.t,30,.04,'local','A');mo=phaseD_measure(rec,a.out.g,idx,B);
 r=struct('scene',string(scene),'snr_db',snr,'record_id',rid,'seed',seed,'input_hash',string(hash), ...
  'frontend',string(names{k}),'duration_s',T,'phase_id',phase,'Delta_s',10,'P',fam.P,'method',string(F.method), ...
  'eta_in',mi.eta,'eta_out',mo.eta,'gain_eta',mo.eta-mi.eta,'peak_in_db',mi.peak_db,'peak_out_db',mo.peak_db, ...
  'gain_peak_db',mo.peak_db-mi.peak_db,'usable_fraction',usable,'input_usable',usable>=.9, ...
  'gain_positive',mo.eta>mi.eta,'runtime_s',a.seconds,'t_round0_s',a.logs{1}.seconds, ...
  't_expansion_s',a.seconds-a.logs{1}.seconds,'triggered',a.triggered,'expansion_rounds',a.rounds, ...
  'initial_dwell_s',a.initial_dwell_s,'J',a.out.J_best,'J_start',a.out.J_B2,'J_round0',a.logs{1}.J, ...
  'hard_fail',a.out.hard_fail,'fallback',a.out.fallback, ...
  'budget_cap',any(a.out.iters(:)>=a.out.max_iter(:)|a.out.fevals(:)>=a.out.max_fevals(:)), ...
  'final_bounds',string(jsonencode(a.m)),'exitflags',string(jsonencode(a.out.exitflags)), ...
  'iterations',string(jsonencode(a.out.iters)),'fevals',string(jsonencode(a.out.fevals)), ...
  't_frontend_s',times.frontend,'t_vit_s',times.vit,'t_smr_s',times.smr,'t_mft_s',times.mft, ...
  't_suv_s',times.suv,'t_dhmm_s',times.dhmm,'oracle_diagnostic',strcmp(names{k},'ORACLE'));
 if strcmp(stage,'B_reg')
  expected=old(old.frontend==r.frontend,:);assert(height(expected)==1);
  di=abs(r.eta_in-expected.eta_in);doo=abs(r.eta_out-expected.eta_out);
  assert(di<1e-9&&doo<1e-9,'PhaseE:RegressionMismatch','VS/SUV did not reproduce X2.');
  regcheck{k}=struct('scene',string(scene),'snr_db',snr,'record_id',rid,'frontend',r.frontend, ...
   'input_hash_match',true,'eta_in_abs_diff',di,'eta_out_abs_diff',doo,'passed',true);
 end
 rows{k}=r;details{k}=struct('frontend',names{k},'input_g',g,'output_g',a.out.g, ...
  'anchor_g',anchors{k},'u_start',u0,'u_final',a.out.u,'ada',a);
end
S=struct('rows',[rows{:}],'details',{details},'truth_g',rec.truth.gtrue,'input_hash',hash, ...
 'scene',scene,'snr_db',snr,'record_id',rid,'seed',seed,'duration_s',T,'regcheck',{regcheck});
S.suv_debug=suv;S.truth_phase=rec.truth.phig;
end
