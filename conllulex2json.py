#!/usr/bin/env python3

import os, sys, fileinput, re, json
from collections import defaultdict
from itertools import chain

from lexcatter import supersenses_for_lexcat, ALL_LEXCATS
from tagging import sent_tags
from mwerender import render

"""
Defines a function to read a .conllulex file sentence-by-sentence into a data structure.
If the script is called directly, outputs the data as JSON.
Also performs validation checks on the input.

@author: Nathan Schneider (@nschneid)
@since: 2017-12-29
"""

def load_sents(inF, morph_syn=True, misc=True, ss_mapper=None):
    """Given a .conllulex file, return an iterator over sentences.

    @param morph_syn: Whether to include CoNLL-U morphological features
    and syntactic dependency relations. POS tags and lemmas are always included.
    @param misc: Whether to include the CoNLL-U miscellaneous column.
    @param ss_mapper: A function to apply to supersense labels to replace them
    in the returned data structure. Applies to all supersense labels (nouns,
    verbs, prepositions). Not applied if the supersense slot is empty.
    """

    lc_tbd = 0

    def _postproc_sent(sent):
        nonlocal lc_tbd

        # check that tokens are numbered from 1, in order
        for i,tok in enumerate(sent['toks'], 1):
            assert tok['#']==i

        # check that MWEs are numbered from 1
        # fix_mwe_numbering.py was written to correct this
        for i,(k,mwe) in enumerate(sorted(chain(sent['smwes'].items(), sent['wmwes'].items()), key=lambda x: int(x[0])), 1):
            assert int(k)==i,(sent['sent_id'],i,k,mwe)

        # check that lexical & weak MWE lemmas are correct
        for lexe in chain(sent['swes'].values(), sent['smwes'].values()):
            assert lexe['lexlemma']==' '.join(sent['toks'][i-1]['lemma'] for i in lexe['toknums']),(lexe,sent['toks'][lexe['toknums'][0]-1])
            lc = lexe['lexcat']
            if lc.endswith('!@'): lc_tbd += 1
            valid_ss = supersenses_for_lexcat(lc)
            ss, ss2 = lexe['ss'], lexe['ss2']
            if valid_ss:
                if ss=='??':
                    assert ss2 is None
                elif ss not in valid_ss or (lc in ('N','V'))!=(ss2 is None) or (ss2 is not None and ss2 not in valid_ss):
                    print('Invalid supersense(s) in lexical entry:', lexe, file=sys.stderr)
            else:
                assert ss is None and ss2 is None,lexe

        # check lexcat on single-word expressions
        for swe in sent['swes'].values():
            tok = sent['toks'][swe['toknums'][0]-1]
            upos, xpos = tok['upos'], tok['xpos']
            lc = swe['lexcat']
            if lc.endswith('!@'): continue
            assert lc in ALL_LEXCATS,(sent['sent_id'],tok)
            if (xpos=='TO')!=lc.startswith('INF'):
                assert upos=='SCONJ' and swe['lexlemma']=='for',(sent['sent_id'],swe,tok)
            if (upos in ('NOUN', 'PROPN'))!=(lc=='N'):
                try:
                    assert upos in ('SYM','X') or (lc in ('PRON','DISC')),(sent['sent_id'],swe,tok)
                except AssertionError:
                    print('Suspicious lexcat/POS combination:', sent['sent_id'], swe, tok, file=sys.stderr)
            if (upos=='AUX')!=(lc=='AUX'):
                assert tok['lemma']=='be' and lc=='V',(sent['sent_id'],tok)    # copula has upos=AUX
            if (upos=='VERB')!=(lc=='V'):
                if lc=='ADJ':
                    print('Word treated as VERB in UD, ADJ for supersenses:', sent['sent_id'], tok['word'], file=sys.stderr)
                else:
                    assert tok['lemma']=='be' and lc=='V',(sent['sent_id'],tok)    # copula has upos=AUX
            if upos=='PRON':
                assert lc=='PRON' or lc=='PRON.POSS',(sent['sent_id'],tok)
            if lc=='ADV':
                assert upos=='ADV' or upos=='PART',(sent['sent_id'],tok)    # PART is for negations
            assert lc!='PP',('PP should only apply to strong MWEs',sent['sent_id'],tok)
        for smwe in sent['smwes'].values():
            assert len(smwe['toknums'])>1
        for wmwe in sent['wmwes'].values():
            assert len(wmwe['toknums'])>1,(sent['sent_id'],wmwe)
            assert wmwe['lexlemma']==' '.join(sent['toks'][i-1]['lemma'] for i in wmwe['toknums']),(wmwe,sent['toks'][wmwe['toknums'][0]-1])
        # we already checked that noninitial tokens in an MWE have _ as their lemma

        # check lextags
        smweGroups = [smwe['toknums'] for smwe in sent['smwes'].values()]
        wmweGroups = [wmwe['toknums'] for wmwe in sent['wmwes'].values()]
        tagging = sent_tags(len(sent['toks']), sent['mwe'], smweGroups, wmweGroups)
        for tok,tag in zip(sent['toks'],tagging):
            fulllextag = tag
            if tok['smwe']:
                smweNum, position = tok['smwe']
                lexe = sent['smwes'][smweNum]
            else:
                position = None
                lexe = sent['swes'][tok['#']]

            if position is None or position==1:
                lexcat = lexe['lexcat']
                fulllextag += '-'+lexcat
                ss1, ss2 = lexe['ss'], lexe['ss2']
                if ss1 is not None:
                    assert ss1
                    fulllextag += '-'+ss1
                    if ss2 is not None and ss2!=ss1:
                        assert ss2
                        fulllextag += '|'+ss2
                if tok['wmwe']:
                    wmweNum, position = tok['wmwe']
                    wmwe = sent['wmwes'][wmweNum]
                    wcat = wmwe['lexcat']
                    if wcat and position==1:
                        fulllextag += '+'+wcat

            assert tok['lextag']==fulllextag,(sent['sent_id'],fulllextag,tok)

        # check rendered MWE string
        s = render([tok['word'] for tok in sent['toks']],
                   smweGroups, wmweGroups)
        if sent['mwe']!=s:
            caveat = ' (may be due to simplification)' if '$1' in sent['mwe'] else ''
            print(f'MWE string mismatch{caveat}:', s,sent['mwe'],sent['sent_id'], file=sys.stderr)

    if ss_mapper is None:
        ss_mapper = lambda ss: ss

    sent = {}
    for ln in inF:
        if not ln.strip():
            if sent:
                _postproc_sent(sent)
                yield sent
                sent = {}
            continue

        ln = ln.strip()

        if ln.startswith('#'):
            if ln.startswith('# newdoc '): continue
            m = re.match(r'^# (\w+) = (.*)$', ln)
            k, v = m.group(1), m.group(2)
            assert k not in ('toks', 'swes', 'smwes', 'wmwes')
            sent[k] = v
        else:
            if 'toks' not in sent:
                sent['toks'] = []   # excludes ellipsis tokens, so they don't interfere with indexing
                sent['etoks'] = []  # ellipsis tokens only
                sent['swes'] = defaultdict(lambda: {'lexlemma': None, 'lexcat': None, 'ss': None, 'ss2': None, 'toknum': None})
                sent['smwes'] = defaultdict(lambda: {'lexlemma': None, 'lexcat': None, 'ss': None, 'ss2': None, 'toknums': []})
                sent['wmwes'] = defaultdict(lambda: {'lexlemma': None, 'toknums': []})
            assert ln.count('\t')==18,ln

            cols = ln.split('\t')
            conllu_cols = cols[:10]
            lex_cols = cols[10:]

            # Load CoNLL-U columns

            tok = {}
            tokNum = conllu_cols[0]
            isEllipsis = re.match(r'^\d+$', tokNum) is None
            if isEllipsis:  # ellipsis node indices are like 24.1
                part1, part2 = tokNum.split('.')
                part1 = int(part1)
                part2 = int(part2)
                tokNum = (part1, part2, tokNum) # ellipsis token offset is a tuple. include the string for convenience
            else:
                tokNum = int(tokNum)
            tok['#'] = tokNum
            tok['word'], tok['lemma'], tok['upos'], tok['xpos'] = conllu_cols[1:5]
            assert tok['lemma']!='_' and tok['upos']!='_',tok
            if morph_syn:
                tok['feats'], tok['head'], tok['deprel'], tok['edeps'] = conllu_cols[5:9]
                if tok['head']=='_':
                    assert isEllipsis
                    tok['head'] = None
                else:
                    tok['head'] = int(tok['head'])
                if tok['deprel']=='_':
                    assert isEllipsis
                    tok['deprel'] = None
            if misc:
                tok['misc'] = conllu_cols[9]
            for nullable_conllu_fld in ('xpos', 'feats', 'edeps', 'misc'):
                if nullable_conllu_fld in tok and tok[nullable_conllu_fld]=='_':
                    tok[nullable_conllu_fld] = None

            if not isEllipsis:
                # Load STREUSLE-specific columns

                tok['smwe'], tok['lexcat'], tok['lexlemma'], tok['ss'], tok['ss2'], \
                    tok['wmwe'], tok['wcat'], tok['wlemma'], tok['lextag'] = lex_cols

                # map the supersenses in the lextag
                lt = tok['lextag']
                for m in re.finditer(r'\b[a-z]\.[A-Za-z/-]+', tok['lextag']):
                    lt = lt.replace(m.group(0), ss_mapper(m.group(0)))
                for m in re.finditer(r'\b([a-z]\.[A-Za-z/-]+)\|\1\b', lt):
                    # e.g. p.Locus|p.Locus due to abstraction of p.Goal|p.Locus
                    lt = lt.replace(m.group(0), m.group(1)) # simplify to p.Locus
                tok['lextag'] = lt

                if tok['smwe']!='_':
                    smwe_group, smwe_position = list(map(int, tok['smwe'].split(':')))
                    tok['smwe'] = smwe_group, smwe_position
                    sent['smwes'][smwe_group]['toknums'].append(tokNum)
                    assert sent['smwes'][smwe_group]['toknums'].index(tokNum)==smwe_position-1,(tok['smwe'],sent['smwes'])
                    if smwe_position==1:
                        assert ' ' in tok['lexlemma']
                        sent['smwes'][smwe_group]['lexlemma'] = tok['lexlemma']
                        assert tok['lexcat'] and tok['lexcat']!='_'
                        sent['smwes'][smwe_group]['lexcat'] = tok['lexcat']
                        sent['smwes'][smwe_group]['ss'] = ss_mapper(tok['ss']) if tok['ss']!='_' else None
                        sent['smwes'][smwe_group]['ss2'] = ss_mapper(tok['ss2']) if tok['ss2']!='_' else None
                    else:
                        assert ' ' not in tok['lexlemma']
                        assert tok['lexcat']=='_'
                else:
                    tok['smwe'] = None
                    assert tok['lexlemma']==tok['lemma'],(sent['sent_id'],tok['lexlemma'],tok['lemma'])
                    sent['swes'][tokNum]['lexlemma'] = tok['lexlemma']
                    assert tok['lexcat'] and tok['lexcat']!='_'
                    sent['swes'][tokNum]['lexcat'] = tok['lexcat']
                    sent['swes'][tokNum]['ss'] = ss_mapper(tok['ss']) if tok['ss']!='_' else None
                    sent['swes'][tokNum]['ss2'] = ss_mapper(tok['ss2']) if tok['ss2']!='_' else None
                    sent['swes'][tokNum]['toknums'] = [tokNum]
                del tok['lexlemma']
                del tok['lexcat']
                del tok['ss']
                del tok['ss2']

                if tok['wmwe']!='_':
                    wmwe_group, wmwe_position = list(map(int, tok['wmwe'].split(':')))
                    tok['wmwe'] = wmwe_group, wmwe_position
                    sent['wmwes'][wmwe_group]['toknums'].append(tokNum)
                    assert sent['wmwes'][wmwe_group]['toknums'].index(tokNum)==wmwe_position-1,(sent['sent_id'],tokNum,tok['wmwe'],sent['wmwes'])
                    if wmwe_position==1:
                        assert tok['wlemma'] and tok['wlemma']!='_',(sent['sent_id'],tokNum,tok)
                        sent['wmwes'][wmwe_group]['lexlemma'] = tok['wlemma']
                        #assert tok['wcat'] and tok['wcat']!='_'    # eventually it would be good to have a category for every weak expression
                        sent['wmwes'][wmwe_group]['lexcat'] = tok['wcat'] if tok['wcat']!='_' else None
                    else:
                        assert tok['wlemma']=='_'
                        assert tok['wcat']=='_'
                else:
                    tok['wmwe'] = None
                del tok['wlemma']
                del tok['wcat']

            if isEllipsis:
                sent['etoks'].append(tok)
            else:
                sent['toks'].append(tok)
    if sent:
        _postproc_sent(sent)
        yield sent

    if lc_tbd>0:
        print('Tokens with lexcat TBD:', lc_tbd, file=sys.stderr)

if __name__=='__main__':
    print('[')
    list_fields = ("toks", "etoks")
    dict_fields = ("swes", "smwes", "wmwes")
    first = True
    for sent in load_sents(fileinput.input()):
        # specially format the output
        if first:
            first = False
        else:
            print(',')
        #print(json.dumps(sent))
        sent_copy = dict(sent)
        for fld in list_fields+dict_fields:
            del sent_copy[fld]
        print(json.dumps(sent_copy, indent=1)[:-2], end=',\n')
        for fld in list_fields:
            print('   ', json.dumps(fld)+':', '[', end='')
            if sent[fld]:
                print()
                print(',\n'.join('      ' + json.dumps(v) for v in sent[fld]))
                print('    ],')
            else:
                print('],')
        for fld in dict_fields:
            print('   ', json.dumps(fld)+':', '{', end='')
            if sent[fld]:
                print()
                print(',\n'.join('      ' + json.dumps(str(k))+': ' + json.dumps(v) for k,v in sent[fld].items()))
                print('    }', end='')
            else:
                print('}', end='')
            print(',' if fld!="wmwes" else '')
        print('}', end='')
    print(']')
