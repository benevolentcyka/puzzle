// Exact enumeration of binary letter masks, followed by a declared 12-bit MD5
// prefix filter. Full MD5 words and the exact mask are returned for every hit.
__kernel void quoted_masks(__global const uint *data, uint blocks,
                           __global const uint *prefix, __global const uint *positions,
                           uint n, ulong start, uint wanted, uint capacity,
                           volatile __global uint *count,
                           __global ulong *masks, __global uint *digests) {
    ulong mask = start + get_global_id(0);
    uint state[4], first = blocks;
    for (uint i = 0; i < n; i++) {
        if (mask & ((ulong)1 << i)) { first = positions[i] / 64; break; }
    }
    for (uint j = 0; j < 4; j++) state[j] = prefix[first * 4 + j];
    uint cursor = 0;
    while (cursor < n && positions[cursor] / 64 < first) cursor++;
    for (uint block = first; block < blocks; block++) {
        uint m[16];
        for (uint j = 0; j < 16; j++) m[j] = data[block * 16 + j];
        while (cursor < n && positions[cursor] / 64 == block) {
            uint p = positions[cursor];
            if (mask & ((ulong)1 << cursor)) m[(p & 63) / 4] ^= 32u << ((p & 3) * 8);
            cursor++;
        }
        md5_block(state, m);
    }
    uint nibble_prefix = ((state[0] & 255u) << 4) | ((state[0] >> 12) & 15u);
    if (nibble_prefix == wanted) {
        uint row = atomic_inc(count);
        if (row < capacity) {
            masks[row] = mask;
            for (uint j = 0; j < 4; j++) digests[row * 4 + j] = state[j];
        }
    }
}
