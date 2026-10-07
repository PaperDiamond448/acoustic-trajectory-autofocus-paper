function out=estimate_dhmm(fe,dcfg)
% Luo et al., JEIT 2022, equations 9/10/13/15-19, single-line adaptation.
% Dynamic slope is estimated separately for every destination-state survivor.
g=fe.g_coarse(:);M=numel(g);K=fe.K;L1=dcfg.L1;G=dcfg.G;sig=dcfg.sigma_bins;
R=abs(fe.C_coarse).^2/max(fe.noise_hat*fe.sumw2,realmin);
LL=log1p(R);score=LL(:,1)-log(M);
psi=zeros(M,K,'uint16');slope=zeros(M,1);state=(1:M)';
for k=2:K
 offsets=round(slope)+(-G:G);
 dest=state+offsets;valid=dest>=1 & dest<=M;
 logker=-.5*((offsets-slope)/sig).^2;
 logker(~valid)=-Inf;
 mx=max(logker,[],2);lognorm=mx+log(sum(exp(logker-mx),2));
 vals=score+logker-lognorm;
 src=repmat(state,1,2*G+1);dest=dest(valid);vals=vals(valid);src=src(valid);
 best=accumarray(dest,vals,[M 1],@max,-Inf);
 winner=vals==best(dest);
 prev=accumarray(dest(winner),src(winner),[M 1],@min,0);
 unreachable=prev==0;prev(unreachable)=state(unreachable);
 psi(:,k)=uint16(prev);score=best+LL(:,k);
 % Fit survivor state history on centred integer frame positions (Eq.18).
 n=min(L1,k);hist=zeros(M,n);hist(:,n)=state;
 for h=n-1:-1:1
  col=k-(n-1-h);
  hist(:,h)=double(psi(sub2ind([M K],hist(:,h+1),repmat(col,M,1))));
 end
 xx=(0:n-1)';xx=xx-mean(xx);slope=(hist*xx)/sum(xx.^2);slope(unreachable)=0;
end
[out.dp_score,p]=max(score);path=zeros(K,1);path(K)=p;
for k=K:-1:2,path(k-1)=double(psi(path(k),k));end
out.path=path;out.g_raw=g(path);
out.g_frame=medfilt1(out.g_raw,dcfg.median_len,[],1,'omitnan','truncate');
out.g=interp_const(fe.tc,out.g_frame,fe.t);
out.config=dcfg;
end
