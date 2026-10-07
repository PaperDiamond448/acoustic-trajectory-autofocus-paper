function a=phaseD_ada(y,fe,fam,u0,idx,Pcfg,t,tau,cap,mode,rerun,base)
assert(any(cap==[0.04 0.08]) && any(strcmp(mode,{'global','local'})));
assert(any(strcmp(rerun,{'A','B'})));
m=ones(fam.P,1); f=fam; f.lb=-m; f.ub=m;
if nargin<12 || isempty(base)
    timer=tic; o=estimate_proposed_T(y,fe,f,u0,idx,Pcfg); seconds=toc(timer);
else, o=base.out; seconds=base.seconds; end
[D,runs]=phaseD_dwell(o.u,m,fam,t,idx,fe.fs);
a=struct('out',o,'seconds',seconds,'rounds',0,'m',m,'initial_dwell_s',D,...
    'triggered',false,'logs',{{struct('J',o.J_best,'dwell_s',D,'seconds',seconds,'m',m,'out',o)}});
levels=[1 2 4]; last=find(levels==cap/0.02);
for k=1:last-1
    S=runs(runs.length_s>=tau,:); if isempty(S), break; end
    next=m;
    if strcmp(mode,'global')
        if all(m>=cap/0.02), break; end
        next(:)=levels(find(levels==m(1))+1);
    else
        hit=false(fam.P,1);
        for p=1:fam.P
            lo=fam.knots(max(1,p-1)); hi=fam.knots(min(fam.P,p+1));
            hit(p)=any(hi>S.start_s & lo<S.end_s);
        end
        hit=hit | [false;hit(1:end-1)] | [hit(2:end);false];
        hit=hit & m<cap/0.02; if ~any(hit), break; end
        for p=find(hit)', next(p)=levels(find(levels==m(p))+1); end
    end
    prev=o; m=next; f.lb=-m; f.ub=m; q=Pcfg;
    if strcmp(rerun,'B'), q.h_stages_s=Pcfg.h_stages_s(end); q.max_iter=Pcfg.max_iter(end); q.max_fevals=Pcfg.max_fevals(end); end
    timer=tic; o=estimate_proposed_T(y,fe,f,prev.u,idx,q); secs=toc(timer);
    assert(isequal(o.cands{1},prev.u),'Previous candidate must be explicit.');
    assert(o.J_best>=prev.J_best-1e-12,'Full-length objective decreased.');
    [D,runs]=phaseD_dwell(o.u,m,fam,t,idx,fe.fs);
    a.logs{end+1}=struct('J',o.J_best,'dwell_s',D,'seconds',secs,'m',m,'out',o);
    a.seconds=a.seconds+secs; a.rounds=k; a.triggered=true;
end
a.out=o; a.m=m;
end
