"""Exact MD5 pair generator; certification uses independent hashlib digests."""
import hashlib
import struct
import sys
from pathlib import Path
import numpy as np
import pyopencl as cl


class PairMD5GPU:
    def __init__(self,ctx,source,positions):
        if sys.byteorder!='little':raise RuntimeError('MD5 buffer decoding requires a little-endian host')
        self.ctx=ctx;self.source=bytes(source);self.positions=positions
        kernel=(Path(__file__).parent/'pair-md5.cl').read_text(encoding='utf8')
        self.kernel_sha256=hashlib.sha256(kernel.replace('\r\n','\n').encode()).hexdigest()
        self.program=cl.Program(ctx.context,kernel).build()
        padded=self.source+b'\x80'
        padded+=b'\0'*((56-len(padded)%64)%64)
        padded+=struct.pack('<Q',len(self.source)*8)
        self.blocks=len(padded)//64
        mf=cl.mem_flags
        data=np.frombuffer(padded,dtype=np.uint32)
        offsets=np.asarray(positions,dtype=np.uint32)
        self.data_buf=cl.Buffer(ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=data)
        self.position_buf=cl.Buffer(ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=offsets)
        self.prefix_buf=cl.Buffer(ctx.context,mf.READ_WRITE,(self.blocks+1)*16)
        self.prefix_kernel=self.program.md5_prefix
        self.pair_kernel=self.program.md5_pairs
        self.prefix_kernel(ctx.queue,(1,),None,self.data_buf,np.uint32(self.blocks),self.prefix_buf).wait()

    def batch(self,start,size):
        total=len(self.positions)*(len(self.positions)-1)//2
        if start<0 or size<1 or start+size>total or total>0xffffffff:
            raise ValueError('Pair interval is outside the supported 32-bit rank space')
        out=np.zeros((size,4),dtype=np.uint32)
        ob=cl.Buffer(self.ctx.context,cl.mem_flags.WRITE_ONLY,out.nbytes)
        self.pair_kernel(self.ctx.queue,(size,),None,self.data_buf,np.uint32(self.blocks),self.prefix_buf,
                         self.position_buf,np.uint32(len(self.positions)),np.uint32(start),ob).wait()
        cl.enqueue_copy(self.ctx.queue,out,ob).wait()
        return [row.tobytes() for row in out]

    def certify(self,pair_at):
        total=len(self.positions)*(len(self.positions)-1)//2
        ranks=sorted({0,total-1,total//2,*[int.from_bytes(hashlib.sha256(f'pair-md5-{i}'.encode()).digest()[:4],'little')%total for i in range(128)]})
        for rank in ranks:
            p,q=(self.positions[i] for i in pair_at(rank,len(self.positions)))
            witness=bytearray(self.source);witness[p]^=32;witness[q]^=32
            if self.batch(rank,1)[0]!=hashlib.md5(witness).digest():
                raise RuntimeError(f'GPU MD5 differs from hashlib at pair rank {rank}')
        print(f'GPU MD5: {len(ranks)} independent full-source comparisons passed.',flush=True)
