% Read saved confirmation trajectories; recreate only their frozen target truth.
addpath('D:\论文集\phaseD\code');
[cfg,B,M]=phaseD_setup();
root='D:\论文集\phaseD\C_confirm';
dst='D:\论文集\研究工作台\第2-4章核对_20261011';
C=readtable(fullfile(root,'C_records.csv'));
L=C(strcmp(C.scene,'S0') & C.snr_db==-17 & strcmp(C.method,'SMR'),:);
A=C(strcmp(C.scene,'S0') & C.snr_db==-17 & strcmp(C.method,'ADA_local_c04_t30_A'),:);
ids=L.record_id(L.max_error_hz<.02);
ids=intersect(ids,A.record_id(A.eta>.85 & A.triggered==0));
samples=cell(numel(ids),1);
for k=1:numel(ids)
 rid=ids(k);p=fullfile(root,'chunks',sprintf('S0_-17dB_chunk_%03d.mat',ceil(rid/10)));
 saved=load(p,'results');S=saved.results([saved.results.record_id]==rid);
 seed=cfg.master_seed+52e6+1e4*cfg.scene_code.S0+rid;
 rec=simulate_baseband_T(cfg,'S0',-17,seed,'eval',300);
 assert(strcmp(phaseD_hash(rec.y,'MD5'),S.input_hash));
 gi=S.details{1}.smr.g(:);go=S.details{5}.ada.out.g(:);
 assert(max(abs(gi-rec.truth.gtrue))<.02 || L.max_error_hz(L.record_id==rid)<.02);
 samples{k}=struct('record_id',rid,'seed',seed,'input_hash',S.input_hash, ...
 't',rec.t(:),'truth',rec.truth.gtrue(:),'target',rec.truth.s_target(:), ...
 'input_g',gi,'output_g',go,'source_file',p, ...
 'eta_in_saved',L.eta(L.record_id==rid),'eta_out_saved',A.eta(A.record_id==rid));
end
save(fullfile(dst,'confirm_candidates.mat'),'samples','-v7');
fprintf('Read-only export complete: %d candidates, no optimizer called.\n',numel(ids));
