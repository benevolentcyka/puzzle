"""Sparse subsets over more than 63 offsets, using binary-search unranking."""
import hashlib
import math
import struct
import sys
from pathlib import Path
import numpy as np
import pyopencl as cl

HERE=Path(__file__).resolve().parent
EMPTY=0xffffffff


def sparse_indices(n,minimum,maximum,start,size):
    if not 0 <= minimum <= maximum <= min(n,4): raise ValueError('Sparse enumeration supports up to four edits')
    total=sum(math.comb(n,k) for k in range(minimum,maximum+1))
    if total>2**63-1 or start<0 or size<1 or start+size>total: raise ValueError('Invalid sparse rank interval')
    choose=np.zeros((n+1,maximum+1),dtype=np.uint64)
    for a in range(n+1):
        for b in range(min(a,maximum)+1): choose[a,b]=math.comb(a,b)
    result=np.full((size,max(1,maximum)),EMPTY,dtype=np.uint32)
    offset=0
    for weight in range(minimum,maximum+1):
        count=math.comb(n,weight); lo,hi=max(start,offset),min(start+size,offset+count)
        if lo<hi:
            ranks=np.arange(lo-offset,hi-offset,dtype=np.uint64)
            first=np.zeros(hi-lo,dtype=np.int64)
            for slot in range(weight):
                remaining=weight-slot
                left=first.copy(); right=np.full(hi-lo,n-remaining,dtype=np.int64)
                choices=choose[n-first,remaining]
                while np.any(left<right):
                    mid=(left+right+1)//2
                    before=choices-choose[n-mid,remaining]
                    advance=before<=ranks
                    left=np.where(advance,mid,left); right=np.where(advance,right,mid-1)
                selected=left; ranks-=choices-choose[n-selected,remaining]
                result[lo-start:hi-start,slot]=selected; first=selected+1
            if np.any(ranks): raise RuntimeError('Sparse unranking did not terminate')
        offset+=count
    return result


class SparseMD5GPU:
    def __init__(self,ctx,source,positions):
        if sys.byteorder!='little': raise RuntimeError('MD5 buffer decoding requires a little-endian host')
        self.ctx=ctx; self.source=bytes(source); self.positions=sorted(set(positions))
        if not self.positions or any(p<0 or p>=len(source) or not (65<=source[p]<=90 or 97<=source[p]<=122) for p in self.positions): raise ValueError('Invalid ASCII-letter offsets')
        kernel=(HERE.parent/'pair-md5.cl').read_text(encoding='utf8')+'\n'+(HERE/'sparse-md5.cl').read_text(encoding='utf8')
        self.kernel_sha256=hashlib.sha256(kernel.encode()).hexdigest()
        self.program=cl.Program(ctx.context,kernel).build()
        padded=self.source+b'\x80'; padded+=b'\0'*((56-len(padded)%64)%64); padded+=struct.pack('<Q',len(self.source)*8)
        self.blocks=len(padded)//64; mf=cl.mem_flags
        self.data_buf=cl.Buffer(ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=np.frombuffer(padded,dtype=np.uint32))
        self.prefix_buf=cl.Buffer(ctx.context,mf.READ_WRITE,(self.blocks+1)*16)
        self.prefix_kernel=self.program.md5_prefix; self.sparse_kernel=self.program.md5_sparse
        self.prefix_kernel(ctx.queue,(1,),None,self.data_buf,np.uint32(self.blocks),self.prefix_buf).wait()

    def descriptors(self,minimum,maximum,start,size):
        selected=sparse_indices(len(self.positions),minimum,maximum,start,size)
        positions=np.asarray(self.positions,dtype=np.uint32)
        return np.where(selected==EMPTY,np.uint32(EMPTY),positions[np.minimum(selected,len(positions)-1)])

    def witness(self,edits):
        work=bytearray(self.source)
        for p in edits:
            if int(p)!=EMPTY: work[int(p)]^=32
        return bytes(work)

    def batch(self,edits):
        edits=np.ascontiguousarray(edits,dtype=np.uint32)
        if edits.ndim!=2 or edits.shape[1]<1 or edits.shape[1]>4 or not len(edits): raise ValueError('Use an edit matrix with width 1..4')
        real_pairs=(edits[:,:-1]!=EMPTY)&(edits[:,1:]!=EMPTY)
        if np.any((edits!=EMPTY)&(edits>=len(self.source))) or np.any(edits[:,1:]<edits[:,:-1]) or np.any(real_pairs&(edits[:,1:]==edits[:,:-1])):
            raise ValueError('Invalid sorted edit offsets')
        out=np.zeros((len(edits),4),dtype=np.uint32); mf=cl.mem_flags
        eb=cl.Buffer(self.ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=edits)
        ob=cl.Buffer(self.ctx.context,mf.WRITE_ONLY,out.nbytes)
        self.sparse_kernel(self.ctx.queue,(len(edits),),None,self.data_buf,np.uint32(self.blocks),self.prefix_buf,eb,np.uint32(edits.shape[1]),ob).wait()
        cl.enqueue_copy(self.ctx.queue,out,ob).wait()
        return [row.tobytes() for row in out]

    def certify(self):
        n=len(self.positions); total=sum(math.comb(n,k) for k in range(min(n,4)+1))
        ranks=sorted({0,total//2,total-1,*[int.from_bytes(hashlib.sha256(f'sparse-{i}'.encode()).digest()[:8],'little')%total for i in range(128)]})
        descriptors=np.concatenate([self.descriptors(0,min(n,4),r,1) for r in ranks])
        got=self.batch(descriptors)
        for rank,edits,digest in zip(ranks,descriptors,got):
            if digest!=hashlib.md5(self.witness(edits)).digest(): raise RuntimeError(f'Independent sparse MD5 mismatch at rank {rank}')
        return len(ranks)
