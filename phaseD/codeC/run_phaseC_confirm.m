function run_phaseC_confirm()
root='D:\论文集\phaseD';phaseD_setup();addpath(fullfile(root,'codeC'),'-begin');
outdir=fullfile(root,'C_confirm');
g=jsondecode(fileread(fullfile(root,'G_gates','gates.json')));assert(g.all_pass);
F=jsondecode(fileread(fullfile(root,'D_dev','FROZEN_METHOD.json')));
assert(strcmp(F.method,'ADA_local_c04_t30_A') && F.Delta_s==10 && F.P==31);
assert(strcmp(F.F_star,'F04') && F.ADA.cap_hz==.04 && F.ADA.tau_s==30 && strcmp(F.ADA.rerun,'A'));
assert(strcmp(phaseD_hash(fullfile(root,'D_dev','FROZEN_METHOD.json'),'SHA-256',true),'ff63f32c38fc17e99620faa074025c337df247bf823be4fa4b40e74860c0a89f'));
manifest=readtable(fullfile(root,'codeC','SOURCE_MANIFEST_C_sha256.csv'),'TextType','string');
for k=1:height(manifest),assert(strcmp(phaseD_hash(char(manifest.source_file(k)),'SHA-256',true),manifest.sha256(k)),'Confirmation source changed.');end
sig=phaseD_hash(fullfile(root,'codeC','SOURCE_MANIFEST_C_sha256.csv'),'SHA-256',true);
folder=fullfile(outdir,'chunks');if ~exist(folder,'dir'),mkdir(folder);end
diary(fullfile(outdir,'C_matlab.log'));pool=gcp('nocreate');if isempty(pool),pool=parpool('Processes',6);end;assert(pool.NumWorkers==6);
completed=0;timer=tic;allrows={};
for sc={'S0','S2'}
    for snr=-20:-14
        for ch=1:20
            ids=(ch-1)*10+(1:10);file=fullfile(folder,sprintf('%s_%+03ddB_chunk_%03d.mat',sc{1},snr,ch));
            if exist(file,'file')
                C=load(file,'results','signature','phase_id');assert(strcmp(C.signature,sig) && C.phase_id==52,'Resume signature mismatch.');results=C.results;
            else
                cells=cell(10,1);scene=sc{1};
                parfor k=1:10,cells{k}=phaseC_one(scene,snr,ids(k),F);end
                results=[cells{:}];signature=sig;phase_id=52;
                partial=[file '.partial.mat'];save(partial,'results','signature','phase_id','-v7.3');movefile(partial,file);
            end
            assert(numel(results)==10 && isequal([results.record_id],ids));
            for k=1:10,allrows{end+1}=results(k).rows;end
            completed=completed+10;phaseD_json(fullfile(outdir,'run_status.json'),struct('stage','C','records_completed',completed,'records_total',2800,'elapsed_seconds',toc(timer),'workers',6));
            fprintf('C %s %d dB chunk %d/20; %d/2800; %.1f seconds\n',sc{1},snr,ch,completed,toc(timer));
        end
    end
end
T=struct2table([allrows{:}]);writetable(T,fullfile(outdir,'C_records.csv'));
phaseD_json(fullfile(outdir,'C_run_config.json'),struct('stage','C','phase_id',52,'records',2800,'methods',{{'SMR','F02','F04','UNB',F.method}},'workers',6,'chunk_size',10,'source_signature',sig,'elapsed_wall_seconds',toc(timer),'matlab_version',version,'Delta',F.Delta_s,'rerun',F.ADA.rerun));
diary off;
end
