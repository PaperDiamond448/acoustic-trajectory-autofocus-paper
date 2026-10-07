function phaseE_guided_batch(first,last)
root='D:\论文集';addpath(fullfile(root,'phaseD','code'));addpath(fullfile(root,'phaseD','codeX'));
dest=fullfile(root,'phaseE','E4_guided_real');
lock=jsondecode(fileread(fullfile(root,'phaseE','PREREGISTRATION_PhaseE_20261007.sha256.json')));
assert(strcmp(phaseD_hash(fullfile(root,'phaseE',lock.file),'SHA-256',true),lock.sha256));
cases=[52 600;52 900;52 2400;61 2100;100 600;100 900;100 1200;100 1500;100 1800;103 900;103 1200;118 1500;121 0;133 1200;136 900];
for i=first:last
 file=fullfile(dest,'records',sprintf('f%d_s%d_T300.csv',cases(i,1),cases(i,2)));
 if isfile(file),fprintf('ALREADY SAVED case %d\n',i);continue;end
 fprintf('CASE %d/15\n',i);S=phaseE_guided_one(cases(i,1),cases(i,2));clear S;
end
end
