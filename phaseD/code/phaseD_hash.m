function h=phaseD_hash(x,alg,isfile)
if nargin<2,alg='SHA-256';end
if nargin<3,isfile=false;end
if isfile
    fid=fopen(x,'rb'); assert(fid>0); c=onCleanup(@()fclose(fid)); b=fread(fid,Inf,'*uint8');
elseif isnumeric(x)
    b=typecast([real(x(:));imag(x(:))],'uint8');
else, b=unicode2native(char(x),'UTF-8'); end
md=java.security.MessageDigest.getInstance(alg); md.update(b);
h=lower(reshape(dec2hex(typecast(md.digest(),'uint8')).',1,[]));
end
