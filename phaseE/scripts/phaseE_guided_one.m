function S=phaseE_guided_one(tone,start_s)
% New outputs only. Numerical estimation uses the frozen Phase D functions.
root='D:\论文集'; dest=fullfile(root,'phaseE','E4_guided_real');T=300;
[F,~,B,M]=phaseX_settings(T,true);
original=fullfile(root,'phaseD','X3_real');
q=load(fullfile(original,'screen_inputs',sprintf('f%d_s%d.mat',tone,start_s)),'y','extract');
y=q.y;t=(0:numel(y)-1)'/20;assert(numel(t)==6000);
hash=phaseD_hash(y,'MD5');
old=readtable(fullfile(original,'X3_cases.csv'),'TextType','string');
old=old(old.tone_hz==tone & old.segment_start_s==start_s & old.method=="SMR",:);
assert(height(old)==1 && strcmp(hash,char(old.input_hash)),'PhaseE:InputMismatch','Guided input differs from archived X3.');
G=readtable(fullfile(dest,'anchors',sprintf('f%d_s%d_guided.csv',tone,start_s)));
assert(height(G)==numel(t) && max(abs(G.time_s-(start_s+t)))<1e-8);
[fe,~,idx,times]=phaseX_front(y,t,B,M);
ref=readtable(fullfile(root,'phaseA','tables','A4_groundtruth.csv'));
gps=tone*interp1(ref.t_s,ref.f_gps_100,start_s+t,'linear',NaN)/100;
[period,f,p0]=phaseX3_metrics(y,t,zeros(size(t)),tone,gps,idx);
base=readtable(fullfile(original,'tracks',sprintf('f%d_s%d_T300.csv',tone,start_s)));
[baselineL,~,pL]=phaseX3_metrics(y,t,base.SMR-tone,tone,gps,idx);
[baselineA,~,pA]=phaseX3_metrics(y,t,base.VS_FM-tone,tone,gps,idx);
deltaOld=abs(10*log10(baselineL.peak_power/period.peak_power)-old.peak_relative_periodogram_db);
assert(deltaOld<1e-9,'PhaseE:MetricMismatch','X3 LPS metric does not reproduce.');
names={'G_ADA','G_UNB','G94_ADA'};rows=cell(1,3);outs=cell(1,3);gs=cell(1,3);fams=cell(1,3);
spec=zeros(numel(f),3);
for k=1:3
 if k==3,anchor=G.guided94_abs_hz-tone;else,anchor=G.guided_med_abs_hz-tone;end
 fam=build_family_T(t,fe.tc,anchor,M.B2,10,T,1);u0=zeros(fam.P,1);
 if k==2
  fam.lb=-Inf(fam.P,1);fam.ub=Inf(fam.P,1);timer=tic;
  a=estimate_proposed_T(y,fe,fam,u0,idx,M.P);seconds=toc(timer);o=a;
  triggered=false;rounds=0;dwell=NaN;round0=seconds;expansion=0;
 else
  a=phaseD_ada(y,fe,fam,u0,idx,M.P,t,30,.04,'local','A');o=a.out;
  seconds=a.seconds;triggered=a.triggered;rounds=a.rounds;dwell=a.initial_dwell_s;
  round0=a.logs{1}.seconds;expansion=seconds-round0;
 end
 [met,~,p]=phaseX3_metrics(y,t,o.g,tone,gps,idx);spec(:,k)=p;
 zero=abs(f-tone)<=.01;[zpk,ii]=max(p(zero));fz=f(zero);
 zl=max(pL(zero));za=max(pA(zero));
 cap=any(o.iters(:)>=o.max_iter(:)|o.fevals(:)>=o.max_fevals(:));
 rows{k}=struct('tone_hz',tone,'segment_start_s',start_s,'segment_end_s',start_s+T, ...
  'duration_s',T,'input_hash',string(hash),'method',string(names{k}), ...
  'frozen_method',string(F.method),'Delta_s',10,'P',fam.P, ...
  'peak_power',met.peak_power,'periodogram_peak_power',period.peak_power, ...
  'peak_relative_periodogram_db',10*log10(met.peak_power/period.peak_power), ...
  'peak_frequency_hz',met.peak_frequency_hz,'prominence_db',met.prominence_db, ...
  'width_3db_hz',met.width_3db_hz,'zero_peak_power',zpk,'zero_peak_frequency_hz',fz(ii), ...
  'zero_peak_relative_periodogram_db',10*log10(zpk/period.peak_power), ...
  'gain_peak_vs_LPS_db',10*log10(met.peak_power/baselineL.peak_power), ...
  'gain_peak_vs_VS_FM_db',10*log10(met.peak_power/baselineA.peak_power), ...
  'gain_zero_peak_vs_LPS_db',10*log10(zpk/zl), ...
  'gain_zero_peak_vs_VS_FM_db',10*log10(zpk/za), ...
  'runtime_s',seconds,'t_round0_s',round0,'t_expansion_s',expansion, ...
  't_frontend_s',times.frontend,'triggered',triggered,'expansion_rounds',rounds, ...
  'initial_dwell_s',dwell,'J',o.J_best,'J_start',o.J_B2,'hard_fail',o.hard_fail, ...
  'budget_cap',cap,'exitflags',string(jsonencode(o.exitflags)), ...
  'iterations',string(jsonencode(o.iters)),'fevals',string(jsonencode(o.fevals)));
 gs{k}=o.g;outs{k}=a;fams{k}=fam;
 fprintf('GUIDED f%d s%d %s: peak=%+.4f dB vs LPS, zero=%+.4f dB vs LPS\n',tone,start_s,names{k},rows{k}.gain_peak_vs_LPS_db,rows{k}.gain_zero_peak_vs_LPS_db);
end
tag=sprintf('f%d_s%d_T300',tone,start_s);use=abs(f-tone)<=1.5;
writetable(array2table([f(use) p0(use) pL(use) pA(use) spec(use,:)], ...
 'VariableNames',[{'frequency_Hz','Periodogram','LPS','VS_FM'} names]),fullfile(dest,'spectra',[tag '.csv']));
writetable(array2table([start_s+t G.guided_med_abs_hz G.guided94_abs_hz cell2mat(cellfun(@(x)tone+x(:),gs,'UniformOutput',false))], ...
 'VariableNames',[{'time_s','guided_med_abs_hz','guided94_abs_hz'} names]),fullfile(dest,'tracks',[tag '.csv']));
S=struct('rows',[rows{:}],'input_hash',hash,'tone_hz',tone,'start_s',start_s,'duration_s',T, ...
 'outs',{outs},'families',{fams},'tracks',{gs},'extract',q.extract,'baseline_metric_abs_diff',deltaOld);
save(fullfile(dest,'records',[tag '.mat']),'S','-v7');
writetable(struct2table(S.rows),fullfile(dest,'records',[tag '.csv']));
end
