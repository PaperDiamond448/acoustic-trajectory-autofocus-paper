function phaseE_dhmm_develop()
root='D:\论文集';addpath(fullfile(root,'phaseD','code'));addpath(fullfile(root,'phaseD','codeX'));
dest=fullfile(root,'phaseE','E2_frontend_ext');
lock=jsondecode(fileread(fullfile(root,'phaseE','PREREGISTRATION_PhaseE_20261007.sha256.json')));
assert(strcmp(phaseD_hash(fullfile(root,'phaseE',lock.file),'SHA-256',true),lock.sha256));
assert(~isfile(fullfile(dest,'DHMM_FROZEN.json')),'PhaseE:AlreadyFrozen','Do not repeat parameter selection.');
[~,cfg,B,~]=phaseX_settings(300,false);rows={};
for scene={'S0','S2'}
 for snr=[-18 -16 -14]
  for rid=1:20
   seed=cfg.master_seed+56e6+1e4*cfg.scene_code.(scene{1})+rid;
   rec=simulate_baseband_T(cfg,scene{1},snr,seed,'eval',300);
   file=fullfile(dest,'dhmm_dev',sprintf('%s_snr%d_id%d.csv',scene{1},snr,rid));
   if isfile(file),continue;end
   [fe,~,idx,~]=phaseX_front(rec.y,rec.t,B,cfg.M);r={};
   for L1=[5 10 20]
    for G=[3 6 12]
     dc=struct('L1',L1,'G',G,'sigma_bins',1,'median_len',5);
     timer=tic;o=estimate_dhmm(fe,dc);secs=toc(timer);met=phaseD_measure(rec,o.g,idx,B);
     r{end+1}=struct('scene',string(scene{1}),'snr_db',snr,'record_id',rid,'seed',seed, ...
      'input_hash',string(phaseD_hash(rec.y,'MD5')),'L1',L1,'G',G,'sigma_bins',1, ...
      'eta',met.eta,'runtime_s',secs); %#ok<AGROW>
    end
   end
   writetable(struct2table([r{:}]),file);
   fprintf('DHMM development %s SNR=%g id=%d complete\n',scene{1},snr,rid);
  end
 end
end
files=dir(fullfile(dest,'dhmm_dev','*.csv'));assert(numel(files)==120);all=table();
for k=1:numel(files),v=readtable(fullfile(files(k).folder,files(k).name));all=[all;v];end %#ok<AGROW>
assert(height(all)==1080);writetable(all,fullfile(dest,'DHMM_development_records.csv'));
summ=groupsummary(all,{'L1','G'},'median','eta');
summ=sortrows(summ,{'median_eta','L1','G'},{'descend','ascend','ascend'});
writetable(summ,fullfile(dest,'DHMM_development_summary.csv'));
f=struct('L1',summ.L1(1),'G',summ.G(1),'sigma_bins',1,'median_len',5, ...
 'criterion','median standalone eta on phase56 development records', ...
 'development_records',120,'candidate_count',9,'selected_median_eta',summ.median_eta(1), ...
 'implementation_sha256',phaseD_hash(fullfile(root,'phaseE','scripts','estimate_dhmm.m'),'SHA-256',true), ...
 'preregistration_sha256',lock.sha256);
fid=fopen(fullfile(dest,'DHMM_FROZEN.json'),'w','n','UTF-8');assert(fid>=0);fprintf(fid,'%s\n',jsonencode(f));fclose(fid);
disp(f);
end
