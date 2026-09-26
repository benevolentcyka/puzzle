"""Independently check GPU MD5 pair generation at padding and rank boundaries."""
import argparse
import hashlib
import json
from pathlib import Path
import importlib.util
from pair_md5_gpu import PairMD5GPU

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pairs',ROOT/'gpu-case-pairs.py')
pairs=importlib.util.module_from_spec(spec);spec.loader.exec_module(pairs)
from bip39_gpu.gpu import context


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--platform',type=int,default=1);args=p.parse_args()
    ctx=context.GPUContext(platform_id=args.platform);tested=0
    lengths=[2,3,54,55,56,57,62,63,64,65,66,118,119,120,121,126,127,128,129,130,254,255,256,257]
    for length in lengths:
        source=bytearray(b' '*length)
        for i in range(0,length,3):source[i]=ord('a')+(i%26)
        source[-1]=ord('Z')
        positions=[i for i,b in enumerate(source) if 65<=b<=90 or 97<=b<=122]
        gpu=PairMD5GPU(ctx,source,positions);total=len(positions)*(len(positions)-1)//2
        got=gpu.batch(0,total)
        for rank,digest in enumerate(got):
            i,j=pairs.pair_at(rank,len(positions));witness=bytearray(source);witness[positions[i]]^=32;witness[positions[j]]^=32
            if digest!=hashlib.md5(witness).digest():raise RuntimeError(f'Mismatch at byte length {length}, rank {rank}')
        tested+=total
    source=(ROOT/'bases/raw-crlfcrlf.txt').read_bytes();positions=[i for i,b in enumerate(source) if 65<=b<=90 or 97<=b<=122]
    gpu=PairMD5GPU(ctx,source,positions);total=len(positions)*(len(positions)-1)//2;ranks={0,total-1,total//2}
    for i in [1,2,255,256,257,16383,16384,len(positions)-2]:
        boundary=i*(2*len(positions)-i-1)//2
        ranks.update(r for r in [boundary-1,boundary,boundary+1] if 0<=r<total)
    for rank in sorted(ranks):
        i,j=pairs.pair_at(rank,len(positions));witness=bytearray(source);witness[positions[i]]^=32;witness[positions[j]]^=32
        if gpu.batch(rank,1)[0]!=hashlib.md5(witness).digest():raise RuntimeError(f'Full-chapter rank-boundary mismatch at {rank}')
    result={'all_passed':True,'synthetic_source_lengths':lengths,'synthetic_pairs':tested,'full_source_rank_boundaries':len(ranks),'md5_kernel_sha256':gpu.kernel_sha256,'source_sha256':hashlib.sha256(source).hexdigest()}
    pairs.atomic_json(ROOT/'pair-md5-verification.json',result);print(json.dumps(result))


if __name__=='__main__':main()
