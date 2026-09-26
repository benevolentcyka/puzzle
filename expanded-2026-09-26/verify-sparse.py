"""Exhaustive small iterator comparisons, large rank inverses and MD5 controls."""
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'bip39-gpu-review/src'))
from sparse_md5_gpu import SparseMD5GPU,sparse_indices,EMPTY
from bip39_gpu.gpu.context import GPUContext


def main():
    checked=0; large=0
    for n in [1,3,7,12,18]:
        for minimum,maximum in [(0,min(n,4)),(min(n,2),min(n,3))]:
            expected=[c for k in range(minimum,maximum+1) for c in itertools.combinations(range(n),k)]
            for start in range(0,len(expected),37):
                got=sparse_indices(n,minimum,maximum,start,min(37,len(expected)-start))
                assert [tuple(int(p) for p in row if p!=EMPTY) for row in got]==expected[start:start+len(got)]
                checked+=len(got)
    for n in [32,546,35825]:
        for maximum in [3,4]:
            total=sum(math.comb(n,k) for k in range(maximum+1))
            ranks=sorted({0,total-1,total//2,*[int.from_bytes(hashlib.sha256(f'sparse-large-{n}-{maximum}-{i}'.encode()).digest()[:8],'big')%total for i in range(32)]})
            for rank in ranks:
                row=sparse_indices(n,0,maximum,rank,1)[0]; bits=[int(p) for p in row if p!=EMPTY]; weight=len(bits)
                reverse=sum(math.comb(n-1-p,weight-j) if n-1-p>=weight-j else 0 for j,p in enumerate(bits))
                reconstructed=sum(math.comb(n,k) for k in range(weight))+math.comb(n,weight)-1-reverse
                assert reconstructed==rank; large+=1
    ctx=GPUContext(platform_id=1); comparisons=0
    for length in [1,55,56,63,64,65,119,120,127,128,129,257]:
        source=(b'aB'*((length+1)//2))[:length]
        positions=sorted({0,length//3,2*length//3,length-1})
        gpu=SparseMD5GPU(ctx,source,positions)
        total=1<<len(positions); edits=gpu.descriptors(0,len(positions),0,total)
        assert gpu.batch(edits)==[hashlib.md5(gpu.witness(e)).digest() for e in edits]
        comparisons+=total
    source=b'aB'*24000; positions=list(range(0,len(source),90)); gpu=SparseMD5GPU(ctx,source,positions)
    comparisons+=gpu.certify()
    report={'passed':True,'itertools_comparisons':checked,'large_rank_inverse_comparisons':large,
            'md5_hashlib_comparisons':comparisons,'sparse_kernel_sha256':gpu.kernel_sha256}
    (HERE/'sparse-verification.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))


if __name__=='__main__': main()
