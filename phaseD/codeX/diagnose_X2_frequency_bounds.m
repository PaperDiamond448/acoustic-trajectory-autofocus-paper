function diagnose_X2_frequency_bounds(firstfile,lastfile)
maxNumCompThreads(1);phaseD_setup();root='D:\论文集\phaseD';O=fullfile(root,'X2_frontend');files=dir(fullfile(O,'chunks','*.mat'));files=files(~endsWith({files.name},'.partial.mat'));rows={};
for fi=firstfile:lastfile
 C=load(fullfile(files(fi).folder,files(fi).name),'results');
 for ri=1:numel(C.results)
  S=C.results(ri);
  for k=1:numel(S.details)
   d=S.details{k};fam=d.family;a=d.ada;
   for z=1:numel(a.logs)
    o=a.logs{z}.out;g1=fam.gA+fam.r*(fam.Bt*o.u);g2=fam.gA+fam.r*fam.Bt*o.u;
    [gm,im]=max(abs(o.g));excess=max(fam.Aineq*o.u-fam.bineq);
    rows{end+1}=struct('file',string(files(fi).name),'scene',string(S.scene),'snr_db',S.snr_db,'record_id',S.record_id,'frontend',string(d.frontend),'round',z-1,'max_abs_g',gm,'grid_max_time_s',(im-1)/20,'saved_formula_max_abs_difference',max(abs(o.g-g1)),'audit_reassociation_max_abs_difference',max(abs(o.g-g2)),'registered_Aineq_max_excess',excess,'registered_checkpoints',numel(fam.tchk),'input_usable',S.rows(k).input_usable,'gain_eta',S.rows(k).gain_eta);
   end
  end
 end
end
T=struct2table([rows{:}]);writetable(T,fullfile(root,'Y_compute',sprintf('X2_BOUND_DIAGNOSTIC_%03d_%03d.csv',firstfile,lastfile)));
bad=T(T.max_abs_g>2+1e-6|T.audit_reassociation_max_abs_difference>1e-12,:);disp(bad);
phaseD_json(fullfile(root,'Y_compute',sprintf('X2_BOUND_DIAGNOSTIC_%03d_%03d.json',firstfile,lastfile)),struct('status','READ_ONLY_DIAGNOSTIC','rows',height(T),'dense_grid_outside_2Hz',height(bad),'max_saved_formula_difference',max(T.saved_formula_max_abs_difference),'max_reassociated_formula_difference',max(T.audit_reassociation_max_abs_difference),'max_registered_inequality_excess',max(T.registered_Aineq_max_excess),'max_dense_grid_abs_g',max(T.max_abs_g),'no_optimizer',true));
end
