function audit_phaseX2_registered_shard(stage,firstfile,lastfile)
% Read-only reconstruction of every saved numerical output; never optimizes.
maxNumCompThreads(1);root='D:\论文集\phaseD';phaseD_setup();addpath(fullfile(root,'codeX'),'-begin');phaseX_verify_sources();
if strcmp(stage,'X1'),folder='X1_duration';total=2400;phase=53;else,assert(strcmp(stage,'X2'));folder='X2_frontend';total=1400;phase=54;end
O=fullfile(root,folder);files=dir(fullfile(O,'chunks','*.mat'));files=files(~endsWith({files.name},'.partial.mat'));
assert(firstfile>=1&&lastfile<=numel(files));files=files(firstfile:lastfile);total=numel(files)*10;
outdir=fullfile(O,'qa_shards');if ~exist(outdir,'dir'),mkdir(outdir);end;tag=sprintf('shard_%03d_%03d',firstfile,lastfile);
csv=readtable(fullfile(O,[stage '_records.csv']),'TextType','string');keep=false(height(csv),1);
for fi=1:numel(files)
 token=regexp(files(fi).name,'^T(\d+)_(S[02])_([+-]\d+)dB_chunk_(\d+)\.mat$','tokens','once');assert(numel(token)==4);
 Tmask=str2double(token{1});snrmask=str2double(token{3});chmask=str2double(token{4});
 match=csv.scene==string(token{2})&csv.snr_db==snrmask&csv.record_id>(chmask-1)*10&csv.record_id<=chmask*10;
 if phase==53,match=match&csv.duration_s==Tmask;end;keep=keep|match;
end
csv=csv(keep,:);assert(height(csv)==4*total);nr=0;rows=0;maxdiff=0;rounds={};smrdwell={};hardfail=0;cap=0;
map=containers.Map('KeyType','char','ValueType','double');
for j=1:height(csv)
 if phase==53,key=sprintf('%s/%g/%d/%d/%s',csv.scene(j),csv.snr_db(j),csv.record_id(j),csv.duration_s(j),csv.method(j));
 else,key=sprintf('%s/%g/%d/%s',csv.scene(j),csv.snr_db(j),csv.record_id(j),csv.frontend(j));end
 assert(~isKey(map,key));map(key)=j;
end
for fi=1:numel(files)
 C=load(fullfile(files(fi).folder,files(fi).name));assert(C.phase_id==phase);
 for ri=1:numel(C.results)
  S=C.results(ri);nr=nr+1;if phase==53,T=S.duration_s;else,T=300;end
  [~,cfg,B,M]=phaseX_settings(T,false);seed=cfg.master_seed+phase*1e6+1e4*cfg.scene_code.(S.scene)+S.record_id;
  rec=simulate_baseband_T(cfg,S.scene,S.snr_db,seed,'eval',T);idx=find(rec.t>=5&rec.t<T-5);
  assert(strcmp(S.input_hash,phaseD_hash(rec.y,'MD5')));
  if phase==53
   fam=S.family;check_out(S.F02,ones(fam.P,1),fam,rec.y,idx,M.P,B.band(2));check_out(S.UNB,Inf(fam.P,1),fam,rec.y,idx,M.P,B.band(2));
   assert(isequal(S.F02.u_init,S.smr.u)&&isequal(S.UNB.u_init,S.smr.u));check_ada(S.ada,fam,rec.y,rec.t,idx,M.P,B.band(2));assert(isequal(S.ada.logs{1}.out,S.F02));
   if ~S.ada.triggered,assert(isequal(S.ada.out,S.F02));end
   gs={S.smr.g,S.F02.g,S.UNB.g,S.ada.out.g};
   dw=phaseD_dwell(S.smr.u,ones(fam.P,1),fam,rec.t,idx,20);smrdwell{end+1}=struct('scene',string(S.scene),'snr_db',S.snr_db,'record_id',S.record_id,'duration_s',T,'SMR_dwell_s',dw,'F02_dwell_s',S.ada.initial_dwell_s);
   adas={S.ada};fronts={'VS'};
  else
   adas=cellfun(@(x)x.ada,S.details,'UniformOutput',false);fronts=cellfun(@(x)x.frontend,S.details,'UniformOutput',false);
  end
  for k=1:4
   r=S.rows(k);rows=rows+1;assert(r.seed==seed&&strcmp(r.input_hash,S.input_hash));assert(r.P==T/10+1&&r.Delta_s==10);
   if phase==53
    key=sprintf('%s/%g/%d/%d/%s',r.scene,r.snr_db,r.record_id,T,r.method);met=phaseD_measure(rec,gs{k},idx,B);
    saved=[r.eta r.peak_db r.prominence_db r.width_3db_hz r.track_rmse_hz r.max_error_hz r.longest_out_0p02_s];recomputed=[met.eta met.peak_db met.prom_db met.width met.rmse met.maxabs met.longest];
   else
    d=S.details{k};a=d.ada;fam=d.family;check_ada(a,fam,rec.y,rec.t,idx,M.P,2,false);
    e=d.input_g(idx)-rec.truth.gtrue(idx);fraction=mean(abs(e-mean(e))<=.1);assert(fraction==r.usable_fraction&&r.input_usable==(fraction>=.9));
    if k==1,assert(max(abs(d.input_g-(fam.gA+fam.r*fam.Bt*a.logs{1}.out.u_init)))<=1e-12);else,assert(isequal(a.logs{1}.out.u_init,zeros(fam.P,1)));assert(isequal(d.input_g,fam.gA));end
    mi=phaseD_measure(rec,d.input_g,idx,B);mo=phaseD_measure(rec,a.out.g,idx,B);
    saved=[r.eta_in r.eta_out r.gain_eta r.peak_in_db r.peak_out_db r.gain_peak_db];recomputed=[mi.eta mo.eta mo.eta-mi.eta mi.peak_db mo.peak_db mo.peak_db-mi.peak_db];
    key=sprintf('%s/%g/%d/%s',r.scene,r.snr_db,r.record_id,r.frontend);
   end
   assert(isequal(isnan(saved),isnan(recomputed)));delta=max(abs(saved(~isnan(saved))-recomputed(~isnan(recomputed))));assert(delta<=1e-12);maxdiff=max(maxdiff,delta);
   maxdiff=max(maxdiff,reconcile_row(r,csv,map(key)));
  end
  for j=1:numel(adas)
   a=adas{j};for z=1:numel(a.logs)
    o=a.logs{z}.out;hardfail=hardfail+o.hard_fail;cap=cap+any(o.iters(:)>=o.max_iter(:)|o.fevals(:)>=o.max_fevals(:));
    rounds{end+1}=struct('scene',string(S.scene),'snr_db',S.snr_db,'record_id',S.record_id,'duration_s',T,'frontend',string(fronts{j}),'round',z-1,'runtime_s',a.logs{z}.seconds,'J',a.logs{z}.J,'dwell_s',a.logs{z}.dwell_s);
   end
  end
  if mod(nr,200)==0,fprintf('%s read-only audit %d/%d\n',stage,nr,total);end
 end
end
assert(nr==total&&rows==4*total);writetable(struct2table([rounds{:}]),fullfile(outdir,[tag '_ADA_rounds.csv']));
if phase==53,writetable(struct2table([smrdwell{:}]),fullfile(outdir,[tag '_SMR_F02_dwell.csv']));end
phaseD_json(fullfile(outdir,[tag '_AUDIT.json']),struct('status','PASS','records',nr,'rows',rows,'all_metrics_and_CSV_max_abs_difference',maxdiff,'ADA_solver_round_hard_fail',hardfail,'ADA_solver_round_budget_cap',cap,'scope','All inputs regenerated using fresh phase seed; every saved metric, every CSV field, scaled budgets, candidate selection, local expansion support, warm starts, full-objective monotonicity and nontrigger identity checked read-only'));
end

function check_ada(a,fam,y,t,idx,PC,band,enforce_dense)
if nargin<8,enforce_dense=true;end
assert(a.rounds<=1&&a.triggered==(a.rounds>0)&&numel(a.logs)==a.rounds+1);
assert(isequal(a.out,a.logs{end}.out)&&a.seconds==sum(cellfun(@(x)x.seconds,a.logs)));
for k=1:numel(a.logs)
 L=a.logs{k};check_out(L.out,L.m,fam,y,idx,PC,band,enforce_dense);
 [dw,runs]=phaseD_dwell(L.out.u,L.m,fam,t,idx,20);assert(dw==L.dwell_s&&L.J==L.out.J_best);
 if k<numel(a.logs)
  rs=runs(runs.length_s>=30,:);assert(~isempty(rs));hit=false(fam.P,1);
  for p=1:fam.P,lo=fam.knots(max(1,p-1));hi=fam.knots(min(fam.P,p+1));hit(p)=any(hi>rs.start_s&lo<rs.end_s);end
  hit=hit|[false;hit(1:end-1)]|[hit(2:end);false];expected=ones(fam.P,1);expected(hit)=2;
  next=a.logs{k+1};assert(isequal(next.m,expected)&&isequal(next.out.u_init,L.out.u)&&isequal(next.out.cands{1},L.out.u)&&next.J>=L.J-1e-12);
 end
end
end

function check_out(o,m,fam,y,idx,PC,band,enforce_dense)
if nargin<8,enforce_dense=true;end
assert(all(isfinite(o.u))&&numel(o.u)==fam.P&&all(abs(o.u)<=m+1e-8));assert(all(fam.Aineq*o.u<=fam.bineq+1e-6));
assert(max(abs(o.g-(fam.gA+fam.r*fam.Bt*o.u)))<=1e-12);
if enforce_dense,assert(max(abs(o.g))<=band+1e-6);end
% For X2, registered frame/SUV-midpoint Aineq/binEq is mandatory above; dense sampled extrema are separately diagnosed, never clipped.
assert(o.J_best==max(o.J));ib=find(strcmp(o.J_labels,o.selected));assert(isscalar(ib)&&isequal(o.u,o.cands{ib}));
assert(isequal(o.max_iter(:),PC.max_iter(:))&&isequal(o.max_fevals(:),PC.max_fevals(:)));
ctx=struct('y',y(idx),'phiA',fam.phiA(idx),'H',fam.H(idx,:),'P',fam.P,'DtD',fam.D2.'*fam.D2,'lambda',PC.lambda_C,'E',sum(abs(y(idx)).^2)+eps);
ctx.blk=make_blocks(numel(idx),PC.h_stages_s(end)*20);
for k=1:numel(o.cands)
 u=o.cands{k};ok=all(abs(u)<=m+1e-8)&&all(fam.Aineq*u<=fam.bineq+1e-6);
 if ok,assert(abs(o.J(k)+coherence_objective(u,ctx))<=1e-12);else,assert(o.J(k)==-Inf);end
end
end

function md=reconcile_row(r,T,j)
md=0;names=fieldnames(r);
for k=1:numel(names)
 a=r.(names{k});b=T.(names{k})(j);
 if isnumeric(a)||islogical(a)
  assert(isequal(isnan(double(a)),isnan(double(b))));if isfinite(double(a)),d=abs(double(a)-double(b));assert(d<=1e-10);md=max(md,d);else,assert(isequaln(double(a),double(b)));end
 else,assert(strcmp(string(a),string(b)));end
end
end
