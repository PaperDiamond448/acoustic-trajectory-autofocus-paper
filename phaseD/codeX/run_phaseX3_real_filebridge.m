function run_phaseX3_real_filebridge()
root='D:\论文集\phaseD';phaseD_setup();addpath(fullfile(root,'codeX'),'-begin');phaseX_verify_sources();outdir=fullfile(root,'X3_real');
freeze=jsondecode(fileread(fullfile(outdir,'X3_TESTSET_FREEZE.json')));assert(strcmp(freeze.status,'FROZEN_BEFORE_ANY_REAL_MODULE'));
% JSON path keys are transformed by jsondecode; explicitly check known files.
checks={'X3_visibility.csv','X3_FROZEN_TESTSET.csv','X3_FROZEN_DURATION_TESTSET.csv'};
proof=readtable(fullfile(outdir,'X3_FREEZE_MANIFEST.csv'),'Delimiter',',','Encoding','UTF-8','ReadVariableNames',true,'VariableNamingRule','preserve','TextType','string');
assert(isequal(proof.Properties.VariableNames,{'source_file','sha256'}),'Freeze CSV schema mismatch');
for k=1:height(proof),assert(strcmp(phaseD_hash(char(proof.source_file(k)),'SHA-256',true),proof.sha256(k)));end
for name={'spectra','tracks','chunks'},if ~exist(fullfile(outdir,name{1}),'dir'),mkdir(fullfile(outdir,name{1}));end,end
pool=gcp('nocreate');if isempty(pool),pool=parpool('Processes',6);end;assert(pool.NumWorkers==6);
timer=tic;diary(fullfile(outdir,'X3_matlab.log'));allrows={};durrows={};completed=0;
for kind=1:2
 if kind==1,K=readtable(fullfile(outdir,checks{2}));Ts=300*ones(height(K),1);else,K=readtable(fullfile(outdir,checks{3}));Ts=K.duration_s;end
 for ch=1:ceil(height(K)/10)
  ids=(ch-1)*10+1:min(ch*10,height(K));file=fullfile(outdir,'chunks',sprintf('kind%d_chunk%03d.mat',kind,ch));
  if exist(file,'file'),C=load(file,'results','freeze_hash');assert(strcmp(C.freeze_hash,phaseD_hash(fullfile(outdir,'X3_TESTSET_FREEZE.json'),'SHA-256',true)));results=C.results;
  else
   cells=cell(numel(ids),1);tones=K.tone_hz(ids);starts=K.segment_start_s(ids);Tvals=Ts(ids);
   wd=fullfile(outdir,'worker_records');if ~exist(wd,'dir'),mkdir(wd);end
   fh=phaseD_hash(fullfile(outdir,'X3_TESTSET_FREEZE.json'),'SHA-256',true);records=cell(numel(ids),1);
   for j=1:numel(ids),records{j}=fullfile(wd,sprintf('kind%d_f%d_s%d_T%d.mat',kind,tones(j),starts(j),Tvals(j)));end
   parfor j=1:numel(ids),phaseX_save_real_worker(tones(j),starts(j),Tvals(j),kind==1,records{j},fh);end
   for j=1:numel(ids),Q=load(records{j},'S','freeze_hash');assert(strcmp(Q.freeze_hash,fh));cells{j}=Q.S;end
   results=[cells{:}];freeze_hash=phaseD_hash(fullfile(outdir,'X3_TESTSET_FREEZE.json'),'SHA-256',true);
   partial=[file '.partial.mat'];save(partial,'results','freeze_hash','-v7');movefile(partial,file);
  end
  for j=1:numel(results),if kind==1,allrows{end+1}=results(j).rows;else,durrows{end+1}=results(j).rows;end,end
  completed=completed+numel(results);phaseD_json(fullfile(outdir,'run_status.json'),struct('stage','X3','completed',completed,'kind',kind,'elapsed_seconds',toc(timer)));fprintf('X3 kind%d %d/%d %.1f seconds\n',kind,min(ch*10,height(K)),height(K),toc(timer));
 end
end
if ~isempty(allrows),writetable(struct2table([allrows{:}]),fullfile(outdir,'X3_cases.csv'));end
if ~isempty(durrows),writetable(struct2table([durrows{:}]),fullfile(outdir,'X3_duration.csv'));end
phaseD_json(fullfile(outdir,'X3_run_config.json'),struct('status','COMPLETE','cases',freeze.passed_cases,'duration_windows',freeze.duration_windows,'elapsed_wall_seconds',toc(timer),'workers',6,'matlab',version,'timing','Loaded six-worker call wall time; sequential X batches'));
delete(pool);diary off;
end
