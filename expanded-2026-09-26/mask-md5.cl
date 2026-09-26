// md5_block and md5_prefix come from the separately fingerprinted pair-md5.cl.
// Each bit selects one independently toggled ASCII letter. Positions are sorted.
__kernel void md5_masks(__global const uint *data, uint blocks,
                       __global const uint *prefix, __global const uint *positions,
                       uint n, __global const ulong *masks, __global uint *output) {
    size_t gid = get_global_id(0);
    ulong mask = masks[gid];
    uint state[4];
    uint first = blocks;
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
    for (uint j = 0; j < 4; j++) output[gid * 4 + j] = state[j];
}
