#!/usr/bin/env python3

import os, sys, fileinput, re, json
from collections import defaultdict
from itertools import chain

from lexcatter import supersenses_for_lexcat, ALL_LEXCATS

"""
Defines a function to read a .conllulex file sentence-by-sentence into a data structure.
If the script is called directly, outputs the data as JSON.
Also performs validation checks on the input.

@author: Nathan Schneider (@nschneid)
@since: 2017-12-29
"""

def load_sents(inF, morph_syn=False, misc=False, ss_mapper=None):
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
        for wmwe in sent['wmwes'].values():
            assert wmwe['lexlemma']==' '.join(sent['toks'][i-1]['lemma'] for i in wmwe['toknums']),(wmwe,sent['toks'][wmwe['toknums'][0]-1])
        # we already checked that noninitial tokens in an MWE have _ as their lemma
        # TODO: check lextag
        # TODO: check rendered MWE string
        # TODO: check lexcat

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
            if morph_syn:
                tok['feats'], tok['head'], tok['deprel'], tok['edeps'] = conllu_cols[5:9]
                tok['head'] = int(tok['head'])
            if misc:
                tok['misc'] = conllu_cols[9]

            if not isEllipsis:
                # Load STREUSLE-specific columns

                tok['smwe'], tok['lexcat'], tok['lexlemma'], tok['ss'], tok['ss2'], \
                    tok['wmwe'], tok['wcat'], tok['wlemma'], tok['lextag'] = lex_cols

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
    for sent in load_sents(fileinput.input()):
        print(json.dumps(sent))
