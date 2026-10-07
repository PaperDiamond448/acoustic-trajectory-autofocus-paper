function export_phaseX3_lofar()
phaseD_setup();root='D:\论文集\phaseD\X3_real';F=jsondecode(fileread(fullfile(root,'X3_TESTSET_FREEZE.json')));
if ~isfield(F.roles,'b'),return;end
b=F.roles.b;P=[];times=[];freq=[];
for s=b.start_s:300:b.end_s-300
 Q=load(fullfile(root,'screen_inputs',sprintf('f%d_s%d.mat',b.tone_hz,s)),'y');lof=compute_lofar(Q.y,20,200,20,8192);mask=abs(lof.freq)<=.5;
 P=[P lof.P_db(mask,:)];times=[times;s+lof.tc(:)];freq=b.tone_hz+lof.freq(mask);
end
writematrix(P,fullfile(root,'role_b_LOFAR_power_db.csv'));writematrix(times,fullfile(root,'role_b_LOFAR_time_s.csv'));writematrix(freq,fullfile(root,'role_b_LOFAR_frequency_hz.csv'));
phaseD_json(fullfile(root,'role_b_LOFAR_config.json'),struct('tone_hz',b.tone_hz,'start_s',b.start_s,'end_s',b.end_s,'L',200,'D',20,'NFFT',8192,'frames_per_segment',291,'headerless_numeric_csv',true,'gap_note','Independent 300-s frames have 9-s gaps at segment boundaries; shown as gaps, not interpolated'));
end
