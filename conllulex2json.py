#!/usr/bin/env python3

import os, sys, fileinput, re, json
from collections import defaultdict

"""
Defines a function to read a .conllulex file sentence-by-sentence into a data structure.
If the script is called directly, outputs the data as JSON.

@author: Nathan Schneider (@nschneid)
@since: 2017-12-29
"""

def load_sents(inF, morph_syn=False, misc=False):
    """Given a .conllulex file, return an iterator over sentences.

    @param morph_syn: Whether to include CoNLL-U morphological features
    and syntactic dependency relations. POS tags and lemmas are always included.
    @param misc: Whether to include the CoNLL-U miscellaneous column.
    """

    sent = {}
    for ln in inF:
        if not ln.strip():
            if sent:
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
                sent['toks'] = []
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
            if not isEllipsis:  # ellipsis node indices are like 24.1
                tokNum = int(tokNum)
            tok['#'] = tokNum
            tok['word'], tok['lemma'], tok['upos'], tok['xpos'] = conllu_cols[1:5]
            if morph_syn:
                tok['feats'], tok['head'], tok['deprel'], tok['edeps'] = conllu_cols[5:9]
                tok['head'] = int(tok['head'])
            if misc:
                tok['misc'] = conllu_cols[9]
            tok['ellipsis'] = isEllipsis

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
                        sent['smwes'][smwe_group]['ss'] = tok['ss'] if tok['ss']!='_' else None
                        sent['smwes'][smwe_group]['ss2'] = tok['ss2'] if tok['ss2']!='_' else None
                    else:
                        assert ' ' not in tok['lexlemma']
                        assert tok['lexcat']=='_'
                else:
                    tok['smwe'] = None
                    assert tok['lexlemma']==tok['lemma'],(sent['sent_id'],tok['lexlemma'],tok['lemma'])
                    sent['swes'][tokNum]['lexlemma'] = tok['lexlemma']
                    assert tok['lexcat'] and tok['lexcat']!='_'
                    sent['swes'][tokNum]['lexcat'] = tok['lexcat']
                    sent['swes'][tokNum]['ss'] = tok['ss'] if tok['ss']!='_' else None
                    sent['swes'][tokNum]['ss2'] = tok['ss2'] if tok['ss2']!='_' else None
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
                        assert tok['wlemma'] and tok['wlemma']!='_',(sent['sent_id'],tokNum)
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

            sent['toks'].append(tok)
    if sent:
        yield sent

if __name__=='__main__':
    for sent in load_sents(fileinput.input()):
        print(json.dumps(sent))
