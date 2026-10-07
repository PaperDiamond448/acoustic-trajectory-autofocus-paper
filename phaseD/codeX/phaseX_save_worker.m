function phaseX_save_worker(stage,scene,snr,rid,T,file,sig,phase)
if exist(file,'file'),C=load(file,'signature','phase_id');assert(strcmp(C.signature,sig)&&C.phase_id==phase);return;end
if strcmp(stage,'X1'),S=phaseX1_one(scene,snr,rid,T);else,S=phaseX2_one(scene,snr,rid);end
signature=sig;phase_id=phase;partial=[file '.partial.mat'];save(partial,'S','signature','phase_id','-v7.3');movefile(partial,file);
end
