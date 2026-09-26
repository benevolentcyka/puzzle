"""Test the seven non-English wordlists available in the July 2019 converter.

The example uses every subset of 21 documented/boundary letter positions,
both paragraph joins, and the published 3c6 prefix. The chapter uses the 576
previously documented group/heading/whitespace shapes. Both test raw entropy
and all ten fixed-word-count/MD5-hex-case settings at BIP44 indices 0..20.
All language and seed calculations are first checked against Trezor vectors.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import time
import unicodedata
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
LANGUAGES=['japanese','spanish','chinese_simplified','chinese_traditional','french','italian','korean']
GROUPS=[[4,5,6,7],[92,93,94,95],[167,168,169,170],[230,231,232,234]]


def save(path, value):
    tmp=path.with_suffix('.json.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)


def mnemonic(entropy, language, lists):
    n=len(entropy)*8;cs=n//32
    bits=(int.from_bytes(entropy,'big')<<cs)|(hashlib.sha256(entropy).digest()[0]>>(8-cs))
    words=[lists[language][(bits>>shift)&2047] for shift in range(n+cs-11,-1,-11)]
    return ('\u3000' if language=='japanese' else ' ').join(words)


def normalized_password(words):
    password=unicodedata.normalize('NFKD',words).encode('utf8')
    return hashlib.sha512(password).digest() if len(password)>128 else password


def example_candidates(errors):
    posts=json.loads((ROOT/'aoi-posts-archive.json').read_text())
    q=next(x for x in posts if x['id']=='cleczc')['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0]
    assert hashlib.md5(q.encode()).hexdigest().startswith('7759227')
    candidates=[]
    for join,separator in [('lf','\n\n'),('crlf','\r\n\r\n')]:
        source=separator.join(q.split('\n\n')).encode('ascii');positions=[];offset=0
        for p in q.split('\n\n'):
            letters=[i for i,c in enumerate(p) if c.isascii() and c.isalpha()]
            positions.extend([offset+letters[0],offset+letters[-1]])
            if 'post outing himself.' in p:positions.append(offset+p.index('post outing himself.')+len('post outing himself')-1)
            offset+=len(p)+len(separator)
        positions=sorted(set(positions));assert len(positions)==21
        work=bytearray(source);last=0
        for rank in range(1<<len(positions)):
            mask=rank^(rank>>1);changed=last^mask
            while changed:
                bit=changed&-changed;work[positions[bit.bit_length()-1]]^=32;changed^=bit
            last=mask;h=hashlib.md5(work).digest()
            if sum(a!=b for a,b in zip((h[0]>>4,h[0]&15,h[1]>>4),(3,12,6)))<=errors:
                candidates.append((h,{'join':join,'rank':rank,'mask':mask,'md5':h.hex(),'positions':positions,'source':source}))
    return candidates


def chapter_candidates():
    paras=json.loads((ROOT/'wattpad-paragraphs.json').read_text(encoding='utf8'));unique={}
    assert len(paras)==273
    for mask in range(16):
        selected={i for bit,g in enumerate(GROUPS) if mask&(1<<bit) for i in g}
        for start in [0,1,3]:
            for spaces in ['keep','nbsp-space','trim']:
                for join,sep in [('lf','\n\n'),('crlf','\r\n\r\n')]:
                    for tail in ['',sep[:len(sep)//2]]:
                        ps=[]
                        for i in range(start,len(paras)):
                            p=paras[i]
                            if i in selected:
                                chars=list(p);letters=[j for j,c in enumerate(chars) if c.isascii() and c.isalpha()]
                                chars[letters[0]]=chars[letters[0]].lower();chars[letters[-1]]=chars[letters[-1]].upper();p=''.join(chars)
                            if spaces!='keep':p=p.replace('\u00a0',' ')
                            if spaces=='trim':p=p.strip()
                            p=p.replace('\r\n','\n').replace('\r','\n')
                            if join=='crlf':p=p.replace('\n','\r\n')
                            ps.append(p)
                        text=(sep.join(ps)+tail).encode('utf8');h=hashlib.md5(text).digest()
                        unique.setdefault(h,{'group_mask':mask,'start':start,'spaces':spaces,'join':join,'tail':tail,'md5':h.hex(),'source':text})
    assert len(unique)==576
    return list(unique.items())


def canonical_example_candidates():
    """Do not trust the prefix when testing the obvious sign-rule answers."""
    posts=json.loads((ROOT/'aoi-posts-archive.json').read_text())
    q=next(x for x in posts if x['id']=='cleczc')['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0]
    assert hashlib.md5(q.encode()).hexdigest().startswith('7759227');original=q.split('\n\n');unique={}
    for draft in ['published','removed','split']:
        paras=list(original)
        if draft=='removed':paras=[p.split(' Even after I explained',1)[0] if ' Even after I explained' in p else p for p in paras]
        if draft=='split':
            paras=[]
            for p in original:
                if ' Even after I explained' in p:
                    before,after=p.split(' Even after I explained',1);paras.extend([before,'Even after I explained'+after])
                else:paras.append(p)
        initials=[next(c for c in p if c.isascii() and c.isalpha()) for p in paras]
        selections=[[],[i for i,c in enumerate(initials) if c in 'FW'],[i for i,c in enumerate(initials) if c not in 'ITASM'],list(range(len(paras)))]
        for selected in selections:
            for mode in ['lu','tt','l0','0u','ul']:
                for named_mask in range(4):
                    ps=[]
                    for i,p in enumerate(paras):
                        chars=list(p);letters=[j for j,c in enumerate(chars) if c.isascii() and c.isalpha()]
                        if i in selected:
                            for bit,pos in enumerate([letters[0],letters[-1]]):
                                if mode[bit]=='l':chars[pos]=chars[pos].lower()
                                elif mode[bit]=='u':chars[pos]=chars[pos].upper()
                                elif mode[bit]=='t':chars[pos]=chars[pos].swapcase()
                        if 'post outing himself.' in p:
                            if named_mask&1:chars[letters[0]]=chars[letters[0]].swapcase()
                            if named_mask&2:pos=p.index('post outing himself.')+len('post outing himself')-1;chars[pos]=chars[pos].swapcase()
                        ps.append(''.join(chars))
                    for join,sep in [('lf','\n\n'),('crlf','\r\n\r\n'),('lf1','\n'),('crlf1','\r\n')]:
                        source=sep.join(ps).encode();md=hashlib.md5(source).digest()
                        unique.setdefault(md,{'draft':draft,'selected':selected,'mode':mode,'named_mask':named_mask,'join':join,'md5':md.hex(),'source':source})
    return list(unique.items())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family',choices=['example','chapter','canonical-example'],required=True)
    parser.add_argument('--prefix-errors',type=int,choices=[0,1],default=0)
    parser.add_argument('--indices',default=','.join(map(str,range(21))))
    parser.add_argument('--languages',default=','.join(LANGUAGES))
    parser.add_argument('--batch',type=int,default=16384)
    parser.add_argument('--platform',type=int,default=1)
    parser.add_argument('--dependency',type=Path,default=ROOT/'bip39-gpu-review')
    args=parser.parse_args();indices=[int(x) for x in args.indices.split(',')];languages=(['english']+LANGUAGES if args.languages=='all' else args.languages.split(','))
    if not indices or len(indices)!=len(set(indices)) or any(i<0 for i in indices):parser.error('Use distinct nonnegative indices')
    if any(l not in ['english']+LANGUAGES for l in languages) or len(languages)!=len(set(languages)):parser.error('Use distinct supported languages')
    sys.path.insert(0,str(args.dependency/'src'))
    spec=importlib.util.spec_from_file_location('certifier',ROOT/'gpu-case-pairs.py');cert=importlib.util.module_from_spec(spec);spec.loader.exec_module(cert)
    from bip39_gpu.gpu import context,pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs,hash160_to_p2pkh
    from bip_utils import Bip44,Bip44Coins,Bip44Changes,Base58Decoder
    context._global_context=context.GPUContext(platform_id=args.platform);pbkdf2_gpu._pbkdf2_cpu_fallback=cert.die_fallback
    cert.certify_gpu(indices[0]);cert.certify_gpu(indices[-1])
    word_dir=HERE/'verification/languages';lists={};assets=hashlib.sha256()
    for language in ['english']+LANGUAGES:
        content=(word_dir/f'{language}.json').read_bytes();assets.update(content);record=json.loads(content)
        assert record['commit']=='45e40c288fe0d6cfba2c57a68f421eeb34d41385'
        lists[language]=record['words'];assert len(lists[language])==2048
    vectors=json.loads((word_dir/'trezor-vectors.json').read_bytes());vector_words=[];expected_seeds=[]
    for language in ['english']+LANGUAGES:
        for entropy,expected_words,seed,_ in vectors[language]:
            words=mnemonic(bytes.fromhex(entropy),language,lists)
            if unicodedata.normalize('NFKD',words)!=unicodedata.normalize('NFKD',expected_words):raise RuntimeError(f'Trezor mnemonic mismatch: {language}')
            cpu_seed=hashlib.pbkdf2_hmac('sha512',unicodedata.normalize('NFKD',words).encode(),b'mnemonicTREZOR',2048,64)
            if cpu_seed.hex()!=seed:raise RuntimeError(f'Trezor CPU seed mismatch: {language}')
            vector_words.append(words);expected_seeds.append(bytes.fromhex(seed))
    got=pbkdf2_gpu.pbkdf2_hmac_sha512_gpu([normalized_password(w) for w in vector_words],[b'mnemonicTREZOR']*len(vector_words))
    if list(got)!=expected_seeds:raise RuntimeError('GPU seed mismatch against multilingual Trezor vectors')
    print(f'{len(vector_words)} official multilingual mnemonic/seed vectors passed.',flush=True)
    candidates=(example_candidates(args.prefix_errors) if args.family=='example' else canonical_example_candidates() if args.family=='canonical-example' else chapter_candidates())
    print(f'{args.family}: {len(candidates):,} source candidates; languages={languages}; indices={indices}',flush=True)
    # A stream of metadata and entropy binds deterministic resume to the inputs.
    entropies=[];stream=hashlib.sha256()
    for md,label in candidates:
        for mode,entropy in [('raw-128',md)]+[(f'fixed-{length*8}-{casing}',hashlib.sha256((md.hex() if casing=='lower' else md.hex().upper()).encode()).digest()[:length]) for casing in ['lower','upper'] for length in [16,20,24,28,32]]:
            entropies.append((entropy,mode,label));stream.update(entropy);stream.update(json.dumps({k:v for k,v in label.items() if k not in ['source']},sort_keys=True).encode());stream.update(mode.encode())
    total=len(entropies)*len(languages);stream_sha=stream.hexdigest();kernel=cert.gpu_kernel_fingerprint();assets_sha=assets.hexdigest()
    suffix='' if languages==LANGUAGES else '-languages-all' if languages==['english']+LANGUAGES else '-languages-'+'-'.join(languages)
    state_path=HERE/f'language-settings-{args.family}-errors{args.prefix_errors}{suffix}.json'
    old=json.loads(state_path.read_text()) if state_path.exists() else None
    if old and any(old[k]!=v for k,v in {'candidate_stream_sha256':stream_sha,'gpu_kernel_sha256':kernel,'wordlists_sha256':assets_sha,'indices':indices,'languages':languages}.items()):raise RuntimeError('Checkpoint inputs differ')
    rank=old['next_rank'] if old else 0;begin=time.perf_counter()
    targets=['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W','1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC'] if args.family=='chapter' else ['1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi']
    target_hashes={Base58Decoder.CheckDecode(a)[1:]:a for a in targets}
    def cpu_node(seed,index):return Bip44.FromSeed(seed,Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    while rank<total:
        size=min(args.batch,total-rank);entries=[];words=[]
        for r in range(rank,rank+size):
            lang_index,offset=divmod(r,len(entropies));entropy,mode,label=entropies[offset];language=languages[lang_index]
            entries.append((entropy,mode,label,language));words.append(mnemonic(entropy,language,lists))
        seeds=pbkdf2_gpu.pbkdf2_hmac_sha512_gpu([normalized_password(w) for w in words],[b'mnemonic']*size)
        sampled=sorted({0,size//2,size-1})
        for k in sampled:
            independent=hashlib.pbkdf2_hmac('sha512',unicodedata.normalize('NFKD',words[k]).encode(),b'mnemonic',2048,64)
            if independent!=seeds[k]:raise RuntimeError('Sampled multilingual CPU/GPU seed mismatch')
        for index in indices:
            output=batch_seed_to_gpu_outputs(seeds,address_index=index)
            if output is None:raise RuntimeError('GPU BIP32 unavailable; refusing fallback')
            hashes=output[0]
            for k in sampled:
                if hash160_to_p2pkh(hashes[k])!=cpu_node(seeds[k],index).PublicKey().ToAddress():raise RuntimeError('Sampled independent multilingual address mismatch')
            for k,h in enumerate(hashes):
                if h not in target_hashes:continue
                node=cpu_node(seeds[k],index)
                if node.PublicKey().ToAddress()!=target_hashes[h]:raise RuntimeError('Hit failed independent CPU validation')
                entropy,mode,label,language=entries[k];witness=bytearray(label['source'])
                if args.family=='example':
                    for bit,pos in enumerate(label['positions']):
                        if label['mask']&(1<<bit):witness[pos]^=32
                assert hashlib.md5(witness).hexdigest()==label['md5']
                dest=HERE/f'FOUND-language-{args.family}.txt';dest.write_bytes(witness)
                save(dest.with_suffix('.json'),{'address':target_hashes[h],'language':language,'mode':mode,'index':index,'entropy':entropy.hex(),'mnemonic':words[k],'private_wif':node.PrivateKey().ToWif(),'label':{a:b for a,b in label.items() if a!='source'}})
                print(f'VERIFIED MATCH {dest}',flush=True);return
        rank+=size
        save(state_path,{'targets':targets,'family':args.family,'allowed_prefix_errors':args.prefix_errors,'prefix_filter_used':args.family=='example','source_candidates':len(candidates),'languages':languages,'indices':indices,'official_vectors':len(vector_words),'candidate_stream_sha256':stream_sha,'wordlists_sha256':assets_sha,'gpu_kernel_sha256':kernel,'candidates_total':total,'next_rank':rank,'derived_addresses':rank*len(indices),'complete':rank==total,'matches':0,'updated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
        print(f'checked={rank:,}/{total:,}, addresses={rank*len(indices):,}; no match; elapsed={time.perf_counter()-begin:.1f}s',flush=True)


if __name__=='__main__':main()
