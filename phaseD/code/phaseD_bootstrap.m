function out=phaseD_bootstrap(values,scenes,ids,snrs,seed)
% values are paired differences (records x endpoints). Sampling is by seed
% within scene and carries all seven SNR cells together.
assert(size(values,1)==numel(ids)); rs=RandStream('mt19937ar','Seed',seed);
ss=unique(scenes); qq=unique(snrs); boot=zeros(2000,size(values,2));
cellmeans=[];
for si=1:numel(ss)
    for qi=1:numel(qq)
        use=scenes==ss(si)&snrs==qq(qi);cellmeans(end+1,:)=mean(values(use,:),1);
    end
end
for b=1:2000
    total=zeros(1,size(values,2));
    for si=1:numel(ss)
        rid=unique(ids(scenes==ss(si))); draw=rid(randi(rs,numel(rid),numel(rid),1));
        for qi=1:numel(qq)
            use=scenes==ss(si)&snrs==qq(qi); tabids=ids(use);v=values(use,:);
            [ok,ix]=ismember(draw,tabids); assert(all(ok)); total=total+mean(v(ix,:),1);
        end
    end
    boot(b,:)=total/(numel(ss)*numel(qq));
end
out=struct('mean',mean(cellmeans,1),'ci',prctile(boot,[2.5 97.5],1),'replicates',2000,...
    'seed',seed,'resampling','scene-stratified seed clusters carrying all SNR cells');
end
