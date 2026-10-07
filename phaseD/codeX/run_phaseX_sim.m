function run_phaseX_sim(stage)
root='D:\论文集\phaseD';phaseD_setup();addpath(fullfile(root,'codeX'),'-begin');phaseX_verify_sources();
if strcmp(stage,'X1'),outdir=fullfile(root,'X1_duration');snrs=[-20 -17 -14];durations=[150 300 450 600];total=2400;phase=53;
else,assert(strcmp(stage,'X2'));outdir=fullfile(root,'X2_frontend');snrs=-20:2:-8;durations=300;total=1400;phase=54;end
folder=fullfile(outdir,'chunks');if ~exist(folder,'dir'),mkdir(folder);end
diary(fullfile(outdir,[stage '_matlab.log']));pool=gcp('nocreate');if isempty(pool),pool=parpool('Processes',6);end;assert(pool.NumWorkers==6);
sig=phaseD_hash(fullfile(root,'codeX','SOURCE_MANIFEST_X_sha256.csv'),'SHA-256',true);completed=0;timer=tic;allrows={};
for T=durations
 for sc={'S0','S2'}
  for snr=snrs
   for ch=1:10
    ids=(ch-1)*10+(1:10);file=fullfile(folder,sprintf('T%d_%s_%+03ddB_chunk_%03d.mat',T,sc{1},snr,ch));
    if exist(file,'file'),C=load(file,'results','signature','phase_id');assert(strcmp(C.signature,sig)&&C.phase_id==phase);results=C.results;
    else
     cells=cell(10,1);scene=sc{1};
     parfor k=1:10
      if strcmp(stage,'X1'),cells{k}=phaseX1_one(scene,snr,ids(k),T);else,cells{k}=phaseX2_one(scene,snr,ids(k));end
     end
     results=[cells{:}];signature=sig;phase_id=phase;
     partial=[file '.partial.mat'];save(partial,'results','signature','phase_id','-v7.3');movefile(partial,file);
    end
    assert(isequal([results.record_id],ids));for k=1:10,allrows{end+1}=results(k).rows;end
    completed=completed+10;phaseD_json(fullfile(outdir,'run_status.json'),struct('stage',stage,'records_completed',completed,'records_total',total,'elapsed_seconds',toc(timer),'workers',6));
    fprintf('%s T%d %s %d dB %d/%d %.1f seconds\n',stage,T,sc{1},snr,completed,total,toc(timer));
   end
  end
 end
end
writetable(struct2table([allrows{:}]),fullfile(outdir,[stage '_records.csv']));
phaseD_json(fullfile(outdir,[stage '_run_config.json']),struct('stage',stage,'phase_id',phase,'records',total,'workers',6,'chunk_size',10,'source_signature',sig,'elapsed_wall_seconds',toc(timer),'matlab_version',version,'Delta',10,'timing','Loaded six-process per-call wall times; no concurrent numerical experiment'));
delete(pool);diary off;
end
