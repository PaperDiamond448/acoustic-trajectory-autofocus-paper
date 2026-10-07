function a=phaseD_ada_prefix(chain,tau,cap)
% Exact prefix of a precomputed global chain; decisions use previous dwell.
% Also valid for a same-tau local cap-0.04 prefix of a cap-0.08 chain.
n=0;maxrounds=round(log2(cap/0.02));
while n<maxrounds && n+1<numel(chain.logs) && chain.logs{n+1}.dwell_s>=tau,n=n+1;end
a=chain;a.logs=chain.logs(1:n+1);last=a.logs{end};a.out=last.out;a.m=last.m;
a.rounds=n;a.triggered=n>0;a.seconds=0;for k=1:numel(a.logs),a.seconds=a.seconds+a.logs{k}.seconds;end
end
