// Exhaustive search of "base text + up to K case toggles" (XOR 0x20) over a list of byte offsets,
// printing every combination whose MD5 starts with a hex prefix. MD5 midstates are cached per
// block, so cost is roughly (combinations x trailing blocks). Multi-threaded over the first offset.
// Build: gcc -O3 -march=native -pthread -o md5-toggle-search md5-toggle-search.c
// Usage: ./md5-toggle-search BASE.bin OFFSETS.txt K HEXPREFIX THREADS > out.txt
// Output lines: "M i j k H <md5>" where i,j,k index into OFFSETS.txt. Derive survivors with
// derive-survivors.cjs. Witness: planting toggles at offsets 100,555,1100 of example-ffww-lf.bin
// and searching for that text's 6-hex prefix recovered them (2026-09-25).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
typedef struct {uint32_t a,b,c,d;} st_t;
static const uint32_t K_[64]={0xd76aa478,0xe8c7b756,0x242070db,0xc1bdceee,0xf57c0faf,0x4787c62a,0xa8304613,0xfd469501,0x698098d8,0x8b44f7af,0xffff5bb1,0x895cd7be,0x6b901122,0xfd987193,0xa679438e,0x49b40821,0xf61e2562,0xc040b340,0x265e5a51,0xe9b6c7aa,0xd62f105d,0x02441453,0xd8a1e681,0xe7d3fbc8,0x21e1cde6,0xc33707d6,0xf4d50d87,0x455a14ed,0xa9e3e905,0xfcefa3f8,0x676f02d9,0x8d2a4c8a,0xfffa3942,0x8771f681,0x6d9d6122,0xfde5380c,0xa4beea44,0x4bdecfa9,0xf6bb4b60,0xbebfbc70,0x289b7ec6,0xeaa127fa,0xd4ef3085,0x04881d05,0xd9d4d039,0xe6db99e5,0x1fa27cf8,0xc4ac5665,0xf4292244,0x432aff97,0xab9423a7,0xfc93a039,0x655b59c3,0x8f0ccc92,0xffeff47d,0x85845dd1,0x6fa87e4f,0xfe2ce6e0,0xa3014314,0x4e0811a1,0xf7537e82,0xbd3af235,0x2ad7d2bb,0xeb86d391};
static const int R_[64]={7,12,17,22,7,12,17,22,7,12,17,22,7,12,17,22,5,9,14,20,5,9,14,20,5,9,14,20,5,9,14,20,4,11,16,23,4,11,16,23,4,11,16,23,4,11,16,23,6,10,15,21,6,10,15,21,6,10,15,21,6,10,15,21};
#define ROTL(x,c) (((x)<<(c))|((x)>>(32-(c))))
static void md5blk(st_t*s,const uint8_t*p){uint32_t M[16];memcpy(M,p,64);uint32_t a=s->a,b=s->b,c=s->c,d=s->d;
 for(int i=0;i<64;i++){uint32_t F;int g;if(i<16){F=(b&c)|(~b&d);g=i;}else if(i<32){F=(d&b)|(~d&c);g=(5*i+1)&15;}else if(i<48){F=b^c^d;g=(3*i+5)&15;}else{F=c^(b|~d);g=(7*i)&15;}
  F=F+a+K_[i]+M[g];a=d;d=c;c=b;b=b+ROTL(F,R_[i]);}
 s->a+=a;s->b+=b;s->c+=c;s->d+=d;}
static uint8_t *buf;static size_t blen,plen;static int npos;static int *pos;static int K;static uint32_t pfx;static int pfxbits;
static void finish(st_t s,size_t fromblk,uint8_t*work,uint8_t out[16]){for(size_t o=fromblk*64;o<plen;o+=64)md5blk(&s,work+o);memcpy(out,&s,16);}
static int prefix_ok(const uint8_t h[16]){uint32_t v=((uint32_t)h[0]<<24)|((uint32_t)h[1]<<16)|((uint32_t)h[2]<<8)|h[3];return (v>>(32-pfxbits))==pfx;}
static pthread_mutex_t mu=PTHREAD_MUTEX_INITIALIZER;static int nextx=0;static long long found=0,tested=0;
static void report(int*idx,int k,const uint8_t h[16]){pthread_mutex_lock(&mu);printf("M");for(int i=0;i<k;i++)printf(" %d",idx[i]);printf(" H ");for(int i=0;i<16;i++)printf("%02x",h[i]);printf("\n");found++;pthread_mutex_unlock(&mu);}
static void rec(uint8_t*work,st_t s,size_t sblk,int*idx,int depth,int start,long long*cnt){
 // s is state after processing blocks [0,sblk)
 for(int x=start;x<npos;x++){int p=pos[x];size_t b=p/64;st_t t=s;for(size_t o=sblk;o<b;o++)md5blk(&t,work+o*64);
  work[p]^=0x20;idx[depth]=x;uint8_t h[16];finish(t,b,work,h);(*cnt)++;if(prefix_ok(h))report(idx,depth+1,h);
  if(depth+1<K)rec(work,t,b,idx,depth+1,x+1,cnt);
  work[p]^=0x20;}
}
static void*worker(void*arg){uint8_t*work=malloc(plen);memcpy(work,buf,plen);int idx[8];long long cnt=0;st_t s0={0x67452301,0xefcdab89,0x98badcfe,0x10325476};
 for(;;){pthread_mutex_lock(&mu);int x=nextx++;pthread_mutex_unlock(&mu);if(x>=npos)break;
  int p=pos[x];size_t b=p/64;st_t t=s0;for(size_t o=0;o<b;o++)md5blk(&t,work+o*64);
  work[p]^=0x20;idx[0]=x;uint8_t h[16];finish(t,b,work,h);cnt++;if(prefix_ok(h))report(idx,1,h);
  if(K>1)rec(work,t,b,idx,1,x+1,&cnt);
  work[p]^=0x20;}
 pthread_mutex_lock(&mu);tested+=cnt;pthread_mutex_unlock(&mu);free(work);return NULL;}
int main(int argc,char**argv){ // args: basefile posfile K hexprefix threads
 if(argc<6){fprintf(stderr,"usage: %s BASE OFFSETS K HEXPREFIX THREADS\n",argv[0]);return 2;}
 FILE*f=fopen(argv[1],"rb");fseek(f,0,SEEK_END);blen=ftell(f);fseek(f,0,SEEK_SET);plen=((blen+8)/64+1)*64;buf=calloc(plen,1);if(fread(buf,1,blen,f)!=blen){fprintf(stderr,"read error\n");return 1;}fclose(f);
 buf[blen]=0x80;uint64_t bits=(uint64_t)blen*8;memcpy(buf+plen-8,&bits,8);
 FILE*g=fopen(argv[2],"r");pos=malloc(sizeof(int)*200000);npos=0;while(fscanf(g,"%d",&pos[npos])==1)npos++;fclose(g);
 K=atoi(argv[3]);pfxbits=strlen(argv[4])*4;pfx=strtoul(argv[4],NULL,16);int T=atoi(argv[5]);
 // base hash
 {st_t s={0x67452301,0xefcdab89,0x98badcfe,0x10325476};uint8_t h[16];finish(s,0,buf,h);printf("B ");for(int i=0;i<16;i++)printf("%02x",h[i]);printf(" len %zu npos %d\n",blen,npos);if(prefix_ok(h))printf("M H base\n");}
 pthread_t th[64];for(int i=0;i<T;i++)pthread_create(&th[i],NULL,worker,NULL);for(int i=0;i<T;i++)pthread_join(th[i],NULL);
 fprintf(stderr,"tested %lld found %lld\n",tested,found);return 0;}
