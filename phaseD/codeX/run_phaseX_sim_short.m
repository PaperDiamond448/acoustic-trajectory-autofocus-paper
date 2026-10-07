function run_phaseX_sim_short(stage,firstjob,lastjob)
% Environment-only batch adapter. Numerical functions and original signatures unchanged.
root='D:\论文集\phaseD';phaseD_setup();addpath(fullfile(root,'codeX'),'-begin');phaseX_verify_sources();
if strcmp(stage,'X1'),folder='X1_duration';snrs=[-20 -17 -14];Ts=[150 300 450 600];phase=53;total=2400;else,assert(strcmp(stage,'X2'));folder='X2_frontend';snrs=-20:2:-8;Ts=300;phase=54;total=1400;end
O=fullfile(root,folder);if ~exist(fullfile(O,'chunks'),'dir'),mkdir(fullfile(O,'chunks'));end
sig=phaseD_hash(fullfile(root,'codeX','SOURCE_MANIFEST_X_sha256.csv'),'SHA-256',true);
jobs={};for T=Ts,for sc={'S0','S2'},for snr=snrs,for ch=1:10,jobs{end+1}=struct('T',T,'scene',sc{1},'snr',snr,'ch',ch);end,end,end,end
assert(firstjob>=1&&lastjob<=numel(jobs));pool=gcp('nocreate');if isempty(pool),pool=parpool('Processes',6);end;assert(pool.NumWorkers==6);timer=tic;new=0;
for ji=firstjob:lastjob
 J=jobs{ji};ids=(J.ch-1)*10+(1:10);file=fullfile(O,'chunks',sprintf('T%d_%s_%+03ddB_chunk_%03d.mat',J.T,J.scene,J.snr,J.ch));
 if exist(file,'file'),C=load(file,'signature','phase_id');assert(strcmp(C.signature,sig)&&C.phase_id==phase);
 else
  cells=cell(10,1);scene=J.scene;snr=J.snr;T=J.T;
  parfor k=1:10,if strcmp(stage,'X1'),cells{k}=phaseX1_one(scene,snr,ids(k),T);else,cells{k}=phaseX2_one(scene,snr,ids(k));end,end
  results=[cells{:}];signature=sig;phase_id=phase;
  partial=[file '.partial.mat'];save(partial,'results','signature','phase_id','-v7.3');movefile(partial,file);new=new+10;
 end
 d=dir(fullfile(O,'chunks','*.mat'));n=sum(~endsWith({d.name},'.partial.mat'))*10;
 phaseD_json(fullfile(O,'run_status.json'),struct('stage',stage,'records_completed',n,'records_total',total,'last_job',ji,'short_batch_seconds',toc(timer),'workers',6));fprintf('%s short batch job%d; %d/%d records %.1fs\n',stage,ji,n,total,toc(timer));
end
phaseD_json(fullfile(O,sprintf('short_batch_%03d_%03d.json',firstjob,lastjob)),struct('stage',stage,'first_job',firstjob,'last_job',lastjob,'new_records',new,'elapsed_wall_seconds',toc(timer),'workers',6,'source_signature',sig,'adapter','run_phaseX_sim_short: same frozen numerical function, original signature and v7.3 output schema; fresh MATLAB process'));
delete(pool);
end
