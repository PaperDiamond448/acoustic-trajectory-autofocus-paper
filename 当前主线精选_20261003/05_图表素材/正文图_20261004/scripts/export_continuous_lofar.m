% Read frozen inputs only. No receiver, optimization, screening or selection.
addpath('D:\论文集\phaseA\code');
src='D:\论文集\phaseD\X3_real';
out='D:\论文集\当前主线精选_20261003\05_图表素材\正文图_20261004\source_data';
if ~exist(out,'dir'),mkdir(out);end
y=[];
for s=0:300:2700
 q=load(fullfile(src,'screen_inputs',sprintf('f100_s%d.mat',s)),'y');
 assert(numel(q.y)==6000);y=[y;q.y(:)];
end
L=compute_lofar(y,20,200,20,8192);
rows=abs(L.freq)<=0.5;cols=L.tc>=600 & L.tc<2100;
writematrix(L.freq(rows)+100,fullfile(out,'continuous_lofar_frequency.csv'));
writematrix(L.tc(cols),fullfile(out,'continuous_lofar_time.csv'));
writematrix(L.P_db(rows,cols),fullfile(out,'continuous_lofar_power_db.csv'));
assert(sum(cols)==1500);
% Check values of the old independently-windowed display wherever support agrees.
oldP=readmatrix(fullfile(src,'role_b_LOFAR_power_db.csv'));
oldT=readmatrix(fullfile(src,'role_b_LOFAR_time_s.csv'));
[dist,loc]=min(abs(L.tc(cols)'-oldT(:)'),[],1);
assert(max(dist)<1e-9);
newP=L.P_db(rows,cols);diffmax=max(abs(newP(:,loc)-oldP),[],'all');
assert(diffmax<1e-9);
meta=struct('status','PASS','frames',sum(cols),'old_frames',numel(oldT), ...
 'new_cross_boundary_frames',sum(cols)-numel(oldT),'old_overlap_max_difference_db',diffmax, ...
 'L',200,'hop',20,'nfft',8192,'fs',20,'tone_hz',100, ...
 'note','Continuous frozen baseband; same original LOFAR function; no interpolation, no receiver or screening rerun.');
fid=fopen(fullfile(out,'continuous_lofar_validation.json'),'w','n','UTF-8');fprintf(fid,'%s',jsonencode(meta,PrettyPrint=true));fclose(fid);
disp(jsonencode(meta));
