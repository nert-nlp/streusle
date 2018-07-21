#!/usr/bin/env python3

import os, sys, fileinput, re, json, argparse
from collections import defaultdict, Counter

from conllulex2json import load_sents
from supersenses import coarsen_pss

"""
Evaluation script for multiword expression (MWE) identification
and supersense disambiguation (also includes possessives).
Scores are broken down according to the type of expression
and the kind of supersense: noun, verb, or SNACS (which applies in English
to prepositions and possessives).
Pass the `-h` flag to see command-line usage information.

INPUT
=====

The first positional argument is the gold standard; subsequent arguments are system outputs,
and each of these must have a filename of the form BASENAME.goldid.{conllulex,json}
or BASENAME.autoid.{conllulex,json}.
Sentences must be in the same order in all files.

Consistency between tags and expressions in the input is assumed.
If the input is a JSON that has been generated by running conllulex2json.py,
it should be consistent; but if the JSON has been generated by other means,
care should be taken in interpreting the results.

OUTPUT
======

The following output formats are supported:

  * basic TSV: this is the default and most concise.
  * extended TSV, activated by the -x option: this is more detailed.
  * JSON, activated by the --json option: this is the most detailed.

It is recommended to view TSV output in a spreadsheet editor.

Results with gold (oracle) MWE identification (goldid) and automatic MWE identification (autoid)
are recorded separately; some evaluation criteria are scored as Accuracy
in the former case and Precision/Recall/F1-score in the latter case.
In the TSV file, if there are any goldid inputs, all the goldid columns will
be displayed first, and then all the autoid columns.

The following kinds of scores are measured within an experimental condition:

Tag-based scores
----------------

Each STREUSLE token has a tag that summarizes its lexical-semantic analysis:
whether it belongs to an MWE, what the expression's lexical category is,
and what the expression's supersense label is.
See documentation of LEXTAG at CONLLULEX.md.
Tag-based scores are denoted `Tags` in the results:

  * Accuracies of the token-level tag (`Full`) and subparts (`-Lexcat`, `-SS`, `-Lexcat -SS`).
    `-Lexcat` ignores the lexcat, attending only to the MWE position (BIO) and strength
    information and the supersense. `-SS` ignores the supersense, and so forth.

  * Link-based measures score MWE identification in a way that gives partial
    credit for partial expression matches. (These are described in Schneider et al., TACL 2014.)
    Precision/Recall/F1 are measured with weak links converted to strong links (`Link+`),
    weak links removed (`Link-`), and the average of those two measures (`LinkAvg`).
    These are the only scores reported by this script that take weak MWEs into account.
    They are measured twice: once for all MWEs, and once for gappy (discontinuous) MWEs only.
    The `GappyMWE`, `Link+`, and `Link-` scores are not shown in the basic TSV view.

Expression-based scores
-----------------------

Instead of being counted per orthographic token,
these are counted per (single-word or strong multiword) expression occurrence.
(Weak MWE groupings and lexcats are ignored by the expression-based measures.)

  * Identification (`ID`) is the Precision/Recall/F1 of identifying expression
    units (orthographic token groupings that constitute a single semantic unit).
    It only gives credit for exact matches.

  * `Labeled` refers to the identification of the expression units AND the correct
    supersense label. Matching is exact in both respects, except for SNACS
    when the -D option is passed to coarsen the labels (see psseval.py for details).
    For SNACS, `Role` and `Fxn` subscores are also provided to target the
    two parts of the supersense labeling; the `Labeled` criterion is stricter
    (requiring both role and function to be correct).

If the gold supersense label is `??`, the token is discarded
(not counted as a match, false positive or false negative,
regardless of whether it is predicted to have a supersense),
except from the all-labels `ID` score, where the supersense label is irrelevant.

Subscores are given based on the kind of supersense (`NOUN`, `VERB`, or `SNACS`)
and the size/shape of the expression (`SWE`: single-word expressions, `MWE`,
`ContigMWE`, `GappyMWE`, of which only `MWE` is presented in the basic TSV view).
In the TSV output the supersense subscores are arranged
horizontally and the size/shape subscores are arranged vertically.

@author: Nathan Schneider (@nschneid)
@since: 2018-07-19
"""

class Ratio(object):
    '''
    Fraction that prints both the ratio and the float value.
    (fractions.Fraction reduces e.g. 378/399 to 18/19. We want to avoid this.)
    '''
    def __init__(self, numerator, denominator):
        self._n = numerator
        self._d = denominator
    def __float__(self):
        return self._n / self._d if self._d!=0 else float('nan')
    def __str__(self):
        return f'{float(self):.1%}'
    def __repr__(self):
        return f'{self.numeratorS}/{self.denominatorS}={self:.1%}'
    def __add__(self, v):
        if v==0:
            return self
        if isinstance(v,Ratio) and self._d==v._d:
            return Ratio(self._n + v._n, self._d)
        return float(self)+float(v)
    def __mul__(self, v):
        return Ratio(self._n * float(v), self._d)
    def __truediv__(self, v):
        return Ratio(self._n / float(v) if float(v)!=0 else float('nan'), self._d)
    __rmul__ = __mul__
    @property
    def numerator(self):
        return self._n
    @property
    def numeratorS(self):
        return f'{self._n:.2f}' if isinstance(self._n, float) else f'{self._n}'
    @property
    def denominator(self):
        return self._d
    @property
    def denominatorS(self):
        return f'{self._d:.2f}' if isinstance(self._d, float) else f'{self._d}'

def f1(prec, rec):
    return 2*prec*rec/(prec+rec) if float(prec+rec)>0 else float('nan')

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
    assert len(gold)==len(pred),(gold,pred)
    c['N'] = len(gold)
    c['correct'] = len(gold & pred)
    assert len(gold - pred)==len(pred - gold)
    c['incorrect'] = len(gold - pred)
    return c


def eval_sent_tagging(sent, syssent, counts):
    goldtags = {tok["#"]: tuple((tok["lextag"]+'--').split('-', 2)) for tok in sent["toks"]}
    predtags = {tok["#"]: tuple((tok["lextag"]+'--').split('-', 2)) for tok in syssent["toks"]}
    c = counts['*', 'Tags']
    c['Full'] += compare_sets_Acc(goldtags.items(), predtags.items())
    c['-Lexcat'] += compare_sets_Acc({(k,mwe,ss) for k,(mwe,lc,ss) in goldtags.items()},
                                     {(k,mwe,ss) for k,(mwe,lc,ss) in predtags.items()})
    c['-SS'] += compare_sets_Acc({(k,mwe,lc) for k,(mwe,lc,ss) in goldtags.items()},
                                 {(k,mwe,lc) for k,(mwe,lc,ss) in predtags.items()})
    c['-Lexcat -SS'] += compare_sets_Acc({(k,mwe) for k,(mwe,lc,ss) in goldtags.items()},
                                         {(k,mwe) for k,(mwe,lc,ss) in predtags.items()})

    goldmwetags = [None]*len(goldtags)
    for i,(mwe,lc,ss) in goldtags.items():
        goldmwetags[i-1] = mwe
    predmwetags = [None]*len(predtags)
    for i,(mwe,lc,ss) in predtags.items():
        predmwetags[i-1] = mwe
    eval_sent_links(goldmwetags, predmwetags, counts)

RE_TAGGING = re.compile(r'^(O|B(o|b(i[_~])+|I[_~])*(I[_~])+)+$')
# don't support plain I and i
STRENGTH = {'I_': '_', 'I~': '~', 'i_': '_', 'i~': '~', 'B': None, 'b': None, 'O': None, 'o': None}
# don't support plain I and i

def form_groups(links):
    """
    >>> form_groups([(1, 2), (3, 4), (2, 5), (6, 8), (4, 7)])==[{1,2,5},{3,4,7},{6,8}]
    True
    """
    groups = []
    groupMap = {} # offset -> group containing that offset
    for a,b in links:
        assert a is not None and b is not None,links
        assert b not in groups,'Links not sorted left-to-right: '+repr((a,b))
        if a not in groupMap: # start a new group
            groups.append({a})
            groupMap[a] = groups[-1]
        assert b not in groupMap[a],'Redunant link?: '+repr((a,b))
        groupMap[a].add(b)
        groupMap[b] = groupMap[a]
    return groups

def eval_sent_links(goldmwetags, predmwetags, counts):
    """
    Construct links between consecutive MWE elements (strong or weak).
    Then compute link-based P, R, F under two conditions--with weak links
    removed, and with weak links converted to strong links--and average them.

    The provided MWE tag sequences are assumed to be valid;
    e.g. the expected behavior is undefined if a
    """
    # Verify the MWE tag sequence is valid
    assert len(goldmwetags)==len(predmwetags)>0
    assert RE_TAGGING.match(''.join(goldmwetags))
    assert RE_TAGGING.match(''.join(predmwetags))
    # Sequences such as B I~ O I~ and O b i_ O are invalid.

    # Construct links from BIO tags
    glinks, plinks = [], []
    g_last_BI, p_last_BI = None, None
    g_last_bi, p_last_bi = None, None
    for j,(goldTag,predTag) in enumerate(zip(goldmwetags, predmwetags)):
        assert goldTag in STRENGTH and predTag in STRENGTH

        if goldTag in {'I','I_','I~'}:
            glinks.append((g_last_BI, j, STRENGTH[goldTag]))
            g_last_BI = j
        elif goldTag=='B':
            g_last_BI = j
        elif goldTag in {'i','i_','i~'}:
            glinks.append((g_last_bi, j, STRENGTH[goldTag]))
            g_last_bi = j
        elif goldTag=='b':
            g_last_bi = j

        if predTag in {'I','I_','I~'}:
            plinks.append((p_last_BI, j, STRENGTH[predTag]))
            p_last_BI = j
        elif predTag=='B':
            p_last_BI = j
        elif predTag in {'i','i_','i~'}:
            plinks.append((p_last_bi, j, STRENGTH[predTag]))
            p_last_bi = j
        elif predTag=='b':
            p_last_bi = j

    # Count link overlaps
    for d in ('Link+', 'Link-'):    # Link+ = strengthen weak links, Link- = remove weak links

        # for strengthened or weakened scores
        glinks1 = [(a,b) for a,b,s in glinks if d=='Link+' or s=='_']
        plinks1 = [(a,b) for a,b,s in plinks if d=='Link+' or s=='_']
        ggroups1 = form_groups(glinks1)
        pgroups1 = form_groups(plinks1)

        # soft matching (in terms of links)
        # precision and recall are defined structurally, not simply in terms of
        # set overlap (PNumer does not necessarily equal RNumer), so compare_sets_PRF doesn't apply
        c = counts['MWE','Tags'][d]
        c['PNumer'] += sum(1 for a,b in plinks1 if any(a in grp and b in grp for grp in ggroups1))
        c['PDenom'] += len(plinks1)
        c['RNumer'] += sum(1 for a,b in glinks1 if any(a in grp and b in grp for grp in pgroups1))
        c['RDenom'] += len(glinks1)

        c = counts['GappyMWE','Tags'][d]
        # cross-gap links only
        c['PNumer'] += sum((1 if b-a>1 else 0) for a,b in plinks1 if any(a in grp and b in grp for grp in ggroups1))
        c['PDenom'] += sum((1 if b-a>1 else 0) for a,b in plinks1)
        c['RNumer'] += sum((1 if b-a>1 else 0) for a,b in glinks1 if any(a in grp and b in grp for grp in pgroups1))
        c['RDenom'] += sum((1 if b-a>1 else 0) for a,b in glinks1)


SS_CLASSES = {
    '*': lambda e: True,
    'AnySS': lambda e: e['ss'],
    'NoSS': lambda e: not e['ss'],
    'NOUN': lambda e: (e['ss'] or '').startswith('n.'),
    'VERB': lambda e: (e['ss'] or '').startswith('v.'),
    'SNACS': lambda e: (e['ss'] or '').startswith('p.'),
    'POSS': lambda e: (e['ss'] or '').startswith('p.') and e['lexcat'] in {'PRON.POSS', 'POSS'},
    'P,PP': lambda e: (e['ss'] or '').startswith('p.') and e['lexcat'] in {'P', 'PP'},
    'P': lambda e: (e['ss'] or '').startswith('p.') and e['lexcat']=='P',
    'PP': lambda e: (e['ss'] or '').startswith('p.') and e['lexcat']=='PP',
    'INF': lambda e: (e['ss'] or '').startswith('p.') and e['lexcat']=='INF.P',
}
SNACS_CLASSES = {'SNACS', 'POSS', 'ADP', 'P', 'PP', 'INF'}
SHAPE_CLASSES = {
    '*': lambda e: True,
    'SWE': lambda e: len(e['toknums']) == 1,
    'MWE': lambda e: len(e['toknums']) > 1,
    'ContigMWE': lambda e: max(e['toknums'])-min(e['toknums'])+1 == len(e['toknums']) > 1,
    'GappyMWE': lambda e: max(e['toknums'])-min(e['toknums'])+1 > len(e['toknums']) > 1,
}

def eval_sent_by_classes(sent, syssent, shapeclass, ssclass, counts, compare_sets):
    goldunits = {tuple(e['toknums']): (e['lexcat'], e['ss'], e['ss2']) for e in list(   sent['swes'].values())+list(   sent['smwes'].values()) \
        if (SHAPE_CLASSES[shapeclass](e) and SS_CLASSES[ssclass](e)) or (ssclass!='*' and e['ss']=='??')}
    predunits = {tuple(e['toknums']): (e['lexcat'], e['ss'], e['ss2']) for e in list(syssent['swes'].values())+list(syssent['smwes'].values()) \
        if (SHAPE_CLASSES[shapeclass](e) and SS_CLASSES[ssclass](e))}
    c = counts[shapeclass, ssclass]

    if ssclass=='*':
        c['ID'] += compare_sets(set(goldunits.keys()), set(predunits.keys()))

    # special case: when we care about supersense labeling,
    # discard gold=?? tokens regardless of their predicted label
    for k,(lc,r,f) in list(goldunits.items()):
        if r=='??':
            if k in predunits:
                del predunits[k]
            del goldunits[k]


    if ssclass!='*':
        c['ID'] += compare_sets(set(goldunits.keys()), set(predunits.keys()))

    c['Labeled'] += compare_sets({(k,r,f) for k,(lc,r,f) in goldunits.items()},
                                 {(k,r,f) for k,(lc,r,f) in predunits.items()})
    if ssclass in SNACS_CLASSES:
        c['Role'] += compare_sets({(k,r) for k,(lc,r,f) in goldunits.items()},
                                  {(k,r) for k,(lc,r,f) in predunits.items()})
        c['Fxn'] +=  compare_sets({(k,f) for k,(lc,r,f) in goldunits.items()},
                                  {(k,f) for k,(lc,r,f) in predunits.items()})

def eval_sys(sysF, gold_sents, ss_mapper):
    goldid = (sysF.name.split('.')[-2]=='goldid')
    if not goldid and sysF.name.split('.')[-2]!='autoid':
        raise ValueError(f'File path of system output not specified for gold vs. auto identification of units to be labeled: {sysF.name}')

    compare_sets = compare_sets_Acc if goldid else compare_sets_PRF

    scores = defaultdict(lambda: defaultdict(Counter))

    for iSent,syssent in enumerate(load_sents(sysF, ss_mapper=ss_mapper)):
        sent = gold_sents[iSent]
        assert sent['sent_id']==syssent['sent_id']

        eval_sent_tagging(sent, syssent, scores)
        for shapeclass in SHAPE_CLASSES:
            for ssclass in SS_CLASSES:
                eval_sent_by_classes(sent, syssent, shapeclass, ssclass, scores, compare_sets)

    for k in scores:
        if k[1] =='Tags':
            if k[0]=='*':   # k is ('*', 'Tags')
                for subscore in ('Full', '-Lexcat', '-SS', '-Lexcat -SS'):
                    c = scores[k][subscore]
                    assert scores[k][subscore]['N']>0,(k,subscore,scores[k][subscore])
                    c['Acc'] = Ratio(c['correct'], c['N'])
            elif k[0] in ('MWE', 'GappyMWE'):
                for subscore in ('Link+', 'Link-'):
                    c = scores[k][subscore]
                    c['P'] = Ratio(c['PNumer'], c['PDenom'])
                    c['R'] = Ratio(c['RNumer'], c['RDenom'])
                    c['F'] = f1(c['P'], c['R'])
                for m in ('P', 'R', 'F'):
                    # strength averaging
                    avg = (scores[k]['Link+'][m]+scores[k]['Link-'][m])/2   # float
                    # construct a ratio by averaging the denominators (this gives insight into underlying recall-denominators)
                    denom = (scores[k]['Link+'][m].denominator+scores[k]['Link-'][m].denominator)/2   # float
                    scores[k]['LinkAvg'][m] = Ratio(avg*denom, denom)
        elif goldid:  # assuming goldid means gold identification of spans & kind of supersense
            for subscore in ('Role','Fxn','Labeled'):
                c = scores[k][subscore]
                assert scores[k][subscore]['N']>0,(k,subscore,scores[k][subscore])
                c['Acc'] = Ratio(c['correct'], c['N'])
        else:
            for subscore in ('ID','Role','Fxn','Labeled'):
                c = scores[k][subscore]
                c['P'] = Ratio(c['correct'], c['Pdenom'])
                c['R'] = Ratio(c['correct'], c['Rdenom'])
                c['F'] = f1(c['P'], c['R'])

    assert len(gold_sents)==iSent+1,f'Mismatch in number of sentences: {len(gold_sents)} gold, {iSent+1} system from {sysFP}'

    return scores


def to_tsv(all_sys_scores, depth, mode=None):
    # the structure of the TSV (default mode)
    blocks = {k: {'gid': {}, 'aid': {}} for k in SHAPE_CLASSES} # gid = gold ID, aid = auto ID
    blocks['*']['aid']['Tags'] = blocks['*']['gid']['Tags'] = {'Full': ('Acc',), '-Lexcat': ('Acc',), '-SS': ('Acc',)}
    blocks['MWE']['aid']['Tags'] = {'LinkAvg': ('P', 'R', 'F')}
    blocks['GappyMWE']['aid']['Tags'] = {'LinkAvg': ('P', 'R', 'F')}
    blocks['SWE']['aid']['Tags'] = {'': ('', '', '')}   # spacing so subsequent columns will align properly
    blocks['ContigMWE']['aid']['Tags'] = {'': ('', '', '')}   # spacing so subsequent columns will align properly
    for k in blocks:
        blocks[k]['gid']['*'] = {'Labeled': ('Acc',)}
        blocks[k]['gid']['NOUN'] = {'Labeled': ('Acc',)}
        blocks[k]['gid']['VERB'] = {'Labeled': ('Acc',)}
        blocks[k]['gid']['SNACS'] = {'Labeled': ('Acc',), 'Role': ('Acc',), 'Fxn': ('Acc',)}
        if mode=='x':
            blocks[k]['gid']['P'] = blocks[k]['gid']['SNACS']
            blocks[k]['gid']['PP'] = blocks[k]['gid']['SNACS']
            blocks[k]['gid']['POSS'] = blocks[k]['gid']['SNACS']
            blocks[k]['gid']['INF'] = blocks[k]['gid']['SNACS']
        blocks[k]['aid']['*'] = {'ID': ('P', 'R', 'F'), 'Labeled': ('P', 'R', 'F')}
        blocks[k]['aid']['NOUN'] = {}
        if mode=='x':
            blocks[k]['aid']['NOUN']['ID'] = ('P', 'R', 'F')
            blocks[k]['aid']['NOUN']['Labeled'] = ('P', 'R', 'F')
        else:
            blocks[k]['aid']['NOUN']['Labeled'] = ('F')
        blocks[k]['aid']['VERB'] = blocks[k]['aid']['NOUN']
        blocks[k]['aid']['SNACS'] = dict(blocks[k]['aid']['NOUN'])
        blocks[k]['aid']['SNACS']['Role'] = ('F',) if mode!='x' else ('P', 'R', 'F')
        blocks[k]['aid']['SNACS']['Fxn'] = ('F',) if mode!='x' else ('P', 'R', 'F')
        if mode=='x':
            blocks[k]['aid']['P'] = blocks[k]['aid']['SNACS']
            blocks[k]['aid']['PP'] = blocks[k]['aid']['SNACS']
            blocks[k]['aid']['POSS'] = blocks[k]['aid']['SNACS']
            blocks[k]['aid']['INF'] = blocks[k]['aid']['SNACS']

    shape_classes = dict(SHAPE_CLASSES)
    if mode!='x':
        del shape_classes['SWE']
        del shape_classes['ContigMWE']
        del shape_classes['GappyMWE']

    ngoldidcols = max(sum(1 for g in blocks[k]['gid'] for h in blocks[k]['gid'][g]) for k in shape_classes)
    nautoidcols = max(sum(1 for g in blocks[k]['aid'] for h in blocks[k]['aid'][g]) for k in shape_classes)
    anygoldid = any(scores for scores in all_sys_scores.values() if scores[0])
    if anygoldid:
        # header 1: unit identification status
        print('\tGOLD ID' + '\t'*ngoldidcols + '\t\tAUTO ID' + '\t'*nautoidcols)
        assert False,'Gold ID columns not yet supported'
    idstatuses = ('gid','aid') if anygoldid else ('aid',)
    firstK = True
    for k in shape_classes:

        if firstK:
            # header 2: class
            print('\t', end='')
            for a in idstatuses:
                for g in blocks[k][a]:
                    if g=='*':
                        print('All Strong Expr. Labels (incl. no supersense)', end='')
                    elif g=='SNACS':
                        print(f'SNACS (D={depth})', end='')
                    else:
                        print(g, end='')

                    for h in blocks[k][a][g]:
                        for m in blocks[k][a][g][h]:
                            print('\t', end='')
                print('\t', end='')
            print()
            firstK = False

        # header 3: subscore
        print((k if k!='*' else 'All Expression Sizes'), end='\t')
        for a in idstatuses:
            for g in blocks[k][a]:
                for h in blocks[k][a][g]:
                    print(h, end='')
                    for m in blocks[k][a][g][h]:
                        print('\t', end='')
            print('\t', end='')
        print()

        # header 4: measure (N, Acc or P, R, F)
        print('='*(len(k) if k!='*' else 10), end='\t')
        sys1scores = dict(zip(['gid','aid'],list(all_sys_scores.values())[0]))
        for a in idstatuses:
            for g in blocks[k][a]:
                for h in blocks[k][a][g]:
                    for m in blocks[k][a][g][h]:
                        if m=='Acc' or m=='R':
                            print(f'{m} /{sys1scores[a][k,g][h][m].denominator}', end='\t')
                        elif m=='F' and 'R' not in blocks[k]['aid'][g][h]:
                            print(f'F (R /{sys1scores[a][k,g][h]["R"].denominator})', end='\t')
                        else:
                            print(m, end='\t')
            print('\t', end='')
        print()

        # values
        for sys,(gidscores,aidscores) in all_sys_scores.items():
            sysscores = {'gid': gidscores, 'aid': aidscores}
            print(sys, end='\t')
            for a in idstatuses:
                for g in blocks[k][a]:
                    for h in blocks[k][a][g]:
                        for m in blocks[k][a][g][h]:
                            v = sysscores[a][k,g][h][m] if m else ''
                            print(v, end='\t')
                print('\t', end='')
            print()
        print()

def to_json(all_sys_scores, depth, mode=None):
    scores = dict(all_sys_scores)
    scores["_meta"] = {"depth": depth}
    print(json.dumps(scores))

def main(args):
    goldF = args.goldfile
    sysFs = args.sysfile

    ss_mapper = lambda ss: coarsen_pss(ss, args.depth) if ss.startswith('p.') else ss

    # Load gold data
    gold_sents = list(load_sents(goldF, ss_mapper=ss_mapper))

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
    args.output_format(all_sys_scores, depth=args.depth, mode=args.output_mode)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Evaluate system output for preposition supersense disambiguation against a gold standard.')
    parser.add_argument('goldfile', type=argparse.FileType('r'),
                        help='gold standard .conllulex or .json file')
    parser.add_argument('sysfile', type=argparse.FileType('r'), nargs='+',
                        help='system prediction file: BASENAME.{goldid,autoid}.{conllulex,json}')
    parser.add_argument('--depth', metavar='D', type=int, choices=range(1,5), default=4,
                        help='depth of hierarchy at which to cluster SNACS supersense labels (default: 4, i.e. no collapsing)')
    # parser.add_argument('--prec-rank', metavar='K', type=int, default=1,
    #                     help='precision@k rank (default: 1)')
    output = parser.add_mutually_exclusive_group()
    output.add_argument('--json', dest='output_format', action='store_const', const=to_json, default=to_tsv,
                        help='output as JSON (default: output as TSV)')
    output.add_argument('-x', '--extended', dest='output_mode', action='store_const', const='x', default='',
                        help='more detailed TSV output')

    args = parser.parse_args()
    main(args)
