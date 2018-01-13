#!/usr/bin/env python3

import os, sys, fileinput, re, json, argparse
from collections import defaultdict, Counter

from conllulex2json import load_sents
from supersenses import coarsen_pss

"""
Evaluation script for adposition supersense disambiguation (also includes possessives).
With --json, outputs result as JSON; otherwise outputs a TSV file for viewing in a spreadsheet editor.
The first positional argument is the gold standard; subsequent arguments are system outputs,
and each of these must have a filename of the form BASENAME.goldid.{conllulex,json}
or BASENAME.autoid.{conllulex,json}.
Sentences must be in the same order in all files.

Invoke with -h to see command-line options.

@author: Nathan Schneider (@nschneid)
@since: 2017-12-29
"""

def f1(prec, rec):
    return 2*prec*rec/(prec+rec) if (prec+rec)>0 else float('nan')

def compare_sets_PRF(gold, pred):
    c = Counter()
    c['correct'] = len(gold & pred)
    c['missed'] = len(gold - pred)
    c['extra'] = len(pred - gold)
    c['Pdenom'] = len(pred)
    c['Rdenom'] = len(gold)
    return c

def compare_sets_Acc(gold, pred):
    c = Counter()
    assert len(gold)==len(pred)
    c['N'] = len(gold)
    c['correct'] = len(gold & pred)
    assert len(gold - pred)==len(pred - gold)
    c['incorrect'] = len(gold - pred)
    return c

def eval_sys(sysF, gold_sents, ss_mapper):
    goldid = (sysF.name.split('.')[-2]=='goldid')
    if not goldid and sysF.name.split('.')[-2]!='autoid':
        raise ValueError(f'File path of system output not specified for gold vs. auto identification of units to be labeled: {sysF.name}')

    compare_sets = compare_sets_Acc if goldid else compare_sets_PRF

    scores = {'All': defaultdict(Counter), 'MWE': defaultdict(Counter), 'MWP': defaultdict(Counter)}

    for iSent,syssent in enumerate(load_sents(sysF, ss_mapper=ss_mapper)):
        sent = gold_sents[iSent]
        assert sent['sent_id']==syssent['sent_id']

        # all units with a PSS label
        c = scores['All']
        goldunits = sent['punits']
        predunits = {tuple(e['toknums']): (e['lexcat'], e['ss'], e['ss2']) for e in list(syssent['swes'].values())+list(syssent['smwes'].values()) if e['ss'] and e['ss'].startswith('p.')}
        c['ID'] += compare_sets(set(goldunits.keys()), set(predunits.keys()))
        c['Role,Fxn'] += compare_sets({(k,r,f) for k,(lc,r,f) in goldunits.items()},
                                      {(k,r,f) for k,(lc,r,f) in predunits.items()})
        c['Role'] +=     compare_sets({(k,r) for k,(lc,r,f) in goldunits.items()},
                                      {(k,r) for k,(lc,r,f) in predunits.items()})
        c['Fxn'] +=      compare_sets({(k,f) for k,(lc,r,f) in goldunits.items()},
                                      {(k,f) for k,(lc,r,f) in predunits.items()})


        # MWEs only
        c = scores['MWE']
        goldunits = {k: v for k,v in goldunits.items() if len(k)>1}
        predunits = {k: v for k,v in predunits.items() if len(k)>1}
        c['ID'] += compare_sets(set(goldunits.keys()), set(predunits.keys()))
        c['Role,Fxn'] += compare_sets({(k,r,f) for k,(lc,r,f) in goldunits.items()},
                                      {(k,r,f) for k,(lc,r,f) in predunits.items()})
        c['Role'] +=     compare_sets({(k,r) for k,(lc,r,f) in goldunits.items()},
                                      {(k,r) for k,(lc,r,f) in predunits.items()})
        c['Fxn'] +=      compare_sets({(k,f) for k,(lc,r,f) in goldunits.items()},
                                      {(k,f) for k,(lc,r,f) in predunits.items()})

        # multiword adpositions only: note this requires the lexcat to be predicted
        c = scores['MWP']
        goldunits = {k: v for k,v in goldunits.items() if v[0]!='PP'}
        predunits = {k: v for k,v in predunits.items() if v[0]!='PP'}
        c['ID'] += compare_sets(set(goldunits.keys()), set(predunits.keys()))
        c['Role,Fxn'] += compare_sets({(k,r,f) for k,(lc,r,f) in goldunits.items()},
                                      {(k,r,f) for k,(lc,r,f) in predunits.items()})
        c['Role'] +=     compare_sets({(k,r) for k,(lc,r,f) in goldunits.items()},
                                      {(k,r) for k,(lc,r,f) in predunits.items()})
        c['Fxn'] +=      compare_sets({(k,f) for k,(lc,r,f) in goldunits.items()},
                                      {(k,f) for k,(lc,r,f) in predunits.items()})

    for k in ('All','MWE','MWP'):
        if goldid:
            for criterion in ('Role','Fxn','Role,Fxn'):
                c = scores[k][criterion]
                assert scores[k][criterion]['N']>0,(k,criterion,scores[k][criterion])
                c['Acc'] = c['correct'] / c['N']
        else:
            for criterion in ('ID','Role','Fxn','Role,Fxn'):
                c = scores[k][criterion]
                c['P'] = c['correct'] / c['Pdenom']
                c['R'] = c['correct'] / c['Rdenom']
                c['F'] = f1(c['P'], c['R'])

    assert len(gold_sents)==iSent+1,f'Mismatch in number of sentences: {len(gold_sents)} gold, {iSent+1} system from {sysFP}'

    return scores

def to_tsv(all_sys_scores, depth):
    for k in ('All','MWE','MWP'):
        print(k)
        print('D='+str(depth)+'\tGold ID:\tRole\tFxn\tRole,Fxn\t\tID\t\t\t\tRole\t\t\t\tFxn\t\t\t\tRole,Fxn\t\t')
        print('Sys\tN\tAcc\tAcc\tAcc' + '\t\tP\tR\tF'*4)
        for sys,(gidscores,aidscores) in all_sys_scores.items():
            print(sys, end='\t')
            print(gidscores[k]["Role"]["N"], end='\t')
            for criterion in ('Role', 'Fxn', 'Role,Fxn'):
                print(f'{gidscores[k][criterion]["Acc"]}', end='\t')
            print('', end='\t')
            for criterion in ('ID', 'Role', 'Fxn', 'Role,Fxn'):
                prf = aidscores[k][criterion]
                print(f'{prf["P"]}\t{prf["R"]}\t{prf["F"]}\t', end='\t')
            print()
        print()

def to_json(all_sys_scores, depth):
    scores = dict(all_sys_scores)
    scores["_meta"] = {"depth": depth}
    print(json.dumps(scores))

def main(args):
    goldF = args.goldfile
    sysFs = args.sysfile

    ss_mapper = lambda ss: coarsen_pss(ss, args.depth) if ss.startswith('p.') else ss

    # Load gold data
    gold_sents = list(load_sents(goldF, ss_mapper=ss_mapper))
    for sent in gold_sents:
        sent['punits'] = {tuple(e['toknums']): (e['lexcat'], e['ss'], e['ss2']) for e in list(sent['swes'].values())+list(sent['smwes'].values()) if e['ss'] and e['ss'].startswith('p.')}

    all_sys_scores = {}
    for sysF in sysFs:
        sysscores = eval_sys(sysF, gold_sents, ss_mapper)
        syspath = sysF.name
        basename = syspath.rsplit('.', 2)[0]
        if basename not in all_sys_scores:
            all_sys_scores[basename] = [defaultdict(lambda: defaultdict(Counter)),defaultdict(lambda: defaultdict(Counter))]
        if syspath.split('.')[-2]=='goldid':
            all_sys_scores[basename][0] = sysscores
        else:
            all_sys_scores[basename][1] = sysscores

    # Print output
    args.output_format(all_sys_scores, depth=args.depth)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Evaluate system output for preposition supersense disambiguation against a gold standard.')
    parser.add_argument('goldfile', type=argparse.FileType('r'),
                        help='gold standard .conllulex or .json file')
    parser.add_argument('sysfile', type=argparse.FileType('r'), nargs='+',
                        help='system prediction file: BASENAME.{goldid,autoid}.{conllulex,json}')
    parser.add_argument('--depth', metavar='D', type=int, choices=range(1,5), default=4,
                        help='depth of hierarchy at which to cluster supersense labels (default: 4, i.e. no collapsing)')
    # parser.add_argument('--prec-rank', metavar='K', type=int, default=1,
    #                     help='precision@k rank (default: 1)')
    parser.add_argument('--json', dest='output_format', action='store_const', const=to_json, default=to_tsv,
                        help='output as JSON (default: output as TSV)')

    args = parser.parse_args()
    main(args)
