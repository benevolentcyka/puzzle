/* MD5 after one byte deletion/insertion/replacement.
 * Prefix is borrowed ONLY before the edited block; all suffix bytes, padding
 * and the changed length are rebuilt. Output words have MD5's little endian.
 * kind: 0 delete, 1 insert, 2 replace.
 */
__kernel void md5_single_edit(__global const uchar *raw, uint length,
 __global const uint *prefix, __global const uint *edits, __global uint *output) {
 uint gid=get_global_id(0),p=edits[gid*3],kind=edits[gid*3+1],value=edits[gid*3+2];
 uint size=kind==0 ? length-1 : kind==1 ? length+1 : length;
 uint blocks=(size+9+63)/64, padded=blocks*64, first=p/64;
 uint state[4]; for(uint z=0;z<4;z++)state[z]=prefix[first*4+z];
 for(uint block=first;block<blocks;block++) {
  uint m[16];
  for(uint z=0;z<16;z++) {
   uint word=0;
   for(uint byte=0;byte<4;byte++) {
    uint o=block*64+z*4+byte,v=0;
    if(o<size) {
     if(kind==0) v=raw[o<p ? o : o+1];
     else if(kind==1) v=o==p ? value : raw[o<p ? o : o-1];
     else v=o==p ? value : raw[o];
    } else if(o==size) v=0x80;
    else if(o>=padded-8) v=(uint)(((ulong)size*8) >> (8*(o-(padded-8))))&255;
    word|=v<<(byte*8);
   }
   m[z]=word;
  }
  md5_block(state,m);
 }
 for(uint z=0;z<4;z++)output[gid*4+z]=state[z];
}

