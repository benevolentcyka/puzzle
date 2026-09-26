"""Independent letter subsets, with deterministic combinatorial unranking."""
import hashlib
import math
import struct
import sys
from pathlib import Path

import numpy as np
import pyopencl as cl

HERE = Path(__file__).resolve().parent


def subset_masks(n, minimum, maximum, start, size):
    """Enumerate subsets by weight, then lexicographic selected bit positions."""
    if not 0 <= minimum <= maximum <= n <= 63:
        raise ValueError('Use 0 <= minimum <= maximum <= positions <= 63')
    total = sum(math.comb(n, k) for k in range(minimum, maximum + 1))
    if start < 0 or size < 1 or start + size > total:
        raise ValueError('Subset interval is outside its rank space')
    result = np.zeros(size, dtype=np.uint64)
    choose = np.zeros((n + 1, n + 1), dtype=np.uint64)
    for a in range(n + 1):
        for b in range(a + 1):
            choose[a, b] = math.comb(a, b)
    offset = 0
    for weight in range(minimum, maximum + 1):
        count = math.comb(n, weight)
        lo, hi = max(start, offset), min(start + size, offset + count)
        if lo < hi:
            ranks = np.arange(lo - offset, hi - offset, dtype=np.uint64)
            remaining = np.full(hi - lo, weight, dtype=np.int64)
            masks = np.zeros(hi - lo, dtype=np.uint64)
            for p in range(n):
                before = choose[n - p - 1, np.maximum(remaining - 1, 0)]
                take = (remaining > 0) & (ranks < before)
                skip = (remaining > 0) & ~take
                ranks[skip] -= before[skip]
                masks[take] |= np.uint64(1 << p)
                remaining[take] -= 1
            if np.any(remaining) or np.any(ranks):
                raise RuntimeError('Subset unranking did not terminate')
            result[lo - start:hi - start] = masks
        offset += count
    return result


class MaskMD5GPU:
    def __init__(self, ctx, source, positions):
        if sys.byteorder != 'little':
            raise RuntimeError('MD5 buffer decoding requires a little-endian host')
        self.ctx, self.source = ctx, bytes(source)
        self.positions = sorted(set(positions))
        if not self.positions or len(self.positions) > 63:
            raise ValueError('Use 1..63 distinct letter offsets')
        if any(p < 0 or p >= len(source) or not (65 <= source[p] <= 90 or 97 <= source[p] <= 122) for p in self.positions):
            raise ValueError('Every toggle offset must refer to an ASCII letter')
        kernel = (HERE.parent / 'pair-md5.cl').read_text(encoding='utf8') + '\n' + (HERE / 'mask-md5.cl').read_text(encoding='utf8')
        self.kernel_sha256 = hashlib.sha256(kernel.encode()).hexdigest()
        self.program = cl.Program(ctx.context, kernel).build()
        padded = self.source + b'\x80'
        padded += b'\0' * ((56 - len(padded) % 64) % 64)
        padded += struct.pack('<Q', len(self.source) * 8)
        self.blocks = len(padded) // 64
        mf = cl.mem_flags
        self.data_buf = cl.Buffer(ctx.context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.frombuffer(padded, dtype=np.uint32))
        self.position_buf = cl.Buffer(ctx.context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.asarray(self.positions, dtype=np.uint32))
        self.prefix_buf = cl.Buffer(ctx.context, mf.READ_WRITE, (self.blocks + 1) * 16)
        self.prefix_kernel = self.program.md5_prefix
        self.mask_kernel = self.program.md5_masks
        self.prefix_kernel(ctx.queue, (1,), None, self.data_buf, np.uint32(self.blocks), self.prefix_buf).wait()

    def witness(self, mask):
        work = bytearray(self.source)
        for bit, pos in enumerate(self.positions):
            if int(mask) & (1 << bit):
                work[pos] ^= 32
        return bytes(work)

    def batch(self, masks):
        masks = np.asarray(masks, dtype=np.uint64)
        if not len(masks) or np.any(masks >= np.uint64(1 << len(self.positions))):
            raise ValueError('Invalid mask batch')
        out = np.zeros((len(masks), 4), dtype=np.uint32)
        mb = cl.Buffer(self.ctx.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=masks)
        ob = cl.Buffer(self.ctx.context, cl.mem_flags.WRITE_ONLY, out.nbytes)
        self.mask_kernel(self.ctx.queue, (len(masks),), None, self.data_buf, np.uint32(self.blocks),
                         self.prefix_buf, self.position_buf, np.uint32(len(self.positions)), mb, ob).wait()
        cl.enqueue_copy(self.ctx.queue, out, ob).wait()
        return [row.tobytes() for row in out]

    def certify(self):
        total = 1 << len(self.positions)
        masks = sorted({0, total - 1, *[1 << i for i in range(len(self.positions))],
                        *[int.from_bytes(hashlib.sha256(f'mask-{i}'.encode()).digest()[:8], 'little') % total for i in range(128)]})
        got = self.batch(masks)
        for mask, digest in zip(masks, got):
            if digest != hashlib.md5(self.witness(mask)).digest():
                raise RuntimeError(f'Independent MD5 mismatch at mask {mask}')
        return len(masks)
