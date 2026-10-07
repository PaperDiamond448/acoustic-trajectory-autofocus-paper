function [x, hdr] = sio_read_channel(file, chan, n0, n)
%SIO_READ_CHANNEL  Read N samples of one channel of an SIO file, starting at
%   ZERO-BASED sample offset N0 of that channel.
%
%   Written instead of calling the distributed sioread.m because that routine
%   maps a start point that is an exact multiple of the record length onto
%   point 2048 of the previous record (its pp1 == 0 branch uses the literal
%   2048 rather than the file's points-per-record).  This reader is checked
%   against sioread on an offset where sioread is correct; see run_bg_check.
%
%   Layout: record 0 is the header; data record (r-1)*nc + chan holds samples
%   (r-1)*ptrec + 1 .. r*ptrec of channel chan.

fid = fopen(file, 'r', 'b');
assert(fid > 0, 'cannot open %s', file);
c = onCleanup(@() fclose(fid));
h = fread(fid, 8, 'int32');
if h(8) ~= 32677
    clear c; fid = fopen(file, 'r', 'l'); c = onCleanup(@() fclose(fid));
    h = fread(fid, 8, 'int32');
    assert(h(8) == 32677, 'bad byte-swap constant');
    hdr.endian = 'l';
else
    hdr.endian = 'b';
end
hdr.id = h(1); hdr.nr = h(2); hdr.rl = h(3); hdr.nc = h(4);
hdr.sl = h(5); hdr.f0 = h(6); hdr.np = h(7);
type = 'int16'; if hdr.sl == 4, type = 'single'; end
ptrec = hdr.rl/hdr.sl;
hdr.ptrec = ptrec;
assert(chan >= 1 && chan <= hdr.nc, 'channel out of range');
assert(n0 >= 0 && n0 + n <= hdr.np, 'segment outside the record');

r1 = floor(n0/ptrec);                 % zero-based record index within channel
r2 = floor((n0+n-1)/ptrec);
nrec = r2 - r1 + 1;
buf = zeros(nrec*ptrec, 1);
for k = 0:nrec-1
    trec = (r1+k)*hdr.nc + chan;      % record number in the file (0 = header)
    fseek(fid, hdr.rl*trec, 'bof');
    buf(k*ptrec + (1:ptrec)) = fread(fid, ptrec, ['*' type]);
end
off = n0 - r1*ptrec;
x = buf(off + (1:n));
end
