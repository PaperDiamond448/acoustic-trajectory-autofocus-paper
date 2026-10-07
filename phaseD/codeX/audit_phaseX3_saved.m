function audit_phaseX3_saved()
maxNumCompThreads(1);phaseD_setup();addpath('D:\论文集\phaseD\codeX','-begin');root='D:\论文集\phaseD\X3_real';
files=dir(fullfile(root,'chunks','*.mat'));nr=0;maxdiff=0;rows={};rounds={};hardfail=0;budgetcap=0;
rawdir=fullfile(root,'audit_raw');if ~exist(rawdir,'dir'),mkdir(rawdir);end
for fi=1:numel(files)
 C=load(fullfile(files(fi).folder,files(fi).name));assert(strcmp(C.freeze_hash,phaseD_hash(fullfile(root,'X3_TESTSET_FREEZE.json'),'SHA-256',true)));
 for ri=1:numel(C.results)
  S=C.results(ri);nr=nr+1;[~,~,B,M]=phaseX_settings(S.duration_s,true);R=real_config();
  if S.duration_s==300,Q=load(fullfile(root,'screen_inputs',sprintf('f%d_s%d.mat',S.tone_hz,S.start_s)),'y');y=Q.y;
  else,[y,~]=phaseA_load_baseband(R.file,9,S.tone_hz,20,10,R.fs_raw,R.n_raw,S.start_s,S.duration_s,10*(S.start_s>0),10*(S.start_s+S.duration_s<3000));end
  assert(strcmp(S.input_hash,phaseD_hash(y,'MD5')));t=(0:numel(y)-1)'/20;idx=find(t>=5&t<S.duration_s-5);
  for j=1:numel(S.rows)
   r=S.rows(j);rows{end+1}=r;assert(r.P==S.duration_s/10+1&&r.Delta_s==10);
   o=S.outs{j};if isempty(o),continue;end
   fam=S.families{j};if isfield(o,'logs'),logs=o.logs;assert(numel(logs)==o.rounds+1&&o.rounds<=1&&o.triggered==(o.rounds>0));else,logs={struct('out',o,'m',fam.ub,'J',o.J_best,'seconds',r.runtime_s)};end
   for z=1:numel(logs)
    L=logs{z};q=L.out;assert(q.J_best==max(q.J)&&all(abs(q.u)<=L.m+1e-8)&&all(fam.Aineq*q.u<=fam.bineq+1e-6));assert(isequal(q.max_iter(:),M.P.max_iter(:))&&isequal(q.max_fevals(:),M.P.max_fevals(:)));
    assert(max(abs(q.g-(fam.gA+fam.r*fam.Bt*q.u)))<=1e-12);[dw,runs]=phaseD_dwell(q.u,L.m,fam,t,idx,20);
    if isfield(o,'logs')
     assert(dw==L.dwell_s&&L.J==q.J_best);
     if z<numel(logs)
      rs=runs(runs.length_s>=30,:);hit=false(fam.P,1);assert(~isempty(rs));
      for p=1:fam.P,hit(p)=any(fam.knots(min(fam.P,p+1))>rs.start_s&fam.knots(max(1,p-1))<rs.end_s);end
      hit=hit|[false;hit(1:end-1)]|[hit(2:end);false];expected=ones(fam.P,1);expected(hit)=2;next=logs{z+1};assert(isequal(next.m,expected)&&isequal(next.out.u_init,q.u)&&isequal(next.out.cands{1},q.u)&&next.J>=L.J-1e-12);
     end
    end
    hardfail=hardfail+q.hard_fail;budgetcap=budgetcap+any(q.iters(:)>=q.max_iter(:)|q.fevals(:)>=q.max_fevals(:));
    rounds{end+1}=struct('tone_hz',S.tone_hz,'segment_start_s',S.start_s,'duration_s',S.duration_s,'method',string(S.names{j}),'round',z-1,'J',q.J_best,'dwell_s',dw,'runtime_s',L.seconds);
   end
  end
  if numel(S.names)==8,suffix='';else,suffix='_duration';end
  tag=sprintf('f%d_s%d_T%d%s',S.tone_hz,S.start_s,S.duration_s,suffix);
  writematrix([t real(y) imag(y)],fullfile(rawdir,[tag '.csv']));
  % Saved no-trigger VS ADA must be the identical F02 result.
  if ~S.outs{3}.triggered,assert(isequal(S.outs{3}.out,S.outs{2}));end
  if mod(nr,20)==0,fprintf('X3 read-only audit %d/122 windows\n',nr);end
 end
end
F=jsondecode(fileread(fullfile(root,'X3_TESTSET_FREEZE.json')));assert(nr==F.passed_cases+F.duration_windows);writetable(struct2table([rounds{:}]),fullfile(root,'X3_solver_rounds.csv'));
A=struct2table([rows{:}]);a=readtable(fullfile(root,'X3_cases.csv'),'TextType','string');b=readtable(fullfile(root,'X3_duration.csv'),'TextType','string');Btab=[a;b];
key={'tone_hz','segment_start_s','duration_s','method'};A=sortrows(A,key);Btab=sortrows(Btab,key);assert(height(A)==height(Btab));
for name=A.Properties.VariableNames
 x=A.(name{1});y=Btab.(name{1});if isnumeric(x)||islogical(x),assert(isequal(isnan(double(x)),isnan(double(y))));finite=isfinite(x);diff=max(abs(double(x(finite))-double(y(finite))));if ~isempty(diff),assert(diff<=1e-10);maxdiff=max(maxdiff,diff);end;else,assert(all(string(x)==string(y)));end
end
phaseD_json(fullfile(root,'SAVED_OUTPUTS_AUDIT.json'),struct('status','PASS','windows',nr,'rows',height(A),'CSV_max_abs_difference',maxdiff,'solver_round_hard_fail',hardfail,'solver_round_budget_cap',budgetcap,'scope','Every frozen input hash, every MAT/CSV field, scaled budget, local support/warm start/objective monotonicity and no-trigger identity; raw complex input exported for independent Python spectral/GPS recomputation'));
end
