function run_phaseX3_continuous_screen()
% Correct the pre-module screening interface to exactly the original A3 frame support.
phaseD_setup();root='D:\论文集\phaseD\X3_real';old=readtable(fullfile(root,'X3_visibility.csv'),'TextType','string');rows=cell(330,1);k=0;timer=tic;
for tone=unique(old.tone_hz,'stable')'
 y=complex(zeros(60000,1));
 for s=0:300:2700,Q=load(fullfile(root,'screen_inputs',sprintf('f%d_s%d.mat',tone,s)),'y');y(s*20+(1:6000))=Q.y;end
 lof=compute_lofar(y,20,200,20,8192);core=abs(lof.freq)<=.5;ann=abs(lof.freq)>=1&abs(lof.freq)<=2;pc=lof.P_db(core,:);[~,imax]=max(pc,[],1);fc=lof.freq(core);ridge=fc(imax);
 for s=0:300:2700
  r=table2struct(old(old.tone_hz==tone&old.segment_start_s==s,:));sel=lof.tc>=s&lof.tc<s+300;
  r.peak_excess_dB=max(reshape(pc(:,sel),[],1))-median(reshape(lof.P_db(ann,sel),[],1));pk=ridge(sel);r.ridge_continuity=mean(abs(pk-median(pk))<=.2);r.passed=r.peak_excess_dB>10&&r.ridge_continuity>.6;r.frames=nnz(sel);k=k+1;rows{k}=r;
 end
 fprintf('Canonical continuous X3 screen tone %g, %.1fs\n',tone,toc(timer));
end
tab=struct2table([rows{:}]);writetable(tab,fullfile(root,'X3_visibility.csv'));writetable(tab(tab.passed,:),fullfile(root,'X3_FROZEN_TESTSET.csv'));
A=readtable('D:\论文集\phaseA\tables\A3_visibility.csv');cmp=tab(ismember(tab.tone_hz,[94 97 100 103 106 109]),:);
for j=1:height(cmp),i=find(A.tone_hz==cmp.tone_hz(j)&A.segment_start_s==cmp.segment_start_s(j));cmp.old_peak_excess_dB(j)=A.peak_excess_dB(i);cmp.old_ridge_continuity(j)=A.ridge_continuity(i);cmp.old_passed(j)=A.peak_excess_dB(i)>10&&A.ridge_continuity(i)>.6;end
cmp.pass_flipped=cmp.passed~=cmp.old_passed;writetable(cmp,fullfile(root,'X3_A3_comparison.csv'));
R=real_config();phaseD_json(fullfile(root,'SCREEN_COMPLETE.json'),struct('status','ALL_330_SCREENED_BEFORE_ANY_REAL_MODULE','candidates',330,'passed',nnz(tab.passed),'raw_sha256',R.file_sha256,'visibility_sha256',phaseD_hash(fullfile(root,'X3_visibility.csv'),'SHA-256',true),'testset_sha256',phaseD_hash(fullfile(root,'X3_FROZEN_TESTSET.csv'),'SHA-256',true),'elapsed_seconds',toc(timer),'frames','Original A3 continuous 0-3000-s LOFAR; interval assignment by frame center; first296/interior300/last295 frames','correction','Preliminary independent-window screening archived, no real-data module had run'));
end
