function run_e4a_formal_paired_batch(outdir, nworkers, chunkSize)
%RUN_E4A_FORMAL_PAIRED_BATCH Frozen 2,800-record E4a bounded/unbounded batch.
% The sole bounded/unbounded difference is the coefficient box u in [-1,1].
% All record-level results are saved in resumable chunks.
if nargin < 1 || isempty(outdir), outdir = fileparts(mfilename('fullpath')); end
if nargin < 2 || isempty(nworkers), nworkers = 6; end
if nargin < 3 || isempty(chunkSize), chunkSize = 10; end
assert(nworkers >= 1 && chunkSize >= 1);
if ~exist(outdir,'dir'), mkdir(outdir); end
chunkDir = fullfile(outdir,'chunks'); if ~exist(chunkDir,'dir'), mkdir(chunkDir); end
root = fileparts(fileparts(outdir));
pilot = fullfile(root,'phaseC','E4a_track_only_pilot_20260925');
snap = fullfile(pilot,'source_snapshot');
wk = fullfile(root,'研究工作台','MATLAB实验','mft_week4_module');
assert(exist(fullfile(pilot,'track_only_metrics.csv'),'file')==2, 'Missing frozen pilot table.');
assert(exist(fullfile(snap,'run_e4a_track_only.m'),'file')==2, 'Missing pilot source snapshot.');
assert(exist(fullfile(wk,'estimate_proposed.m'),'file')==2, 'Missing inherited BTA implementation.');
addpath(wk,'-begin'); addpath(snap,'-begin');
cfg=mft_config(); cfg.phase_id.track_only=33;
cfg.M.P.max_iter=[240 240 240]; cfg.M.P.max_fevals=[1000 1000 1000];
cfg.M.P.label='P240_E4a';
B=cfg.B; M=cfg.M; Pcfg=M.P;
assert(isequal(B.eval_s,[5 295]) && B.fs==20 && B.N==6000);
assert(isequal(M.B2.u_bounds,[-1 1]) && M.B2.radius==0.02 && M.B2.knot_ds==15);
assert(isequal(M.B2.band,[-2 2]) && isequal(Pcfg.h_stages_s,[20 60 290]));
assert(all(Pcfg.max_iter==240) && all(Pcfg.max_fevals==1000));
scenes={'S0','S2'}; snrs=-20:-14; ids=1:200;
jobs=make_jobs(cfg,'track_only',scenes,snrs,ids);
assert(numel(jobs)==2800 && numel(unique([jobs.seed]))==400);
pilotRows=readtable(fullfile(pilot,'track_only_metrics.csv'));
assert(height(pilotRows)==2800);
evalIdx=find((0:B.N-1)'/B.fs>=B.eval_s(1) & (0:B.N-1)'/B.fs<B.eval_s(2));
assert(numel(evalIdx)==5800);
ds=dir(fullfile(snap,'*.m'));
sourceFiles=fullfile({ds.folder},{ds.name});
sourceFiles=[sourceFiles,{fullfile(wk,'estimate_proposed.m'), ...
    fullfile(wk,'coherence_objective.m'),fullfile(wk,'make_blocks.m')}];
sourceHashes=cell(size(sourceFiles));
for k=1:numel(sourceFiles), sourceHashes{k}=sha256_file(sourceFiles{k}); end
sig=sha256_text(strjoin(sourceHashes,'|'));
runCfg=struct('protocol','E4a formal paired batch','status','in_progress', ...
    'created_utc',utc_now(),'source_root',root,'pilot_root',pilot,'output_root',outdir, ...
    'scenes',{scenes},'snr_db',snrs,'record_ids',ids,'records',numel(jobs), ...
    'unique_seeds',numel(unique([jobs.seed])),'phase_id',33, ...
    'seed_formula','20260915 + 1e6*33 + 1e4*scene_code + record_id; SNR excluded', ...
    'geometry_mode','eval','sample_snr_definition','20 Hz synthetic complex-baseband sample SNR', ...
    'eval_s',B.eval_s,'eval_samples',numel(evalIdx),'fs',B.fs,'N',B.N, ...
    'band_hz',M.B2.band,'radius_hz',M.B2.radius,'knots_s',(0:M.B2.knot_ds:300), ...
    'stages_s',Pcfg.h_stages_s,'max_iter_per_stage',Pcfg.max_iter, ...
    'max_fevals_per_stage',Pcfg.max_fevals,'tol_x',Pcfg.tol_x, ...
    'tol_opt',Pcfg.tol_opt,'lambda_C',Pcfg.lambda_C,'optimizer','fmincon SQP; existing analytic gradient', ...
    'methods',{{'SMR','BTA_bounded','BTA_unbounded'}}, ...
    'unbounded_difference','Only fam.lb=-Inf and fam.ub=Inf; preserve fam.Aineq/fam.bineq and radius-scaled basis.', ...
    'chunk_size',chunkSize,'workers',nworkers,'bootstrap_replicates',2000, ...
    'bootstrap_seed',20260925,'code_signature_sha256',sig,'source_files',{sourceFiles}, ...
    'source_sha256',{sourceHashes},'matlab_version',version,'started_utc',utc_now());
cfgPath=fullfile(outdir,'run_config.json');
if exist(cfgPath,'file')
    old=jsondecode(fileread(cfgPath));
    assert(strcmp(old.code_signature_sha256,sig) && old.phase_id==33 && ...
        old.records==2800 && isequal(old.max_iter_per_stage(:),[240;240;240]), ...
        'Existing output config does not match this frozen run; refusing resume.');
else
    write_json(cfgPath,runCfg);
end
manifest=table(string(sourceFiles(:)),string(sourceHashes(:)), ...
    'VariableNames',{'source_file','sha256'});
writetable(manifest,fullfile(outdir,'source_manifest_sha256.csv'));
diaryFile=fullfile(outdir,'matlab_run.log'); diary(diaryFile);
fprintf('E4a formal paired batch: 2800 records, 14 cells, chunk=%d, workers=%d\n',chunkSize,nworkers);
fprintf('Budget per BTA stage: 240 iterations / 1000 function evaluations. Signature %s\n',sig);
pool=gcp('nocreate');
if isempty(pool), pool=parpool('Processes',nworkers); end
assert(pool.NumWorkers==nworkers,'Existing pool worker count differs from frozen configuration.');
doneRecords=0; totalChunks=numel(scenes)*numel(snrs)*ceil(200/chunkSize);
completedChunks=0; totalTimer=tic;
for si=1:numel(scenes)
    for qi=1:numel(snrs)
        scene=scenes{si}; snr=snrs(qi);
        tag=sprintf('%s_%+03ddB',scene,snr);
        cellJobs=jobs(strcmp({jobs.scene},scene) & [jobs.snr_db]==snr);
        expectedSeeds=[cellJobs.seed]';
        pilotCell=load(fullfile(pilot,'cells',[tag '.mat']), ...
            'rows','gtrue','gvit','gsmr','uSMR','t','cell_seeds');
        assert(numel(pilotCell.cell_seeds)==200 && isequal(pilotCell.cell_seeds(:),expectedSeeds), ...
            'Frozen pilot seeds differ in %s.',tag);
        nch=ceil(numel(cellJobs)/chunkSize);
        for ch=1:nch
            ix=(ch-1)*chunkSize+1:min(ch*chunkSize,numel(cellJobs));
            outFile=fullfile(chunkDir,sprintf('%s_chunk_%03d.mat',tag,ch));
            if exist(outFile,'file')
                C=load(outFile,'records','chunk_signature','cell_tag','chunk_no');
                if strcmp(C.chunk_signature,sig) && strcmp(C.cell_tag,tag) && C.chunk_no==ch && ...
                        numel(C.records)==numel(ix) && all([C.records.record_id]==[cellJobs(ix).record_id])
                    doneRecords=doneRecords+numel(ix); completedChunks=completedChunks+1;
                    fprintf('resume %s chunk %d/%d (%d records); total %d/2800\n',tag,ch,nch,numel(ix),doneRecords);
                    continue
                end
                error('Mismatched existing chunk: %s',outFile);
            end
            ticChunk=tic; part=cellJobs(ix); resultCells=cell(numel(part),1); coeffS=zeros(21,numel(part));
            coeffB=zeros(21,numel(part)); coeffU=zeros(21,numel(part));
            parfor q=1:numel(part)
                [resultCells{q},coeffS(:,q),coeffB(:,q),coeffU(:,q)]= ...
                    process_one(part(q),pilotRows,pilotCell,cfg,B,M,Pcfg,evalIdx);
            end
            records=[resultCells{:}]; cell_tag=tag; chunk_no=ch; chunk_ids=[part.record_id]; %#ok<NASGU>
            chunk_signature=sig; chunk_seconds=toc(ticChunk); %#ok<NASGU>
            tmp=[outFile '.partial'];
            save(tmp,'records','coeffS','coeffB','coeffU','cell_tag','chunk_no', ...
                'chunk_ids','chunk_signature','chunk_seconds','-v7.3');
            movefile(tmp,outFile,'f');
            doneRecords=doneRecords+numel(part); completedChunks=completedChunks+1;
            status=struct('status','in_progress','updated_utc',utc_now(), ...
                'records_completed',doneRecords,'records_total',2800, ...
                'chunks_completed',completedChunks,'chunks_total',totalChunks, ...
                'last_cell',tag,'last_chunk',ch,'last_chunk_seconds',chunk_seconds, ...
                'elapsed_seconds',toc(totalTimer));
            write_json(fullfile(outdir,'run_status.json'),status);
            fprintf('saved %s chunk %d/%d: %d records, %.1f s; total %d/2800 (%.1f%%)\n', ...
                tag,ch,nch,numel(part),chunk_seconds,doneRecords,100*doneRecords/2800);
        end
    end
end
assert(doneRecords==2800,'Completed record count is %d, expected 2800.',doneRecords);
diary off;
analyze_e4a_formal_batch(outdir);
runCfg.status='complete'; runCfg.completed_utc=utc_now();
runCfg.elapsed_seconds=toc(totalTimer); runCfg.completed_records=doneRecords;
write_json(cfgPath,runCfg);
status=struct('status','complete','updated_utc',utc_now(), ...
    'records_completed',2800,'records_total',2800,'chunks_completed',completedChunks, ...
    'chunks_total',totalChunks,'elapsed_seconds',toc(totalTimer));
write_json(fullfile(outdir,'run_status.json'),status);
fprintf('E4a complete: 2,800 paired records. Analysis/report generated.\n');
end

function [R,uS,uB,uU]=process_one(j,pilotRows,pilotCell,cfg,B,M,Pcfg,evalIdx)
rec=simulate_baseband(cfg,j.scene,j.snr_db,j.seed,'eval');
ih=input_hash(rec.y);
pr=pilotRows(strcmp(string(pilotRows.scene),j.scene) & pilotRows.snr_db==j.snr_db & ...
    pilotRows.record_id==j.record_id,:);
assert(height(pr)==1 && strcmp(char(pr.input_hash),ih), ...
    'Input hash mismatch: %s %d dB record %d.',j.scene,j.snr_db,j.record_id);
ci=find(pilotCell.rows.record_id==j.record_id,1);
assert(~isempty(ci));
assert(max(abs(double(pilotCell.gtrue(:,ci))-rec.truth.gtrue))<2e-6, 'Pilot truth track mismatch.');
fcfg=struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine, ...
    'band',B.band,'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
t0=tic; fe=common_frontend(rec.y,rec.t,fcfg); tFe=toc(t0);
t0=tic; oVit=estimate_b1(fe,M.B1); tVit=toc(t0);
assert(max(abs(double(pilotCell.gvit(:,ci))-oVit.g))<2e-6, 'Pilot VIT track mismatch.');
t0=tic; fam=build_family(rec.t,fe.tc,oVit.g,M.B2); tFam=toc(t0);
t0=tic; oSMR=estimate_b2(fe,fam,M.B2); tSmr=toc(t0);
assert(max(abs(double(pilotCell.gsmr(:,ci))-oSMR.g))<2e-6, 'Pilot SMR track mismatch.');
assert(max(abs(double(pilotCell.uSMR(:,ci))-oSMR.u))<2e-6, 'Pilot SMR coefficients mismatch.');
famU=fam; famU.lb=-inf(fam.P,1); famU.ub=inf(fam.P,1);
% Confirm the ablation changes only box limits; global inequalities remain exact.
assert(isequal(fam.Aineq,famU.Aineq) && isequal(fam.bineq,famU.bineq) && ...
    isequal(fam.Bt,famU.Bt) && isequal(fam.gA,famU.gA));
t0=tic; outB=estimate_proposed(rec.y,fe,fam,oSMR.u,evalIdx,Pcfg); tB=toc(t0);
t0=tic; outU=estimate_proposed(rec.y,fe,famU,oSMR.u,evalIdx,Pcfg); tU=toc(t0);
assert(numel(outB.exitflags)==3 && numel(outU.exitflags)==3);
assert(abs(outB.J_B2-outU.J_B2)<1e-11,'SMR start objective differs between variants.');
assert(all(abs(outB.u)<=1+1e-7),'Bounded solution violates coefficient box.');
mS=measure(rec,oSMR.g,evalIdx,B); mB=measure(rec,outB.g,evalIdx,B); mU=measure(rec,outU.g,evalIdx,B);
baseChain=tFe+tVit+tFam+tSmr;
R=struct('record_id',j.record_id,'scene',string(j.scene),'snr_db',j.snr_db,'seed',j.seed, ...
    'input_hash',string(ih),'noise_hat',fe.noise_hat,'geo_f0_hz',rec.truth.geo.f0, ...
    'geo_v_mps',rec.truth.geo.v,'geo_t_cpa_rx_s',rec.truth.geo.t_cpa_rx, ...
    'vit_pout',pr.vit_pout,'vit_out_longest_s',pr.vit_out_longest_s, ...
    'vit_rmse_hz',pr.vit_rmse_hz,'proj_bounded_rmse_hz',pr.proj_bounded_rmse_hz, ...
    'proj_unbounded_rmse_hz',pr.proj_unbounded_rmse_hz, ...
    'oracle_projection_gap_hz',pr.delta_proj_rmse_hz, ...
    'J290_smr',outB.J_B2,'J290_bounded',outB.J_best,'J290_unbounded',outU.J_best, ...
    'selected_bounded',string(outB.selected),'selected_unbounded',string(outU.selected), ...
    'fallback_bounded',outB.fallback,'fallback_unbounded',outU.fallback, ...
    'hard_fail_bounded',outB.hard_fail,'hard_fail_unbounded',outU.hard_fail, ...
    'peak_power_smr',mS.peak_power,'peak_power_bounded',mB.peak_power,'peak_power_unbounded',mU.peak_power, ...
    'peak_db_smr',mS.peak_db,'peak_db_bounded',mB.peak_db,'peak_db_unbounded',mU.peak_db, ...
    'peak_frequency_smr_hz',mS.peak_frequency,'peak_frequency_bounded_hz',mB.peak_frequency, ...
    'peak_frequency_unbounded_hz',mU.peak_frequency, ...
    'prominence_smr_db',mS.prom_db,'prominence_bounded_db',mB.prom_db,'prominence_unbounded_db',mU.prom_db, ...
    'width_smr_hz',mS.width,'width_bounded_hz',mB.width,'width_unbounded_hz',mU.width, ...
    'eta_oracle',mS.eta_oracle,'eta_smr',mS.eta,'eta_bounded',mB.eta,'eta_unbounded',mU.eta, ...
    'eta_loss_smr_db',mS.eta_loss_db,'eta_loss_bounded_db',mB.eta_loss_db,'eta_loss_unbounded_db',mU.eta_loss_db, ...
    'track_rmse_smr_hz',mS.rmse,'track_rmse_bounded_hz',mB.rmse,'track_rmse_unbounded_hz',mU.rmse, ...
    'pout_smr',mS.pout,'pout_bounded',mB.pout,'pout_unbounded',mU.pout, ...
    'max_error_smr_hz',mS.maxabs,'max_error_bounded_hz',mB.maxabs,'max_error_unbounded_hz',mU.maxabs, ...
    'longest_out_smr_s',mS.longest,'longest_out_bounded_s',mB.longest,'longest_out_unbounded_s',mU.longest, ...
    'umax_smr',max(abs(oSMR.u)),'umax_bounded',max(abs(outB.u)),'umax_unbounded',max(abs(outU.u)), ...
    'box_active_smr',sum(abs(oSMR.u)>=1-1e-6),'box_active_bounded',sum(abs(outB.u)>=1-1e-6), ...
    'box_active_unbounded',sum(abs(outU.u)>=1-1e-6), ...
    'band_violation_smr_hz',band_violation(fam,oSMR.u,M.B2.band), ...
    'band_violation_bounded_hz',band_violation(fam,outB.u,M.B2.band), ...
    'band_violation_unbounded_hz',band_violation(famU,outU.u,M.B2.band), ...
    't_frontend_s',tFe,'t_vit_s',tVit,'t_family_s',tFam,'t_smr_s',tSmr, ...
    't_bounded_optimizer_s',tB,'t_unbounded_optimizer_s',tU, ...
    't_chain_smr_s',baseChain,'t_chain_bounded_s',baseChain+tB,'t_chain_unbounded_s',baseChain+tU, ...
    'b_fallback',outB.fallback,'u_fallback',outU.fallback, ...
    'b_messages',string(strjoin(outB.messages,' || ')), ...
    'u_messages',string(strjoin(outU.messages,' || ')));
for s=1:3
    R.(sprintf('b_exitflag_s%d',s))=outB.exitflags(s); R.(sprintf('u_exitflag_s%d',s))=outU.exitflags(s);
    R.(sprintf('b_iterations_s%d',s))=outB.iters(s); R.(sprintf('u_iterations_s%d',s))=outU.iters(s);
    R.(sprintf('b_fevals_s%d',s))=outB.fevals(s); R.(sprintf('u_fevals_s%d',s))=outU.fevals(s);
    R.(sprintf('b_firstorderopt_s%d',s))=outB.firstorderopt(s); R.(sprintf('u_firstorderopt_s%d',s))=outU.firstorderopt(s);
    R.(sprintf('b_stage_seconds_s%d',s))=outB.stage_seconds(s); R.(sprintf('u_stage_seconds_s%d',s))=outU.stage_seconds(s);
    R.(sprintf('b_iter_cap_s%d',s))=isfinite(outB.iters(s)) && outB.iters(s)>=Pcfg.max_iter(s)-1e-9;
    R.(sprintf('u_iter_cap_s%d',s))=isfinite(outU.iters(s)) && outU.iters(s)>=Pcfg.max_iter(s)-1e-9;
    R.(sprintf('b_feval_cap_s%d',s))=isfinite(outB.fevals(s)) && outB.fevals(s)>=Pcfg.max_fevals(s)-1e-9;
    R.(sprintf('u_feval_cap_s%d',s))=isfinite(outU.fevals(s)) && outU.fevals(s)>=Pcfg.max_fevals(s)-1e-9;
    R.(sprintf('b_stage_feasible_s%d',s))=isfinite(outB.stage_J290(s));
    R.(sprintf('u_stage_feasible_s%d',s))=isfinite(outU.stage_J290(s));
    R.(sprintf('b_stage_J290_s%d',s))=outB.stage_J290(s); R.(sprintf('u_stage_J290_s%d',s))=outU.stage_J290(s);
end
uS=oSMR.u(:); uB=outB.u(:); uU=outU.u(:);
end

function m=measure(rec,g,idx,B)
t=rec.t(:); phi=2*pi*cumtrapz(t,g(:)); nfft=2^nextpow2(B.fft_pad*numel(idx));
f=(-nfft/2:nfft/2-1)'*B.fs/nfft; P=fftshift(abs(fft(rec.y(idx).*exp(-1j*phi(idx)),nfft)).^2);
sel=abs(f)<=B.band(2); ps=P(sel); fb=f(sel); [pk,ip]=max(ps);
m.peak_power=pk; m.peak_db=10*log10(max(pk,realmin)); m.peak_frequency=fb(ip);
side=(f>=B.noise_bands(1,1)&f<=B.noise_bands(1,2)) | (f>=B.noise_bands(2,1)&f<=B.noise_bands(2,2));
m.prom_db=10*log10(max(pk,realmin)/max(median(P(side)),realmin));
db=10*log10(max(ps,realmin)); th=db(ip)-10*log10(2); il=ip; ir=ip;
while il>1 && db(il-1)>=th, il=il-1; end
while ir<numel(db) && db(ir+1)>=th, ir=ir+1; end
if il==1 || ir==numel(db), m.width=NaN; else
    fl=crossing(fb(il-1),db(il-1),fb(il),db(il),th);
    fr=crossing(fb(ir),db(ir),fb(ir+1),db(ir+1),th); m.width=fr-fl;
end
den=max(sum(abs(rec.truth.s_target(idx)))^2,realmin);
st=rec.truth.s_target(idx).*exp(-1j*phi(idx)); Pt=fftshift(abs(fft(st,nfft)).^2);
m.eta=max(Pt(sel))/den; phiT=2*pi*cumtrapz(t,rec.truth.gtrue(:));
stT=rec.truth.s_target(idx).*exp(-1j*phiT(idx)); Po=fftshift(abs(fft(stT,nfft)).^2);
m.eta_oracle=max(Po(sel))/den; m.eta_loss_db=-10*log10(max(m.eta,realmin)/max(m.eta_oracle,realmin));
e=g(idx)-rec.truth.gtrue(idx); m.rmse=sqrt(mean(e.^2)); a=abs(e); m.pout=mean(a>0.02); m.maxabs=max(a);
mask=a>0.02; d=diff([false;mask(:);false]); st0=find(d==1); en=find(d==-1)-1;
if isempty(st0), m.longest=0; else, m.longest=max(en-st0+1)/B.fs; end
end

function x=band_violation(fam,u,band)
g=fam.gAchk+fam.r*fam.Bchk*u; x=max([0;g-band(2);band(1)-g]);
end
function x=crossing(f1,d1,f2,d2,th)
if d2==d1, x=(f1+f2)/2; else, x=f1+(th-d1)*(f2-f1)/(d2-d1); end
end
function h=input_hash(y)
b=typecast([real(y(:));imag(y(:))],'uint8'); md=java.security.MessageDigest.getInstance('MD5'); md.update(b);
h=lower(reshape(dec2hex(typecast(md.digest(),'uint8')).',1,[]));
end
function h=sha256_file(path)
fid=fopen(path,'rb'); assert(fid>0,'Cannot read source %s.',path); c=onCleanup(@()fclose(fid)); b=fread(fid,inf,'*uint8'); %#ok<NASGU>
md=java.security.MessageDigest.getInstance('SHA-256'); md.update(b); h=lower(reshape(dec2hex(typecast(md.digest(),'uint8')).',1,[]));
end
function h=sha256_text(s)
md=java.security.MessageDigest.getInstance('SHA-256'); md.update(uint8(s)); h=lower(reshape(dec2hex(typecast(md.digest(),'uint8')).',1,[]));
end
function write_json(path,x)
fid=fopen(path,'w'); assert(fid>0,'Cannot write %s.',path); c=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s',jsonencode(x,'PrettyPrint',true));
end
function s=utc_now()
s=char(datetime('now','TimeZone','UTC','Format','yyyy-MM-dd''T''HH:mm:ss''Z'''));
end
