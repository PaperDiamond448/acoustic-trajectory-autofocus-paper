function phaseX_verify_sources()
root='D:\论文集\phaseD';
for name={'SOURCE_MANIFEST_X_sha256.csv'}
 m=readtable(fullfile(root,'codeX',name{1}),'TextType','string');
 for k=1:height(m),assert(strcmp(phaseD_hash(char(m.source_file(k)),'SHA-256',true),m.sha256(k)),'Frozen source changed: %s',m.source_file(k));end
end
end
