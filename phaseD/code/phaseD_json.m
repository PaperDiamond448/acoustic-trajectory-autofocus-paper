function phaseD_json(path,x)
fid=fopen(path,'w','n','UTF-8'); assert(fid>0); c=onCleanup(@()fclose(fid));
fprintf(fid,'%s',jsonencode(x,'PrettyPrint',true));
end
