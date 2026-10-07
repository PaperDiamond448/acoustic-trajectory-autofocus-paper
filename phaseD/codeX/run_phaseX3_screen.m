function run_phaseX3_screen()
root='D:\论文集\phaseD';phaseD_setup();addpath(fullfile(root,'codeX'),'-begin');phaseX_verify_sources();
outdir=fullfile(root,'X3_real');R=real_config();assert(exist(R.file,'file')==2);
assert(strcmp(phaseD_hash(R.file,'SHA-256',true),R.file_sha256));
tones=[49 64 79 94 112 130;52 67 82 97 115 133;55 70 85 100 118 136;58 73 88 103 121 139;61 76 91 106 124 142];
freqs=[reshape(tones',[],1);109;127;145];rows=cell(330,1);k=0;timer=tic;
folder=fullfile(outdir,'screen_inputs');if ~exist(folder,'dir'),mkdir(folder);end
for q=1:33
 f=freqs(q);if q<=30,set=ceil(q/6);if set==1,group='strong';else,group='weak';end;levels=[158 132 128 124 120];level=levels(set);inferred=set==5;else,set=0;group='shallow';level=NaN;inferred=false;end
 for s=0:300:2700
  lo=10*(s>0);hi=10*(s+300<3000);
  [y,extract]=phaseA_load_baseband(R.file,9,f,20,10,R.fs_raw,R.n_raw,s,300,lo,hi);
  lof=compute_lofar(y,20,200,20,8192);core=abs(lof.freq)<=.5;ann=abs(lof.freq)>=1 & abs(lof.freq)<=2;
  pc=lof.P_db(core,:);[~,imax]=max(pc,[],1);fc=lof.freq(core);ridge=fc(imax);center=median(ridge);
  excess=max(pc(:))-median(reshape(lof.P_db(ann,:),[],1));continuity=mean(abs(ridge-center)<=.2);
  k=k+1;rows{k}=struct('tone_hz',f,'segment_start_s',s,'segment_end_s',s+300,'group',string(group),'set_number',set,'source_level_db',level,'source_level_inferred',inferred,'peak_excess_dB',excess,'ridge_continuity',continuity,'passed',excess>10&&continuity>.6,'competing_ridge',f==103&&s==900,'frames',numel(lof.tc),'input_hash',string(phaseD_hash(y,'MD5')),'guard_lo_s',lo,'guard_hi_s',hi);
  % Store all screened inputs, even rejected ones, before any module is run.
  save(fullfile(folder,sprintf('f%d_s%d.mat',f,s)),'y','extract','-v7.3');
 end
 fprintf('X3 screening %d/33 tones, %.1f seconds\n',q,toc(timer));
end
tab=struct2table([rows{:}]);writetable(tab,fullfile(outdir,'X3_visibility.csv'));
writetable(tab(tab.passed,:),fullfile(outdir,'X3_FROZEN_TESTSET.csv'));
old=readtable('D:\论文集\phaseA\tables\A3_visibility.csv');sel=ismember(tab.tone_hz,[94 97 100 103 106 109]);cmp=tab(sel,:);
for j=1:height(cmp),i=find(old.tone_hz==cmp.tone_hz(j)&old.segment_start_s==cmp.segment_start_s(j));assert(isscalar(i));cmp.old_peak_excess_dB(j)=old.peak_excess_dB(i);cmp.old_ridge_continuity(j)=old.ridge_continuity(i);cmp.old_passed(j)=old.peak_excess_dB(i)>10&&old.ridge_continuity(i)>.6;end
cmp.pass_flipped=cmp.passed~=cmp.old_passed;writetable(cmp,fullfile(outdir,'X3_A3_comparison.csv'));
phaseD_json(fullfile(outdir,'SCREEN_COMPLETE.json'),struct('status','ALL_330_SCREENED_BEFORE_ANY_REAL_MODULE','candidates',330,'passed',nnz(tab.passed),'raw_sha256',R.file_sha256,'visibility_sha256',phaseD_hash(fullfile(outdir,'X3_visibility.csv'),'SHA-256',true),'testset_sha256',phaseD_hash(fullfile(outdir,'X3_FROZEN_TESTSET.csv'),'SHA-256',true),'elapsed_seconds',toc(timer),'frames','291 wholly supported LOFAR frames per independently extracted 300-s interval; A3 used a continuous LOFAR, differences and flips retained'));
end
