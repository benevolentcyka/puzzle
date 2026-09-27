"""Test sentence-level interpretations of the claimed format example.

case: independently toggle all 30 sentence endpoints, with the published 3c6
MD5 filter. drafts: independently retain/delete all 15 sentences, preserving
their punctuation and retained paragraph joins; no MD5 prefix filter.
These are bounded hypotheses, not a complete puzzle search.
"""
import argparse
import datetime
import hashlib
import importlib.util
import itertools
import json
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('quoted_masks', HERE/'quoted-mask-search.py')
Q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Q)
A, ROOT = Q.A, Q.ROOT
PARENT = "m/44'/0'/0'/0"


def question():
    post = next(x for x in json.loads((ROOT/'aoi-posts-archive.json').read_bytes()) if x['id']=='cleczc')
    q = post['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0].encode('ascii')
    assert hashlib.md5(q).hexdigest() == '7759227d7406d8230d7e3a8f7b9846d7'
    return q


def units(source, sep):
    """Only split at sentence-final punctuation followed by a space.

    The example has no abbreviations that need exceptions. An ellipsis stays
    intact. Quotes closing a sentence stay with that sentence.
    """
    return [re.split(rb'(?<=[.!?]) +(?=[A-Za-z])', p) for p in source.split(sep)]


def draft(groups, mask, sep):
    paras, bit = [], 0
    for group in groups:
        kept = []
        for sentence in group:
            if mask & (1 << bit):
                kept.append(sentence)
            bit += 1
        if kept:
            paras.append(b' '.join(kept))
    return sep.join(paras)


def endpoints(source, sep):
    positions, offset = [], 0
    for group in units(source, sep):
        for sentence in group:
            letters = [i for i,c in enumerate(sentence) if 65<=c<=90 or 97<=c<=122]
            positions += [offset+letters[0],offset+letters[-1]]
            offset += len(sentence)+1
        offset += len(sep)-1
    return sorted(set(positions))


def fixture_check():
    q = question()
    expected = [0,92,96,254,258,414,419,531,535,652,655,717,721,920,
                925,1004,1009,1106,1109,1146,1150,1294,1300,1356,1359,1386,
                1392,1436,1439,1547]
    assert endpoints(q,b'\n\n') == expected
    assert [len(g) for g in units(q,b'\n\n')] == [1,1,1,1,2,1,1,2,3,2]
    for sep in [b'\n\n',b'\r\n\r\n']:
        source = sep.join(q.split(b'\n\n'))
        groups = units(source,sep)
        assert draft(groups,(1<<15)-1,sep) == source
        assert draft(groups,1<<5,sep) == b'Even after I explained the method used and the result in detail.'
        assert draft(groups,(1<<4)|(1<<5),sep) == source.split(sep)[4]
        assert draft(groups,0,sep) == b''
        # Independent byte walk: sentence endpoint offsets agree after CR insertion.
        actual = endpoints(source,sep)
        mapped = [len(sep.join(q[:p].split(b'\n\n'))) for p in expected]
        assert actual == mapped
        for mask in range(1<<15):
            out = draft(groups,mask,sep)
            assert not out.startswith(sep) and not out.endswith(sep)
    return 2*(1<<15)+10


class CheckedWallet:
    def __init__(self, platform, indices):
        from bip39_gpu.gpu import context, pbkdf2_gpu
        from bip_utils import Base58Decoder
        context._global_context = context.GPUContext(platform_id=platform)
        pbkdf2_gpu._pbkdf2_cpu_fallback = A.CERT.die_fallback
        self.ctx, self.pbkdf2, self.indices = context._global_context, pbkdf2_gpu, indices
        self.gpu = Q.WalletPathsGPU(self.ctx)
        self.certified = self.gpu.certify([dict(name='bip44',parent=PARENT,hardened=False,direct=False)])
        self.target = A.TARGETS['example'][0]
        self.target_hash = Base58Decoder.CheckDecode(self.target)[1:]

    def check(self, rows, name, config):
        """Rows are (MD5 entropy, exact source bytes, metadata)."""
        from bip_utils import Bip32Secp256k1
        from bip39_gpu.gpu.bip32_gpu import hash160_to_p2pkh,base58check_encode
        if not rows:
            return False
        for entropy, source, label in rows:
            if hashlib.md5(source).digest()!=entropy:
                raise RuntimeError('Exact witness does not match MD5 entropy')
        words = [A.mnemonic(e) for e,_,_ in rows]
        seeds = self.pbkdf2.pbkdf2_hmac_sha512_gpu([A.HELPER.normalized_password(w) for w in words],[b'mnemonic']*len(words))
        hashes,keys,pubs = self.gpu.batch(seeds,PARENT,self.indices)
        for k in sorted({0,len(rows)//2,len(rows)-1}):
            seed = hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
            if seed!=seeds[k]:
                raise RuntimeError('Independent seed mismatch')
            for j,index in enumerate(self.indices):
                node = Bip32Secp256k1.FromSeed(seed).DerivePath(f'{PARENT}/{index}')
                pub = node.PublicKey().RawCompressed().ToBytes()
                h = hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest()
                r = k*len(self.indices)+j
                if hashes[r].tobytes()!=h or keys[r].tobytes()!=node.PrivateKey().Raw().ToBytes() or pubs[r].tobytes()!=pub:
                    raise RuntimeError('Independent key/public/hash160 mismatch')
        for r,h in enumerate(hashes):
            if h.tobytes()!=self.target_hash:
                continue
            k,j = divmod(r,len(self.indices))
            seed = hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
            path = f'{PARENT}/{self.indices[j]}'
            node = Bip32Secp256k1.FromSeed(seed).DerivePath(path)
            pub = node.PublicKey().RawCompressed().ToBytes()
            if hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())!=self.target:
                raise RuntimeError('Hit failed CPU verification')
            dest = HERE/f'FOUND-structural-{name}.txt'
            dest.write_bytes(rows[k][1])
            A.CERT.atomic_json(dest.with_suffix('.json'),dict(address=self.target,path=path,
                md5=rows[k][0].hex(),mnemonic=words[k],metadata=rows[k][2],configuration=config,
                private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01')))
            print(f'VERIFIED MATCH saved privately: {dest}',flush=True)
            return True
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--family',choices=['case','drafts'],required=True)
    ap.add_argument('--join',choices=['lf','crlf'],default='lf')
    ap.add_argument('--indices',default='0,1,2,3,4,5,6')
    ap.add_argument('--platform',type=int,default=1)
    ap.add_argument('--limit',type=int)
    ap.add_argument('--verify-only',action='store_true')
    args = ap.parse_args()
    indices = [int(x) for x in args.indices.split(',')]
    if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices):
        ap.error('Use distinct nonhardened indices')
    if args.limit is not None and args.limit<1:
        ap.error('Limit must be positive')
    fixture_count = fixture_check()
    print(f'PASS: {fixture_count:,} sentence serialization checks',flush=True)
    if args.verify_only:
        return
    sep = b'\n\n' if args.join=='lf' else b'\r\n\r\n'
    source = sep.join(question().split(b'\n\n'))
    wallet = CheckedWallet(args.platform,indices)
    md5 = Q.FilteredMasks(wallet.ctx,source,endpoints(source,sep)) if args.family=='case' else None
    comparisons = md5.certify() if md5 else 0
    bases = [(label['source'],{k:v for k,v in label.items() if k!='source'})
             for _,label in A.span_bases() if label['join']==args.join]
    total = 1<<30 if md5 else len(bases)*((1<<15)-1)
    config = dict(family=args.family,join=args.join,indices=indices,source_sha256=hashlib.sha256(source).hexdigest(),
        target=wallet.target,parent=PARENT,language='english',passphrase='',prefix='3c6' if md5 else None,
        positions=md5.base.positions if md5 else None,capitalization_timing='before deletion' if not md5 else None,
        md5_filter_comparisons=comparisons,sentence_fixtures=fixture_count,bip32_comparisons=wallet.certified,
        gpu_kernel_sha256=A.CERT.gpu_kernel_fingerprint(),wallet_kernel_sha256=wallet.gpu.kernel_sha256,
        code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                     [Path(__file__),HERE/'quoted-mask-search.py',HERE/'quoted-mask.cl',HERE/'search-assumptions.py']})
    tag = hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    dest = HERE/f'structural-{args.family}-{args.join}-{tag}.json'
    state = json.loads(dest.read_bytes()) if dest.exists() else dict(configuration=config,texts_total=total,
        next_rank=0,derived_entropies=0,derived_addresses=0,matches=0,complete=False)
    if state['configuration']!=config:
        raise RuntimeError('Checkpoint differs')
    stop = min(total,state['next_rank']+args.limit) if args.limit else total
    begun = last = time.monotonic()
    print(f'{dest.name}: {state["next_rank"]:,}/{total:,}',flush=True)
    while state['next_rank']<stop:
        start = state['next_rank']
        size = min(1048576 if md5 else 8192,stop-start)
        if md5:
            rows = [(e,md5.base.witness(mask),dict(mask=mask)) for mask,e in md5.batch(start,size)]
        else:
            rows = []
            for rank in range(start,start+size):
                b,m = divmod(rank,(1<<15)-1)
                work = draft(units(bases[b][0],sep),m+1,sep)
                rows.append((hashlib.md5(work).digest(),work,dict(bases[b][1],retained_sentence_mask=m+1)))
        if wallet.check(rows,f'{args.family}-{args.join}',config):
            state['matches']+=1
            A.CERT.atomic_json(dest,state)
            return
        state['next_rank']+=size
        state['derived_entropies']+=len(rows)
        state['derived_addresses']+=len(rows)*len(indices)
        state['complete']=state['next_rank']==total
        state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        A.CERT.atomic_json(dest,state)
        if time.monotonic()-last>=20 or state['next_rank']==stop:
            print(f'texts={state["next_rank"]:,}/{total:,} addresses={state["derived_addresses"]:,} elapsed={time.monotonic()-begun:.1f}s',flush=True)
            last=time.monotonic()
    print('COMPLETE, no match' if state['complete'] else 'LIMIT reached; rerun to resume',flush=True)


if __name__=='__main__':
    main()
