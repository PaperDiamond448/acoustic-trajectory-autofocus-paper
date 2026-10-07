function [m,f,p]=phaseX3_metrics(y,t,g,tone,gps,idx)
z=y(:).*exp(-1i*2*pi*cumtrapz(t(:),g(:)));
nfft=2^nextpow2(8*numel(y));f=tone+(-nfft/2:nfft/2-1)'*20/nfft;
p=abs(fftshift(fft(z,nfft))).^2/numel(y);
use=f>=tone-1.5&f<=tone+1.5;fu=f(use);pu=p(use);[pk,im]=max(pu);
offset=abs(fu-fu(im));floorMask=offset>=.5&offset<=1.5;
if any(floorMask),prom=10*log10(pk/max(median(pu(floorMask)),realmin));else,prom=NaN;end
db=10*log10(max(pu,realmin));target=db(im)-3;
il=find(db(1:im)<=target,1,'last');ir0=find(db(im:end)<=target,1,'first');
if isempty(il)||isempty(ir0),width=NaN;else,ir=im+ir0-1;fl=interp1(db([il il+1]),fu([il il+1]),target,'linear');fr=interp1(db([ir-1 ir]),fu([ir-1 ir]),target,'linear');width=fr-fl;end
e=tone+g(idx)-gps(idx);valid=isfinite(e);e=e(valid);
if isempty(e),bias=NaN;rms=NaN;else,bias=mean(e);rms=sqrt(mean((e-bias).^2));end
m=struct('peak_power',pk,'peak_frequency_hz',fu(im),'prominence_db',prom,'width_3db_hz',width,'gps_mean_offset_hz',bias,'gps_demeaned_rms_hz',rms,'gps_samples',nnz(valid));
end
