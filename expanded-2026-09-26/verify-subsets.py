"""Certify unranking and MD5 against itertools/hashlib, including 64-bit ranks."""
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'bip39-gpu-review/src'))
from mask_md5_gpu import MaskMD5GPU, subset_masks
from bip39_gpu.gpu.context import GPUContext


def main():
    ctx = GPUContext(platform_id=1)
    checked = 0
    for n in [1,2,7,12]:
        for minimum, maximum in [(0,n),(0,min(n,3)),(min(n,2),n)]:
            expected = [sum(1 << b for b in c) for k in range(minimum,maximum+1) for c in itertools.combinations(range(n),k)]
            for start in range(0,len(expected),31):
                got = subset_masks(n,minimum,maximum,start,min(31,len(expected)-start))
                assert list(map(int,got)) == expected[start:start+len(got)]
                checked += len(got)
    # Exercise ranks beyond uint32 and the last combination in a huge family.
    for n in [32,40,63]:
        total = 1 << n
        for rank in [0,total//2,total-2,total-1,*[int.from_bytes(hashlib.sha256(f'large-rank-{n}-{i}'.encode()).digest()[:8],'big')%total for i in range(25)]]:
            mask = int(subset_masks(n,0,n,rank,1)[0])
            assert 0 <= mask < total
            bits = [p for p in range(n) if mask & (1 << p)]
            weight = len(bits)
            # Independent inverse formula, using the reverse combinadic rank.
            reverse = sum(math.comb(n-1-p,weight-j) if n-1-p >= weight-j else 0 for j,p in enumerate(bits))
            reconstructed = sum(math.comb(n,k) for k in range(weight)) + math.comb(n,weight)-1-reverse
            assert reconstructed == rank
        assert int(subset_masks(n,0,n,total-1,1)[0]) == total-1
    comparisons = 0
    for length in [1,55,56,63,64,65,119,120,127,128,129,257,1024]:
        source = (b'aB' * ((length+1)//2))[:length]
        positions = sorted({0, length//2, length-1})
        gpu = MaskMD5GPU(ctx,source,positions)
        masks = list(range(1 << len(positions)))
        assert gpu.batch(masks) == [hashlib.md5(gpu.witness(m)).digest() for m in masks]
        comparisons += len(masks)
    # A long source and all 32 independent offsets, including padding/prefix reuse.
    source = b'aB' * 24000
    positions = [i*750 for i in range(63)]
    gpu = MaskMD5GPU(ctx,source,positions)
    comparisons += gpu.certify()
    report = {'subset_unranking_itertools_comparisons':checked, 'md5_hashlib_comparisons':comparisons,
              'large_rank_positions':[32,40,63], 'large_rank_inverse_comparisons':87,
              'md5_kernel_sha256':gpu.kernel_sha256, 'passed':True}
    (HERE/'subset-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
