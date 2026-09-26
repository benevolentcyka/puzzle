"""Historical BIP32 presets and BIP44 account/change hypotheses, without hints.

The 2019 converter explicitly offered m/0, Bitcoin Core m/0'/0' with hardened
addresses, blockchain.info m/44'/0'/0', and MultiBit HD m/0'/0. This matrix
also checks root addresses, normal/hardened root children, the opposite Core
checkbox setting, and BIP44 accounts 0/1, change chains 0/1. All eight original
wordlists and raw + ten fixed entropy settings are enabled by default.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import sys
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0,str(ROOT/'bip39-gpu-review/src'))
sys.path.insert(0,str(HERE))
from wallet_paths_gpu import WalletPathsGPU, full_path


def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def presets():
    return [{'name':name,'parent':parent,'hardened':hard,'direct':direct} for name,parent,hard,direct in [
        ('root','m',False,True),
        ('bip32-default','m/0',False,False),
        ('bip32-default-hardened','m/0',True,False),
        ('bitcoin-core',"m/0'/0'",True,False),
        ('bitcoin-core-normal',"m/0'/0'",False,False),
        ('blockchain-coinomi-ledger',"m/44'/0'/0'",False,False),
        ('multibit-hd',"m/0'/0",False,False),
        ('root-child','m',False,False),
        ('root-child-hardened','m',True,False),
        ('bip44-external',"m/44'/0'/0'/0",False,False),
        ('bip44-internal',"m/44'/0'/0'/1",False,False),
        ('bip44-account1-external',"m/44'/0'/1'/0",False,False),
        ('bip44-account1-internal',"m/44'/0'/1'/1",False,False),
    ]]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--family',choices=['example','chapter','both'],default='both')
    ap.add_argument('--languages',default='all')
    ap.add_argument('--indices',default=','.join(map(str,range(21))))
    ap.add_argument('--passphrase',default='')
    ap.add_argument('--platform',type=int,default=1)
    ap.add_argument('--batch',type=int,default=2048)
    ap.add_argument('--limit',type=int,help='Maximum new seed candidates; omission runs to completion')
    ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args()
    helper=load_module('language_helpers',ROOT/'followup-2026-09-26/language-settings-gpu.py')
    cert=load_module('pair_certifier',ROOT/'gpu-case-pairs.py')
    languages=['english']+helper.LANGUAGES if args.languages=='all' else args.languages.split(',')
    indices=[int(i) for i in args.indices.split(',')]
    if not languages or len(set(languages))!=len(languages) or any(l not in ['english']+helper.LANGUAGES for l in languages): ap.error('Use distinct historical languages')
    if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices): ap.error('Use distinct indices below 2**31')
    if args.batch<1 or (args.limit is not None and args.limit<1): ap.error('Batch and limit must be positive')
    salt=b'mnemonic'+unicodedata.normalize('NFKD',args.passphrase).encode()
    if len(salt)>128: ap.error('This runner supports a normalized passphrase salt of at most 128 bytes')
    from bip39_gpu.gpu import context,pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import hash160_to_p2pkh,base58check_encode
    from bip_utils import Bip32Secp256k1,Base58Decoder
    context._global_context=context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback=cert.die_fallback
    gpu=WalletPathsGPU(context._global_context); paths=presets()
    comparisons=gpu.certify(paths)
    word_dir=ROOT/'followup-2026-09-26/verification/languages'
    lists={}; assets=hashlib.sha256(); vectors=json.loads((word_dir/'trezor-vectors.json').read_bytes())
    vector_words=[]; expected=[]
    for language in ['english']+helper.LANGUAGES:
        content=(word_dir/f'{language}.json').read_bytes(); assets.update(content); record=json.loads(content)
        if record['commit']!='45e40c288fe0d6cfba2c57a68f421eeb34d41385': raise RuntimeError('Wordlist is not the pinned historical source')
        lists[language]=record['words']; assert len(lists[language])==2048
        for entropy,words,seed,_ in vectors[language]:
            got=helper.mnemonic(bytes.fromhex(entropy),language,lists)
            if unicodedata.normalize('NFKD',got)!=unicodedata.normalize('NFKD',words): raise RuntimeError('Official mnemonic vector mismatch')
            vector_words.append(got); expected.append(bytes.fromhex(seed))
    got=pbkdf2_gpu.pbkdf2_hmac_sha512_gpu([helper.normalized_password(w) for w in vector_words],[b'mnemonicTREZOR']*len(vector_words))
    if list(got)!=expected: raise RuntimeError('Official multilingual seed vector mismatch')
    report={'passed':True,'bip32_private_public_hash160_comparisons':comparisons,'official_multilingual_seed_vectors':len(vector_words),
            'wallet_kernel_sha256':gpu.kernel_sha256,'gpu_kernel_sha256':cert.gpu_kernel_fingerprint(),'presets':paths}
    cert.atomic_json(HERE/'wallet-path-verification.json',report)
    print(f'{comparisons} independent private/public/hash160 path comparisons and {len(vector_words)} official seed vectors passed.',flush=True)
    if args.verify_only: return
    families=['example','chapter'] if args.family=='both' else [args.family]
    candidates=[]
    for family in families:
        candidates.extend((family,md,label) for md,label in (helper.canonical_example_candidates() if family=='example' else helper.chapter_candidates()))
    entries=[]; stream=hashlib.sha256()
    for family,md,label in candidates:
        modes=[('raw-128',md)]+[(f'fixed-{length*8}-{casing}',hashlib.sha256((md.hex() if casing=='lower' else md.hex().upper()).encode()).digest()[:length]) for casing in ['lower','upper'] for length in [16,20,24,28,32]]
        for language in languages:
            for mode,entropy in modes:
                entries.append((family,entropy,mode,language,label))
                stream.update(entropy); stream.update(json.dumps({'family':family,'mode':mode,'language':language,'label':{k:v for k,v in label.items() if k!='source'}},sort_keys=True).encode())
    example_target='1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'
    chapter_targets=['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W','1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']
    target_hashes={Base58Decoder.CheckDecode(a)[1:]:a for a in [example_target]+chapter_targets}
    configuration={'family':args.family,'source_candidates':len(candidates),'languages':languages,'indices':indices,'paths':paths,
                   'passphrase':args.passphrase,'candidate_stream_sha256':stream.hexdigest(),'wordlists_sha256':assets.hexdigest(),
                   'wallet_kernel_sha256':gpu.kernel_sha256,'gpu_kernel_sha256':cert.gpu_kernel_fingerprint(),
                   'targets':[example_target]+chapter_targets,'prefix_filter_used':False,'format':'compressed-P2PKH','enumeration':'candidate-language-entropy-v1'}
    cfg_tag=hashlib.sha256(json.dumps(configuration,sort_keys=True).encode()).hexdigest()[:16]
    state_path=HERE/f'historical-wallets-{args.family}-{cfg_tag}.json'
    old=json.loads(state_path.read_text()) if state_path.exists() else None
    if old and old['configuration']!=configuration: raise RuntimeError('Checkpoint configuration differs')
    rank=old['next_rank'] if old else 0; total=len(entries); stop=min(total,rank+args.limit) if args.limit else total
    per_seed=sum(1 if p['direct'] else len(indices) for p in paths)
    def record(matches=0):
        cert.atomic_json(state_path,{'configuration':configuration,'candidates_total':total,'next_rank':rank,
                         'derived_addresses':rank*per_seed,'complete':rank==total,'matches':matches,
                         'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    begin=time.perf_counter(); last=begin
    print(f'{state_path.name}: {total:,} seeds, {per_seed} addresses/seed; no MD5 hint filter',flush=True)
    while rank<stop:
        batch=entries[rank:min(rank+args.batch,stop)]
        words=[helper.mnemonic(e,language,lists) for _,e,_,language,_ in batch]
        seeds=pbkdf2_gpu.pbkdf2_hmac_sha512_gpu([helper.normalized_password(w) for w in words],[salt]*len(words))
        sampled=sorted({0,len(batch)//2,len(batch)-1})
        for k in sampled:
            if seeds[k]!=hashlib.pbkdf2_hmac('sha512',unicodedata.normalize('NFKD',words[k]).encode(),salt,2048,64): raise RuntimeError('Sampled independent PBKDF2 mismatch')
        for preset in paths:
            used_indices=[0] if preset['direct'] else indices
            hashes,keys,pubs=gpu.batch(seeds,preset['parent'],used_indices,preset['hardened'],preset['direct'])
            for k in sampled:
                for j,index in enumerate(used_indices):
                    node=Bip32Secp256k1.FromSeed(seeds[k]).DerivePath(full_path(preset['parent'],index,preset['hardened'],preset['direct']))
                    row=k*len(used_indices)+j; public=node.PublicKey().RawCompressed().ToBytes()
                    independent=hashlib.new('ripemd160',hashlib.sha256(public).digest()).digest()
                    if hashes[row].tobytes()!=independent or keys[row].tobytes()!=node.PrivateKey().Raw().ToBytes() or pubs[row].tobytes()!=public: raise RuntimeError('Sampled independent BIP32 key/public/hash160 mismatch')
            for row in range(len(hashes)):
                h=hashes[row].tobytes()
                if h not in target_hashes: continue
                k,j=divmod(row,len(used_indices)); family,entropy,mode,language,label=batch[k]
                address=target_hashes[h]
                if address not in ([example_target] if family=='example' else chapter_targets): continue
                path=full_path(preset['parent'],used_indices[j],preset['hardened'],preset['direct'])
                node=Bip32Secp256k1.FromSeed(seeds[k]).DerivePath(path); private=node.PrivateKey().Raw().ToBytes()
                public=node.PublicKey().RawCompressed().ToBytes()
                if hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(public).digest()).digest())!=address: raise RuntimeError('Hit failed independent validation')
                if hashlib.md5(label['source']).hexdigest()!=label['md5']: raise RuntimeError('Witness bytes differ from source MD5')
                dest=HERE/f'FOUND-historical-wallets-{family}.txt'; dest.write_bytes(label['source'])
                cert.atomic_json(dest.with_suffix('.json'),{'address':address,'path':path,'language':language,'mode':mode,
                                 'entropy':entropy.hex(),'mnemonic':words[k],'passphrase':args.passphrase,
                                 'private_wif':base58check_encode(b'\x80'+private+b'\x01'),
                                 'source_label':{a:b for a,b in label.items() if a!='source'}})
                record(matches=1); print(f'VERIFIED MATCH: {dest}',flush=True); return
        rank+=len(batch); record()
        now=time.perf_counter()
        if now-last>=20 or rank==stop:
            print(f'checked={rank:,}/{total:,} seeds; addresses={rank*per_seed:,}; no match; elapsed={now-begin:.1f}s',flush=True)
            last=now
    record(); print('COMPLETE finite family' if rank==total else 'LIMIT reached; checkpoint can resume',flush=True)


if __name__=='__main__': main()
