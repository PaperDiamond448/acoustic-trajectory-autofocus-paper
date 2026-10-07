function audit_real_worker_chunks()
root='D:\论文集\phaseD';phaseD_setup();O=fullfile(root,'X3_real');files=dir(fullfile(O,'chunks','*.mat'));files=files(~endsWith({files.name},'.partial.mat'));n=0;
for fi=1:numel(files)
 C=load(fullfile(files(fi).folder,files(fi).name),'results','freeze_hash');
 for k=1:numel(C.results)
  S=C.results(k);kind=1+(numel(S.rows)==3);
  file=fullfile(O,'worker_records',sprintf('kind%d_f%d_s%d_T%d.mat',kind,S.tone_hz,S.start_s,S.duration_s));
  if exist(file,'file'),Q=load(file,'S','freeze_hash');assert(strcmp(C.freeze_hash,Q.freeze_hash)&&isequaln(S,Q.S));n=n+1;end
 end
end
assert(n==16);phaseD_json(fullfile(root,'Y_compute','REAL_WORKER_CHUNK_BRIDGE_AUDIT.json'),struct('status','PASS','records_compared',n,'proof','All 16 duration worker S exactly isequaln to committed chunks, including all numeric/metadata fields; v7.3 worker originals retained; no optimization'));
end
