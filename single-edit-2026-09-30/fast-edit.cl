
/* Exact single-byte edit, using 32-bit payload words and explicit new padding.
 * Independently certified against hashlib for insertion/deletion/replacement,
 * including both original/new MD5 padding boundary lengths.
 */
__kernel void md5_single_edit(__global const uint *raw, uint length,
    __global const uint *prefix, __global const uint *edits, __global uint *out) {
    uint gid=get_global_id(0), p=edits[gid*3], kind=edits[gid*3+1], c=edits[gid*3+2];
    uint new_length=kind==0 ? length-1 : kind==1 ? length+1 : length;
    uint blocks=(new_length+9+63)/64, first=p/64;
    uint st[4]; for(uint j=0;j<4;j++) st[j]=prefix[first*4+j];
    for(uint b=first;b<blocks;b++) {
        uint m[16];
        for(uint w=0;w<16;w++) {
            uint index=b*16+w, off=index*4, v=0;
            if(off<new_length) {
                v=raw[index];
                if(kind==0 && off+4>p) {
                    uint shifted=(v>>8) | (off+4<length ? raw[index+1]<<24 : 0);
                    if(off<p) { uint mask=(1u<<(8*(p-off)))-1; v=(v&mask)|(shifted&~mask); }
                    else v=shifted;
                } else if(kind==1 && off+4>p) {
                    uint shifted=(v<<8) | (index ? raw[index-1]>>24 : 0);
                    if(off<=p) {
                        uint k=p-off, mask=k ? (1u<<(8*k))-1 : 0;
                        v=(v&mask)|(shifted&~mask);
                        v=(v&~(255u<<(8*k)))|(c<<(8*k));
                    } else v=shifted;
                } else if(kind==2 && off<=p && p<off+4) {
                    uint shift=8*(p-off); v=(v&~(255u<<shift))|(c<<shift);
                }
            }
            if(off<=new_length && new_length<off+4) {
                uint remain=new_length-off;
                uint mask=remain ? (1u<<(8*remain))-1 : 0;
                v=(v&mask)|(128u<<(8*remain));
            }
            if(b==blocks-1 && w==14) v=new_length*8u;
            if(b==blocks-1 && w==15) v=0;
            m[w]=v;
        }
        md5_block(st,m);
    }
    for(uint j=0;j<4;j++) out[gid*4+j]=st[j];
}
