// Variable-length sparse edit lists, padded with UINT_MAX; sorted byte offsets.
__kernel void md5_sparse(__global const uint *data, uint blocks,
                        __global const uint *prefix, __global const uint *edits,
                        uint width, __global uint *output) {
    size_t gid = get_global_id(0);
    uint first_edit = edits[gid*width];
    uint first = first_edit == 0xffffffffu ? blocks : first_edit/64;
    uint state[4];
    for (uint j=0; j<4; j++) state[j]=prefix[first*4+j];
    uint cursor=0;
    for (uint block=first; block<blocks; block++) {
        uint m[16];
        for (uint j=0; j<16; j++) m[j]=data[block*16+j];
        while (cursor<width && edits[gid*width+cursor]/64==block) {
            uint p=edits[gid*width+cursor];
            m[(p&63)/4] ^= 32u << ((p&3)*8);
            cursor++;
        }
        md5_block(state,m);
    }
    for (uint j=0; j<4; j++) output[gid*4+j]=state[j];
}
