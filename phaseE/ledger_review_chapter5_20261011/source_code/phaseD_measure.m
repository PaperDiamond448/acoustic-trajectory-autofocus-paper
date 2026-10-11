function m=phaseD_measure(rec,g,idx,B)
t=rec.t(:); phi=2*pi*cumtrapz(t,g(:)); nfft=2^nextpow2(B.fft_pad*numel(idx));
f=(-nfft/2:nfft/2-1)'*B.fs/nfft; P=fftshift(abs(fft(rec.y(idx).*exp(-1j*phi(idx)),nfft)).^2);
sel=abs(f)<=B.band(2); ps=P(sel); fb=f(sel); [pk,ip]=max(ps);
m.peak_power=pk; m.peak_db=10*log10(max(pk,realmin)); m.peak_frequency=fb(ip);
side=(f>=B.noise_bands(1,1)&f<=B.noise_bands(1,2)) | (f>=B.noise_bands(2,1)&f<=B.noise_bands(2,2));
m.prom_db=10*log10(max(pk,realmin)/max(median(P(side)),realmin));
db=10*log10(max(ps,realmin)); th=db(ip)-10*log10(2); il=ip; ir=ip;
while il>1 && db(il-1)>=th, il=il-1; end
while ir<numel(db) && db(ir+1)>=th, ir=ir+1; end
if il==1 || ir==numel(db), m.width=NaN; else
    fl=crossing(fb(il-1),db(il-1),fb(il),db(il),th);
    fr=crossing(fb(ir),db(ir),fb(ir+1),db(ir+1),th); m.width=fr-fl;
end
den=max(sum(abs(rec.truth.s_target(idx)))^2,realmin);
st=rec.truth.s_target(idx).*exp(-1j*phi(idx)); Pt=fftshift(abs(fft(st,nfft)).^2);
m.eta=max(Pt(sel))/den; phiT=2*pi*cumtrapz(t,rec.truth.gtrue(:));
stT=rec.truth.s_target(idx).*exp(-1j*phiT(idx)); Po=fftshift(abs(fft(stT,nfft)).^2);
m.eta_oracle=max(Po(sel))/den; m.eta_loss_db=-10*log10(max(m.eta,realmin)/max(m.eta_oracle,realmin));
e=g(idx)-rec.truth.gtrue(idx); m.rmse=sqrt(mean(e.^2)); a=abs(e); m.pout=mean(a>0.02); m.maxabs=max(a);
mask=a>0.02; d=diff([false;mask(:);false]); st0=find(d==1); en=find(d==-1)-1;
if isempty(st0), m.longest=0; else, m.longest=max(en-st0+1)/B.fs; end
end

function x=crossing(f1,d1,f2,d2,th)
if d2==d1, x=(f1+f2)/2; else, x=f1+(th-d1)*(f2-f1)/(d2-d1); end
end
