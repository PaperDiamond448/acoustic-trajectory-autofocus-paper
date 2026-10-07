function reconcile_phaseC_csv()
% Extra read-only reconciliation after the numerical-process exit anomaly.
root='D:\论文集\phaseD\C_confirm';addpath('D:\论文集\phaseD\code');
T=readtable(fullfile(root,'C_records.csv'),'TextType','string');assert(height(T)==14000);
map=containers.Map('KeyType','char','ValueType','double');
for i=1:height(T),key=makekey(T.scene(i),T.snr_db(i),T.record_id(i),T.method(i));assert(~isKey(map,key));map(key)=i;end
files=dir(fullfile(root,'chunks','*.mat'));assert(numel(files)==280);
n=0;maxdiff=0;seen=false(14000,1);
for fi=1:numel(files)
    C=load(fullfile(files(fi).folder,files(fi).name),'results');
    for ri=1:numel(C.results)
        S=C.results(ri);
        for mi=1:numel(S.rows)
            r=S.rows(mi);key=makekey(r.scene,r.snr_db,r.record_id,r.method);assert(isKey(map,key));i=map(key);assert(~seen(i));seen(i)=true;
            fields=fieldnames(r);
            for k=1:numel(fields)
                name=fields{k};a=r.(name);b=T.(name)(i);
                if isnumeric(a)||islogical(a)
                    a=double(a);b=double(b);assert(isequal(isnan(a),isnan(b)) && isequal(isinf(a),isinf(b)));
                    if isfinite(a),d=abs(a-b);assert(d<=1e-12);maxdiff=max(maxdiff,d);
                    elseif isinf(a),assert(a==b);end
                else,assert(strcmp(string(a),string(b)));end
            end
            n=n+1;
        end
    end
end
assert(n==14000 && all(seen));
phaseD_json(fullfile(root,'CSV_MAT_RECONCILIATION.json'),struct('status','PASS','rows',n,'chunks',280,'numeric_tolerance',1e-12,'numeric_max_abs_difference',maxdiff,'scope','Every CSV field reconciled against original MAT row; no output files modified and no optimization'));
fprintf('CSV/MAT reconciliation PASS: 14000 rows, max numeric difference %.17g\n',maxdiff);
end

function k=makekey(scene,snr,rid,method)
k=sprintf('%s|%d|%d|%s',char(scene),snr,rid,char(method));
end
