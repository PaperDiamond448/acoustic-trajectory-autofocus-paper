function run_phaseD_batch(stage,Delta,rerun)
% Only development stages are callable; confirmation has no entry point.
assert(any(strcmp(stage,{'D1','fixed','rerunA','rerunB','grid'})));
if nargin<2,Delta=NaN;end;if nargin<3,rerun='';end
root='D:\论文集';phaseD_setup();outdir=fullfile(root,'phaseD','D_dev');if ~exist(outdir,'dir'),mkdir(outdir);end
g=jsondecode(fileread(fullfile(root,'phaseD','G_gates','gates.json')));assert(g.all_pass,'All G1-G8 gates must pass.');
manifest=readtable(fullfile(root,'phaseD','code','SOURCE_MANIFEST_sha256.csv'),'TextType','string');
for k=1:height(manifest),assert(strcmp(phaseD_hash(char(manifest.source_file(k)),'SHA-256',true),manifest.sha256(k)),'Frozen source changed.');end
sig=phaseD_hash(fileread(fullfile(root,'phaseD','code','SOURCE_MANIFEST_sha256.csv')));
folder=fullfile(outdir,[stage '_chunks']);if ~exist(folder,'dir'),mkdir(folder);end
diary(fullfile(outdir,[stage '_matlab.log']));pool=gcp('nocreate');if isempty(pool),pool=parpool('Processes',6);end;assert(pool.NumWorkers==6);
completed=0;timer=tic;allrows={};
for sc={'S0','S2'}
    for snr=-20:-14
        for ch=1:6
            ids=(ch-1)*10+(1:10);file=fullfile(folder,sprintf('%s_%+03ddB_chunk_%03d.mat',sc{1},snr,ch));
            if exist(file,'file')
                C=load(file,'results','signature','delta','rerun_mode');
                assert(strcmp(C.signature,sig)&&isequaln(C.delta,Delta)&&strcmp(C.rerun_mode,rerun),'Resume signature mismatch.');results=C.results;
            else
                cells=cell(10,1);scene=sc{1};
                parfor k=1:10
                    if strcmp(stage,'D1'),cells{k}=phaseD_d1_one(scene,snr,ids(k));
                    else,cells{k}=phaseD_d2_one(scene,snr,ids(k),Delta,stage,rerun);end
                end
                results=[cells{:}];signature=sig;delta=Delta;rerun_mode=rerun;
                partial=[file '.partial.mat'];save(partial,'results','signature','delta','rerun_mode','-v7.3');movefile(partial,file);
            end
            assert(numel(results)==10&&isequal([results.record_id],ids));
            for k=1:10,allrows{end+1}=results(k).rows;end
            completed=completed+10;phaseD_json(fullfile(outdir,'run_status.json'),struct('stage',stage,'records_completed',completed,'records_total',840,'elapsed_seconds',toc(timer),'workers',6));
            fprintf('%s %s %d dB chunk %d/6; %d/840; %.1f seconds\n',stage,sc{1},snr,ch,completed,toc(timer));
        end
    end
end
T=struct2table([allrows{:}]);writetable(T,fullfile(outdir,[stage '_records.csv']));
phaseD_json(fullfile(outdir,[stage '_run_config.json']),struct('stage',stage,'phase_id',51,'records',840,'workers',6,'chunk_size',10,'source_signature',sig,'elapsed_wall_seconds',toc(timer),'matlab_version',version,'Delta',Delta,'rerun',rerun));
diary off;
end
