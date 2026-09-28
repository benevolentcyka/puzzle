"""Bounded check for reuse of previously public text, hashes, or private keys.

This tests a stale-input hypothesis, not an inference that reuse happened.
The corpus is public puzzle records created before the example's funding block.
Their archived content can include later edits; this is not a historical snapshot.
No transactions are signed or sent. Future matching keys remain in FOUND files.
"""
import datetime
import hashlib
import importlib.util
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
spec=importlib.util.spec_from_file_location('structural',ROOT/'assumptions-2026-09-27/structural-search.py')
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
A=S.A
CUTOFF=1564635878
TARGETS=A.TARGETS['example']+A.TARGETS['chapter']


def corpus():
    paths=[ROOT/'aoi-posts-archive.json',ROOT/'aoi-comments-archive.json',
           ROOT/'followup-2026-09-26/research/puzzleponky-comments-1.json']
    records=[]
    for p in paths:
        obj=json.loads(p.read_bytes())
        for item in obj if isinstance(obj,list) else obj['data']:
            if item.get('created_utc',CUTOFF+1)>CUTOFF:
                continue
            text=item.get('body',item.get('selftext',''))
            records.append((item['id'],text))
    return records,{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def candidates(records):
    texts={}
    hexes={}
    wifs={}
    for source,text in records:
        spans=[('paragraph',x) for x in text.split('\n\n')]
        spans += [('line',x) for x in text.splitlines()]
        spans += [('quote',m.group(1)) for m in re.finditer(r'"([^"\n]{1,2048})"',text)]
        spans += [('solution-clause',m.group(1)) for m in re.finditer(r'(?:solution|answer)\s*(?:was|is|:)\s*(.+)',text,re.I)]
        for shape,value in spans:
            for trim,t in [('exact',value),('trim',value.strip())]:
                if not 1<=len(t)<=4096:
                    continue
                b=t.encode('utf8')
                texts.setdefault(b,dict(source=source,shape=shape,trim=trim))
        for value in re.findall(r'(?<![0-9a-fA-F])(?:[0-9a-fA-F]{64}|[0-9a-fA-F]{32})(?![0-9a-fA-F])',text):
            hexes.setdefault(value.lower(),source)
        for value in re.findall(r'(?<![1-9A-HJ-NP-Za-km-z])(?:[KL][1-9A-HJ-NP-Za-km-z]{51}|5[1-9A-HJ-NP-Za-km-z]{50})(?![1-9A-HJ-NP-Za-km-z])',text):
            wifs.setdefault(value,source)
    entropies={}
    for text,label in texts.items():
        for algo in ['md5','sha256']:
            e=hashlib.new(algo,text).digest()
            entropies.setdefault(e,dict(label,algorithm=algo,source_sha256=hashlib.sha256(text).hexdigest()))
    for value,source in hexes.items():
        entropies.setdefault(bytes.fromhex(value),dict(source=source,shape='literal-public-hex'))
    # Two independently solved fixtures certify this exact matching pipeline.
    for value,label in [('9dd2efb9bc976c2095bd534d7b8d431c','stage-one'),
                        (hashlib.md5(b'Still 21st Century').hexdigest(),'grycoin-one')]:
        entropies.setdefault(bytes.fromhex(value),dict(shape='control',control=label))
    return list(entropies.items()),wifs,len(texts),len(hexes)


def main():
    from bip_utils import Base58Decoder,Bip32Secp256k1
    from bip39_gpu.gpu.bip32_gpu import hash160_to_p2pkh,base58check_encode
    records,files=corpus()
    entries,wifs,text_count,hex_count=candidates(records)
    wallet=S.CheckedWallet(1,list(range(21)))
    wanted={Base58Decoder.CheckDecode(a)[1:]:a for a in TARGETS}
    controls={'19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN','18EpYz5qB3XoxZWouJF3KdEp3E2nfv9FgP'}
    found_controls=set()
    config=dict(cutoff_block_time=CUTOFF,cutoff_applies_to='record created_utc; archived content can contain later edits',targets=TARGETS,source_files=files,indices=wallet.indices,
        parent=S.PARENT,language='english',passphrase='',algorithms=['md5','sha256','literal-public-hex'],
        wallet_kernel_sha256=wallet.gpu.kernel_sha256,gpu_kernel_sha256=A.CERT.gpu_kernel_fingerprint(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    matches=[]
    valid_wifs=0
    for wif,source in wifs.items():
        try:
            payload=Base58Decoder.CheckDecode(wif)
        except Exception:
            continue
        if not (payload[0]==128 and (len(payload)==33 or (len(payload)==34 and payload[-1]==1))):
            continue
        key=payload[1:33]
        from bip_utils import Secp256k1PrivateKey
        pub=Secp256k1PrivateKey.FromBytes(key).PublicKey()
        valid_wifs+=1
        for compressed in [True,False]:
            encoded=(pub.RawCompressed() if compressed else pub.RawUncompressed()).ToBytes()
            address=hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(encoded).digest()).digest())
            if address in TARGETS:
                dest=HERE/'FOUND-public-wif.json'
                A.CERT.atomic_json(dest,dict(address=address,private_wif=wif,source=source,compressed=compressed))
                matches.append(dict(address=address,file=dest.name))
    print(f'{len(records)} public records; {text_count} text values; {hex_count} literal hashes; {valid_wifs} valid published WIFs; {len(entries)} distinct entropies',flush=True)
    comparisons=0
    for begin in range(0,len(entries),4096):
        batch=entries[begin:begin+4096]
        words=[A.mnemonic(e) for e,_ in batch]
        seeds=wallet.pbkdf2.pbkdf2_hmac_sha512_gpu([A.HELPER.normalized_password(w) for w in words],[b'mnemonic']*len(words))
        hashes,keys,pubs=wallet.gpu.batch(seeds,S.PARENT,wallet.indices)
        for k in sorted({0,len(batch)//2,len(batch)-1}):
            seed=hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
            assert seed==seeds[k]
            for j,index in enumerate(wallet.indices):
                node=Bip32Secp256k1.FromSeed(seed).DerivePath(f'{S.PARENT}/{index}')
                pub=node.PublicKey().RawCompressed().ToBytes()
                h=hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest()
                r=k*len(wallet.indices)+j
                assert h==hashes[r].tobytes() and pub==pubs[r].tobytes() and node.PrivateKey().Raw().ToBytes()==keys[r].tobytes()
                comparisons+=1
        control_hashes={Base58Decoder.CheckDecode(a)[1:]:a for a in controls}
        for r,h in enumerate(hashes):
            raw=h.tobytes()
            if raw in control_hashes:
                found_controls.add(control_hashes[raw])
            if raw not in wanted:
                continue
            k,j=divmod(r,len(wallet.indices))
            seed=hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
            path=f'{S.PARENT}/{wallet.indices[j]}'
            node=Bip32Secp256k1.FromSeed(seed).DerivePath(path)
            pub=node.PublicKey().RawCompressed().ToBytes()
            assert hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())==wanted[raw]
            dest=HERE/'FOUND-public-entropy.json'
            A.CERT.atomic_json(dest,dict(address=wanted[raw],path=path,entropy=batch[k][0].hex(),source=batch[k][1],
                private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01')))
            matches.append(dict(address=wanted[raw],file=dest.name))
        print(f'Checked {min(begin+4096,len(entries)):,}/{len(entries):,} entropies',flush=True)
    assert found_controls==controls,'Positive matching controls failed'
    report=dict(configuration=config,public_records=len(records),distinct_texts=text_count,literal_hex_strings=hex_count,
        valid_public_wifs=valid_wifs,wif_address_comparisons=valid_wifs*2,entropy_candidates=len(entries),
        derived_addresses=len(entries)*len(wallet.indices),positive_controls=sorted(found_controls),
        sampled_cpu_comparisons=comparisons,complete=True,matches=matches,
        checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        limitations='A finite extraction of public text is not every prior full solution string. No arbitrary passphrases or other paths.')
    A.CERT.atomic_json(HERE/'public-wallet-result.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='configuration'}),flush=True)


if __name__=='__main__':
    main()
