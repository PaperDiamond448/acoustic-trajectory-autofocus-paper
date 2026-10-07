function phaseE_screen_background()
root='D:\论文集';addpath(fullfile(root,'phaseD','code'));addpath(fullfile(root,'phaseD','codeX'));
[~,~,~,~]=phaseX_settings(300,false);R=real_config();dest=fullfile(root,'phaseE','E5_inject');
lock=jsondecode(fileread(fullfile(root,'phaseE','PREREGISTRATION_PhaseE_20261007.sha256.json')));
assert(strcmp(phaseD_hash(fullfile(root,'phaseE',lock.file),'SHA-256',true),lock.sha256));
assert(strcmp(phaseD_hash(R.file,'SHA-256',true),R.file_sha256),'PhaseE:RawMismatch','Raw SIO fingerprint differs.');
freq=(-100:99)'*.1;center=abs(freq)<=2.5;ring=abs(freq)>=3 & abs(freq)<=8;
w=hann(200,'symmetric');frames=(0:199)'+(0:290)*20+1;
tones=unique([reshape([49 64 79 94 112 130 148 166 201 235 283 338 388]'+[0 3 6 9 12],[],1);109;127;145;163;198;232;280;335;385]);
rows={};
for band_id=1:2
 centers=[263.5 315];fref=centers(band_id);assert(all(abs(tones-fref)>10));
 for wid=0:9
  start_s=300*wid;tag=sprintf('b%d_w%d',band_id,wid);
  if wid==0,lo=0;hi=20;elseif wid==9,lo=20;hi=0;else,lo=10;hi=10;end
  [z,extract]=phaseA_load_baseband(R.file,9,fref,20,10,R.fs_raw,R.n_raw,start_s,300,lo,hi);
  power=abs(fftshift(fft(z(frames).*w,200,1),1)).^2/sum(w.^2);
  db=10*log10(max(power,realmin));pcenter=db(center,:);pr=db(ring,:);
  [peak,linearIndex]=max(pcenter(:));floor=median(pr(:));score=peak-floor;retain=score<8;
  [ifreq,itime]=ind2sub(size(pcenter),linearIndex);cf=freq(center);
  yfft=abs(fft(z)).^2/numel(z);nu=(0:5999)'*20/6000;nu(nu>=10)=nu(nu>=10)-20;
  scale=sqrt(mean(yfft(abs(nu)<=2)));assert(isfinite(scale)&&scale>0);normalized=z/scale;
  row=struct('band_id',band_id,'center_hz',fref,'window_id',wid,'start_s',start_s,'end_s',start_s+300, ...
   'guard_lo_s',lo,'guard_hi_s',hi,'screen_score_db',score,'center_peak_db',peak,'annulus_median_db',floor, ...
   'center_peak_baseband_hz',cf(ifreq),'center_peak_frame_start_s',start_s+itime-1, ...
   'threshold_db',8,'retained',retain,'normalization_scale',scale, ...
   'raw_background_hash',string(phaseD_hash(z,'MD5')),'normalized_background_hash',string(phaseD_hash(normalized,'MD5')));
  save(fullfile(dest,'background',[tag '.mat']),'z','normalized','power','freq','extract','row','-v7');
  writetable(struct2table(row),fullfile(dest,'screen_rows',[tag '.csv']));
  rows{end+1}=row; %#ok<AGROW>
  fprintf('BACKGROUND %s center=%g score=%.4f dB retained=%d\n',tag,fref,score,retain);
 end
end
allrows=struct2table([rows{:}]);
writetable(allrows,fullfile(dest,'BACKGROUND_SCREEN.csv'));
f=struct('screen_complete',true,'screened_windows',20,'retained_windows',nnz(allrows.retained), ...
 'injection_started',false,'raw_sio_sha256',R.file_sha256,'preregistration_sha256',lock.sha256);
fid=fopen(fullfile(dest,'BACKGROUND_SCREEN_FREEZE.json'),'w','n','UTF-8');fprintf(fid,'%s\n',jsonencode(f));fclose(fid);
disp(f);
end
