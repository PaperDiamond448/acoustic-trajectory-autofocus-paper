function [D,runs,mask]=phaseD_dwell(u,m,fam,t,idx,fs)
a=abs(fam.Bt(idx,:)*u(:)); b=fam.Bt(idx,:)*m(:);
mask=a>=0.95*b;
d=diff([false;mask(:);false]); starts=find(d==1); ends=find(d==-1)-1;
lengths=(ends-starts+1)/fs;
runs=table(t(idx(starts)),t(idx(ends))+1/fs,lengths,...
    'VariableNames',{'start_s','end_s','length_s'});
if isempty(lengths), D=0; else, D=max(lengths); end
end
