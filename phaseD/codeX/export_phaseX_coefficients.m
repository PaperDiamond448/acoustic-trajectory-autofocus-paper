function export_phaseX_coefficients()
phaseD_setup();root='D:\论文集\phaseD';
for folder={'X1_duration','X2_frontend','X3_real'}
 O=fullfile(root,folder{1});files=dir(fullfile(O,'chunks','*.mat'));files=files(~endsWith({files.name},'.partial.mat'));groups=containers.Map('KeyType','double','ValueType','any');
 for fi=1:numel(files)
  C=load(fullfile(files(fi).folder,files(fi).name),'results');
  for ri=1:numel(C.results)
   S=C.results(ri);if isfield(S,'duration_s'),T=S.duration_s;else,T=300;end
   if isKey(groups,T),G=groups(T);else,G=struct('u',[],'u0',[],'bounds',[],'keys',{{}});end
   for k=1:numel(S.rows)
    r=S.rows(k);
    if strcmp(folder{1},'X1_duration')
     if k==1,u=S.smr.u;u0=u;b=ones(numel(u),1);elseif k==2,u=S.F02.u;u0=S.F02.u_init;b=ones(numel(u),1);elseif k==3,u=S.UNB.u;u0=S.UNB.u_init;b=Inf(numel(u),1);else,u=S.ada.out.u;u0=S.ada.logs{1}.out.u_init;b=S.ada.m;end
     key=struct('scene',r.scene,'snr_db',r.snr_db,'record_id',r.record_id,'seed',r.seed,'input_hash',r.input_hash,'duration_s',T,'method',r.method);
    elseif strcmp(folder{1},'X2_frontend')
     a=S.details{k}.ada;u=a.out.u;u0=a.logs{1}.out.u_init;b=a.m;
     key=struct('scene',r.scene,'snr_db',r.snr_db,'record_id',r.record_id,'seed',r.seed,'input_hash',r.input_hash,'duration_s',T,'frontend',r.frontend,'method',r.method);
    else
     a=S.outs{k};
     if k==1,u=S.outs{2}.u_init;u0=u;b=ones(numel(u),1);
     elseif isempty(a),u=zeros(T/10+1,1);u0=u;b=ones(numel(u),1);
     elseif isfield(a,'logs'),u=a.out.u;u0=a.logs{1}.out.u_init;b=a.m;
     else,u=a.u;u0=a.u_init;b=S.families{k}.ub;end
     if numel(S.rows)==8,kind='case';else,kind='duration';end
     key=struct('tone_hz',r.tone_hz,'segment_start_s',r.segment_start_s,'duration_s',T,'input_hash',r.input_hash,'dataset',string(kind),'method',r.method);
    end
    G.u(:,end+1)=u;G.u0(:,end+1)=u0;G.bounds(:,end+1)=b;key.column_1based=size(G.u,2);key.P=numel(u);G.keys{end+1}=key;
   end
   groups(T)=G;
  end
 end
 for T=sort(cell2mat(keys(groups)))
  G=groups(T);u=G.u;u0=G.u0;bounds=G.bounds;keytable=struct2table([G.keys{:}]);
  tag=sprintf('coefficients_T%d',T);save(fullfile(O,[tag '.mat']),'u','u0','bounds','-v7.3');writetable(keytable,fullfile(O,[tag '_keys.csv']));
  assert(size(u,1)==T/10+1&&size(u,2)==height(keytable));fprintf('%s T%d coefficient matrix %dx%d\n',folder{1},T,size(u,1),size(u,2));
 end
end
phaseD_json(fullfile(root,'Y_compute','COEFFICIENT_EXPORT.json'),struct('status','COMPLETE','format','v7.3','column_keys','Companion *_keys.csv; column_1based identifies matrix column','scope','Exact saved coefficients, original module initial coefficients and final bounds; no optimizer rerun'));
end
