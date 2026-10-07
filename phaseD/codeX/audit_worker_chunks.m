function audit_worker_chunks()
root='D:\论文集\phaseD';phaseD_setup();n=0;
for folder={'X1_duration','X2_frontend'}
 O=fullfile(root,folder{1});files=dir(fullfile(O,'chunks','*.mat'));files=files(~endsWith({files.name},'.partial.mat'));
 for fi=1:numel(files)
  C=load(fullfile(files(fi).folder,files(fi).name),'results');
  for k=1:numel(C.results)
   S=C.results(k);if isfield(S,'duration_s'),T=S.duration_s;else,T=300;end
   f=fullfile(O,'worker_records',sprintf('T%d_%s_%+03ddB_r%03d.mat',T,S.scene,S.snr_db,S.record_id));
   if exist(f,'file'),Q=load(f,'S');assert(isequaln(S,Q.S),'Saved worker result differs from submitted chunk.');n=n+1;end
  end
 end
end
phaseD_json(fullfile(root,'Y_compute','WORKER_CHUNK_BRIDGE_AUDIT.json'),struct('status','PASS','records_compared',n,'proof','Every completed worker-file S is exactly isequaln to its committed chunk copy, including all numerical and metadata fields; no optimization'));
end
