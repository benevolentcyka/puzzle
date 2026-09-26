// Uses the fingerprinted, repaired BIP32/secp256k1 primitives.
__kernel void wallet_parents(__global const uchar *seeds,
                             __global const uint *path, uint length,
                             __global uchar *parents) {
    size_t gid = get_global_id(0);
    uchar seed[64], master[64];
    uchar label[12] = {'B','i','t','c','o','i','n',' ','s','e','e','d'};
    for (uint i=0; i<64; i++) seed[i] = seeds[gid*64+i];
    hmac_sha512(label,12,seed,64,master);
    uchar key[32], chain[32], next_key[32], next_chain[32];
    for (uint i=0; i<32; i++) { key[i]=master[i]; chain[i]=master[i+32]; }
    for (uint step=0; step<length; step++) {
        bip32_ckdpriv(key,chain,path[step],next_key,next_chain);
        for (uint i=0; i<32; i++) { key[i]=next_key[i]; chain[i]=next_chain[i]; }
    }
    for (uint i=0; i<32; i++) { parents[gid*64+i]=key[i]; parents[gid*64+32+i]=chain[i]; }
}

__kernel void wallet_children(__global const uchar *parents,
                              __global const uint *indices, uint count, uint direct,
                              __global uchar *hashes, __global uchar *keys,
                              __global uchar *public_keys) {
    size_t gid = get_global_id(0);
    size_t seed_index = gid/count;
    uint index = indices[gid%count];
    uchar key[32], chain[32], child[32], child_chain[32];
    for (uint i=0; i<32; i++) { key[i]=parents[seed_index*64+i]; chain[i]=parents[seed_index*64+32+i]; }
    if (direct) { for (uint i=0; i<32; i++) child[i]=key[i]; }
    else bip32_ckdpriv(key,chain,index,child,child_chain);
    uint ax[8], ay[8];
    secp256k1_point_mul_g(ax,ay,child);
    uchar pub[33], hash[20];
    secp256k1_pubkey_compressed(pub,ax,ay);
    hash160(pub,33,hash);
    for (uint i=0; i<20; i++) hashes[gid*20+i]=hash[i];
    for (uint i=0; i<32; i++) keys[gid*32+i]=child[i];
    for (uint i=0; i<33; i++) public_keys[gid*33+i]=pub[i];
}
