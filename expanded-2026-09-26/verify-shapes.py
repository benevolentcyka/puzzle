"""Compare new exact-byte shapes to the previously tested chapter generator."""
import importlib.util
import itertools
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    chapter=load('subset_runner',HERE/'chapter-subsets.py')
    prior=load('prior_shapes',ROOT/'followup-2026-09-26/language-settings-gpu.py')
    known={(label['start'],label['spaces'],label['join']):label['source'] for _,label in prior.chapter_candidates()
           if label['group_mask']==15 and not label['tail']}
    checked=0
    for start,spaces,join in itertools.product([0,1,3],['keep','nbsp-space','trim'],['lf','crlf']):
        source,positions=chapter.chapter_source(join,start,spaces,'ffww','match')
        if source!=known[(start,spaces,join)] or len(positions)!=32: raise RuntimeError('Independent shape byte comparison failed')
        checked+=1
    report={'passed':True,'prior_generator_byte_comparisons':checked,'previous_known_shapes':576}
    (HERE/'shape-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__': main()
