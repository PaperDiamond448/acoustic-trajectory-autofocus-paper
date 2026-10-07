function phaseX_save_real_worker(tone,start_s,T,fullcase,file,freeze_hash)
% Store the identical frozen numerical result locally; no complex parfor return.
if exist(file,'file')
 Q=load(file,'freeze_hash','S');assert(strcmp(Q.freeze_hash,freeze_hash));
 assert(Q.S.tone_hz==tone&&Q.S.start_s==start_s&&Q.S.duration_s==T);
 assert(numel(Q.S.rows)==3+5*fullcase);return;
end
S=phaseX3_one(tone,start_s,T,fullcase);
partial=[file '.partial.mat'];save(partial,'S','freeze_hash','-v7.3');movefile(partial,file);
end
