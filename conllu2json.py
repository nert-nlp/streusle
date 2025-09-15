#!/usr/bin/env python3

import json
import re
import sys
from argparse import ArgumentParser, FileType
from collections import defaultdict
from itertools import chain
from typing import Literal, Iterable, Any, overload

from lexcatter import supersenses_for_lexcat, ALL_LEXCATS
from mwerender import render
from supersenses import ancestors, makesslabel
from tagging import sent_tags

desc = \
"""
Adapted from conllulex2json.py, but for the new feature-based annotations in .conllu.
Defines a function to read a .conllu file sentence-by-sentence into a data structure.
If the script is called directly, outputs the data as JSON.
Also performs validation checks on the input.

@author: Nathan Schneider (@nschneid)
@since: 2025-09-13
"""

class SENTINEL: pass
sentinel = SENTINEL()

@overload
def regex_filter_uniq(pattern: str, items: Iterable[str], default: Any=...) -> Any: ...

@overload
def regex_filter_uniq(pattern: str, items: Iterable[str], default: SENTINEL=sentinel) -> str: ...


def regex_filter_uniq(pattern: str, items: Iterable[str], default=sentinel):
    results = [s for s in items if re.search(pattern, s)]
    if not results:
        if default is sentinel:
            raise ValueError(f'None of the items matches the pattern: {pattern}')
        return default
    if len(results)>1:
        raise ValueError(f'Multiple items match the pattern: {pattern}')
    return results[0]

def parse_mwe_lemma(mwelemma: str) -> list[str]:
    """Given a lemma of the form 'x y z' or 'x <4> y <2> z', expand to
    list of individual token lemmas where gap positions are None:
    ['x', 'y', 'z'], ['x', None, None, None, None, 'y', None, None, 'z']"""
    assert re.match(r'^(\S+ )*\S+$', mwelemma)  # ensure no weird whitespace characters. goeswith "MWEs" can have no spaces in the lemma
    mwe_tok_lemmas = []    # lemma of any token that is part of the expression; None for any token in a gap
    for x in mwelemma.split(' '):
        if (m := re.match(r'^<([1-9]\d*)>$', x)):
            gaplen = int(m.group(1))
            mwe_tok_lemmas.extend([None]*gaplen)
        else:
            mwe_tok_lemmas.append(x)
    return mwe_tok_lemmas

def load_sents(inF, morph_syn=True, misc=True, ss_mapper=None,
               store_conllulex: Literal[False, 'full', 'toks'] = False,
               validate_pos=True, validate_type=True):
    """Given a .conllulex or .json file, return an iterator over sentences.
    If a .conllulex file, performs consistency checks.

    @param morph_syn: Whether to include CoNLL-U morphological features
    and syntactic dependency relations, if available.
    POS tags and lemmas are always included.
    @param misc: Whether to include the CoNLL-U miscellaneous column explicitly in the output
    (the field will always be processed).
    @param ss_mapper: A function to apply to supersense labels to replace them
    in the returned data structure. Applies to all supersense labels (nouns,
    verbs, prepositions). Not applied if the supersense slot is empty.
    @param store_conllu: If input is .conllu, whether to store the sentence's
    input lines as a string in the returned data structure--'full' to store all
    lines (including metadata and ellipsis nodes), 'toks' to store regular tokens only.
    @param validate_pos: Validate consistency of lextag with UPOS
    @param validate_type: Validate SWE-specific or SMWE-specific tags only apply to the corresponding MWE type
    Has no effect if input is JSON.
    """
    if store_conllulex: assert store_conllulex in {'full', 'toks'}

    if ss_mapper is None:
        ss_mapper = lambda ss: ss

    # If .json: just load the data
    if inF.name.endswith('.json'):
        for sent in json.load(inF):
            for lexe in chain(sent['swes'].values(), sent['smwes'].values()):
                if lexe['ss'] is not None:
                    lexe['ss'] = ss_mapper(lexe['ss'])
                if lexe['ss2'] is not None:
                    lexe['ss2'] = ss_mapper(lexe['ss2'])
                assert all(t>0 for t in lexe['toknums']),('Token offsets must be positive',lexe)
            if 'wmwes' in sent:
                for lexe in sent['wmwes'].values():
                    assert all(t>0 for t in lexe['toknums']),('Token offsets must be positive',lexe)

            if not morph_syn:
                for tok in sent['toks']:
                    tok.pop('feats', None)
                    tok.pop('head', None)
                    tok.pop('deprel', None)
                    tok.pop('edeps', None)

            yield sent
        return

    # Otherwise, .conllulex: create data structures and check consistency

    lc_tbd = 0

    def _postproc_sent(sent):
        nonlocal lc_tbd

        # check that tokens are numbered from 1, in order
        for i,tok in enumerate(sent['toks'], 1):
            assert tok['#']==i

        # check that MWEs are numbered from 1 based on first token offset
        xmwes =  [(e["toknums"][0], 's', mwenum) for mwenum,e in sent['smwes'].items()]
        xmwes += [(e["toknums"][0], 'w', mwenum) for mwenum,e in sent['wmwes'].items()]
        xmwes.sort()
        for k,(_,_,mwenum) in enumerate(xmwes, start=1):
            assert mwenum==k,f"In {sent['sent_id']}, MWEs are not numbered in the correct order: use normalize_mwe_numbering.py to fix"
        
        # check that lexical (non-weak) MWE lemmas are correct
        lexes_to_validate = chain(sent['swes'].values(), sent['smwes'].values()) if validate_type else []
        for lexe in lexes_to_validate:
            expected_lexlemma = ' '.join(lem for i in lexe['toknums'] for lem in [sent['toks'][i-1]['lemma']] if lem!='_')
            # lemma '_' happens on goeswith tokens (these are no longer annotated as MWEs)
            assert lexe['lexlemma']==(expected_lexlemma or '_'),f"In {sent['sent_id']}, MWE lemma is incorrect: {lexe} vs. {expected_lexlemma!r} {sent['toks'][lexe['toknums'][0]-1]}"
            lc = lexe['lexcat']
            if lc.endswith('!@'): lc_tbd += 1
            valid_ss = supersenses_for_lexcat(lc)
            if lc=='V':
                assert len(lexe['toknums'])==1,f'In {sent["sent_id"]}, Verbal MWE "{lexe["lexlemma"]}" lexcat must be subtyped (V.VID, etc., not V)'
            ss, ss2 = lexe['ss'], lexe['ss2']
            if valid_ss:
                if ss=='??':
                    assert ss2 is None
                elif ss not in valid_ss or (lc in ('N','V') or lc.startswith('V.'))!=(ss2 is None) or (ss2 is not None and ss2 not in valid_ss):
                    assert False,f"In {sent['sent_id']}, invalid supersense(s) in lexical entry: {lexe}"
                elif ss.startswith('p.'):
                    assert ss2.startswith('p.')
                    assert ss2 not in {'p.Experiencer', 'p.Stimulus', 'p.Originator', 'p.Recipient', 'p.SocialRel', 'p.Org', 'p.OrgMember', 'p.Ensemble', 'p.QuantityValue'},(f'{ss2} should never be function',lexe)
                    if ss!=ss2:
                        ssA, ss2A = ancestors(ss), ancestors(ss2)
                        # there are just a few permissible combinations where one is the ancestor of the other
                        if (ss,ss2) not in {('p.Circumstance','p.Locus'), ('p.Circumstance','p.Path'),
                            ('p.Locus','p.Goal'), ('p.Locus','p.Source'),
                            ('p.Characteristic','p.Stuff'),
                            ('p.Whole','p.Gestalt'), ('p.Org', 'p.Gestalt'),
                            ('p.QuantityItem','p.Gestalt'), ('p.Goal','p.Locus')}:
                            assert ss not in ss2A,f"In {sent['sent_id']}, unexpected construal: {ss} ~> {ss2}"
                            assert ss2 not in ssA,f"In {sent['sent_id']}, unexpected construal: {ss} ~> {ss2}"
            else:
                assert ss is None and ss2 is None and lc not in ('N', 'V', 'P', 'INF.P', 'PP', 'POSS', 'PRON.POSS'),f"In {sent['sent_id']}, invalid supersense(s) in lexical entry: {lexe}"

        # check lexcat on single-word expressions
        for swe in sent['swes'].values():
            tok = sent['toks'][swe['toknums'][0]-1]
            upos, xpos = tok['upos'], tok['xpos']
            lc = swe['lexcat']
            if lc.endswith('!@'): continue
            if lc not in ALL_LEXCATS:
                assert not validate_type, f"In {sent['sent_id']}, invalid lexcat {lc} for single-word expression '{tok['word']}'"
                continue
            if validate_pos and upos!=lc and (upos,lc) not in {('NOUN','N'),('PROPN','N'),('VERB','V'),
                ('ADP','P'),('ADV','P'),('SCONJ','P'),
                ('ADP','DISC'),('ADV','DISC'),('SCONJ','DISC'),
                ('PART','POSS')}:
                # most often, the single-word lexcat should match its upos
                # check a list of exceptions
                mismatchOK = False
                if xpos=='TO' and lc.startswith('INF'):
                    mismatchOK = True
                elif (xpos=='TO')!=lc.startswith('INF'):
                    assert upos=='SCONJ' and swe['lexlemma']=='for',(sent['sent_id'],swe,tok)
                    mismatchOK = True

                if (upos in ('NOUN', 'PROPN'))!=(lc=='N'):
                    #try:
                    assert upos in ('SYM','X') or (lc in ('PRON','DISC')),(sent['sent_id'],swe,tok)
                    #except AssertionError:
                    #    print('Suspicious lexcat/POS combination:', sent['sent_id'], swe, tok, file=sys.stderr)
                    mismatchOK = True
                message = f"In {sent['sent_id']}, single-word expression '{tok['word']}' has lexcat {lc}, which is incompatible with its upos {upos}"
                if (upos=='AUX')!=(lc=='AUX'):
                    assert tok['lemma']=='be' and lc=='V',message    # copula has upos=AUX
                    mismatchOK = True
                if (upos=='VERB')!=(lc=='V'):
                    if lc=='ADJ':
                        print('Word treated as VERB in UD, ADJ for supersenses:', sent['sent_id'], tok['word'], file=sys.stderr)
                    else:
                        assert tok['lemma']=='be' and lc=='V',message    # copula has upos=AUX
                    mismatchOK = True
                if upos=='PRON':
                    assert lc=='PRON' or lc=='PRON.POSS',message
                    mismatchOK = True
                if lc=='ADV':
                    assert upos=='ADV' or upos=='PART',message    # PART is for negations
                    mismatchOK = True
                if upos=='ADP' and lc=='CCONJ':
                    assert tok['lemma']=='versus'
                    mismatchOK = True

                assert mismatchOK,message
            if validate_type:
                assert lc!='PP',f"In {sent['sent_id']}, PP should only apply to strong MWEs, but occurs for single-word expression '{tok['word']}'"
        for smwe in sent['smwes'].values():
            assert len(smwe['toknums'])>1,smwe
        for wmwe in sent['wmwes'].values():
            assert len(wmwe['toknums'])>1,f"In {sent['sent_id']}, weak MWE has only one token according to group indices: {wmwe}"
            assert wmwe['lexlemma']==' '.join(sent['toks'][i-1]['lemma'] for i in wmwe['toknums']),(sent["sent_id"],wmwe,sent['toks'][wmwe['toknums'][0]-1])
        # we already checked that noninitial tokens in an MWE have _ as their lemma

        # generate lextags
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
                sslabel = makesslabel(lexe)
                if sslabel:
                    fulllextag += '-' + sslabel

                if tok['wmwe']:
                    wmweNum, position = tok['wmwe']
                    wmwe = sent['wmwes'][wmweNum]
                    wcat = wmwe['lexcat']
                    if wcat and position==1:
                        fulllextag += '+'+wcat

            assert 'lextag' not in tok
            tok['lextag'] = fulllextag

        # check rendered MWE string
        s = render([tok['word'] for tok in sent['toks']],
                   smweGroups, wmweGroups)
        if sent['mwe']!=s:
            caveat = ' (may be due to simplification)' if '$1' in sent['mwe'] else ''
            print(f'MWE string mismatch{caveat}:', s,sent['mwe'],sent['sent_id'], file=sys.stderr)

    sent = {}
    sent_conllulex = ''
    toknum2smwe = {}
    toknum2wmwe = {}

    for ln in chain(inF, [""]):  # Add empty line at the end to avoid skipping the last sent
        ln = ln.strip()
        if not ln:
            if sent:
                if store_conllulex: sent['conllulex'] = sent_conllulex
                _postproc_sent(sent)
                yield sent
                sent = {}
                sent_conllulex = ''
                toknum2smwe = {}
                toknum2wmwe = {}
            continue

        if ln.startswith('#'):  # metadata
            if store_conllulex=='full': sent_conllulex += ln + '\n'
            if ln.startswith('# newdoc ') or ln.startswith('# newpar ') or ln.startswith('# TODO: '): continue
            m = re.match(r'^# (\w+) = (.*)$', ln)
            assert m,ln
            k, v = m.group(1), m.group(2)
            assert k not in ('toks', 'swes', 'smwes', 'wmwes')
            sent[k] = v
        else:   # regular and ellipsis tokens
            if 'toks' not in sent:
                sent['toks'] = []   # excludes ellipsis and multiword tokens, so they don't interfere with indexing
                sent['etoks'] = []  # ellipsis tokens and multiword tokens only (not to be confused with MWEs)
                sent['swes'] = {}   #defaultdict(lambda: {'lexlemma': None, 'lexcat': None, 'ss': None, 'ss2': None, 'toknums': []})
                sent['smwes'] = {}  #defaultdict(lambda: {'lexlemma': None, 'lexcat': None, 'ss': None, 'ss2': None, 'toknums': []})
                sent['wmwes'] = {}  #defaultdict(lambda: {'lexlemma': None, 'toknums': []})
            assert ln.count('\t')==9,ln

            conllu_cols = ln.split('\t')
            assert len(conllu_cols)==10,ln

            # Load CoNLL-U columns

            tok = {}
            tokNum = conllu_cols[0]

            # Special kinds of tokens: ellipsis nodes and multiword tokens.
            # These do not receive STREUSLE annotations.
            isEllipsis = isMWT = False
            if re.match(r'^\d+$', tokNum) is None:
                if '.' in tokNum:
                    isEllipsis = True # ellipsis token (e.g. 24.1), part of enhanced representation
                elif '-' in tokNum:
                    isMWT = True # multiword token (e.g. 10-11), used for clitics
            if isEllipsis or isMWT:
                if store_conllulex=='full': sent_conllulex += ln + '\n'
                part1, part2 = tokNum.split('.' if isEllipsis else '-')
                part1 = int(part1)
                part2 = int(part2)
                tokNum = (part1, part2, tokNum) # token offset is a tuple. include the string for convenience
            else:
                sent_conllulex += ln + '\n'
                tokNum = int(tokNum)
            tok['#'] = tokNum
            tok['word'], tok['lemma'], tok['upos'], tok['xpos'] = conllu_cols[1:5]
            assert isMWT or (tok['upos']!='_' and (tok['lemma']!='_' or tok['upos']=='X' and conllu_cols[7]=='goeswith')),tok
            if morph_syn:
                tok['feats'], tok['head'], tok['deprel'], tok['edeps'] = conllu_cols[5:9]
                if tok['head']=='_':
                    assert isEllipsis or isMWT
                    tok['head'] = None
                else:
                    tok['head'] = int(tok['head'])
                if tok['deprel']=='_':
                    assert isEllipsis or isMWT
                    tok['deprel'] = None
            
            tok['misc'] = conllu_cols[9]
            for nullable_conllu_fld in ('xpos', 'feats', 'edeps', 'misc'):
                if nullable_conllu_fld in tok and tok[nullable_conllu_fld]=='_':
                    tok[nullable_conllu_fld] = None
            if tok['misc'] is not None:
                tok['misc'] = tok['misc'].split('|')
                # per https://universaldependencies.org/format.html#miscellaneous MISC must be splittable on | but components 
                # are not required to be attribute/value pairs

            if not isEllipsis and not isMWT:
                # Load lexical semantic features:
                #   MWECat, MWELemma, MWELen, MWEString, Supersense, TODO: PRel

                assert isinstance(tokNum,int)

                #######################################
                # process lexical expression (non-weak)
                #######################################

                # read supersenses
                ss = regex_filter_uniq(r'^Supersense(\[scene\])?=', tok['misc'] or '', default=None)
                if ss:
                    ss = ss_mapper(ss[ss.index('=')+1:])
                ss2 = regex_filter_uniq(r'^Supersense(\[coding\])=', tok['misc'] or '', default=None)
                if ss2:
                    ss2 = ss2[ss2.index('=')+1:]
                if not ss2 and (ss or '').startswith(('p.','`$')):
                    ss2 = ss

                # read expression units: SMWE, SWE
                if (smweLemma := regex_filter_uniq(r'^MWELemma=', tok['misc'] or '', default=None)):
                    # starting an SMWE
                    smweLemma = smweLemma[9:]
                    smweString = regex_filter_uniq(r'^MWEString=', tok['misc'] or '', default=None)
                    if smweString:
                        smweString = smweString[10:]    # note: goeswith tokens are space-separated in here but not smweLemma
                    else:
                        smweString = smweLemma
                    smwe_tok_words = parse_mwe_lemma(smweString)
                    smweLen = regex_filter_uniq(r'^MWELen=', tok['misc'])
                    assert re.match(r'^[1-9]\d*', smweLen[7:]),smweLen
                    smweLen = int(smweLen[7:])
                    assert smweLen>=2,smweLen
                    assert smweLen==len(smwe_tok_words),(smweLen,smwe_tok_words)
                    assert smweString.count(' ')>=smweLemma.count(' ')    # possibly > due to goeswith tokens
                    smweCat = regex_filter_uniq(r'^MWECat=', tok['misc'])
                    smweCat = smweCat[7:]
                    smwe_group = len(sent['smwes']) + len(sent['wmwes']) + 1
                    toknums = [i for i,lem in enumerate(smwe_tok_words, start=tokNum) if lem is not None]
                    assert 2<=len(toknums)<=smweLen
                    smwe_tok_lemmas = parse_mwe_lemma(smweLemma)
                    smwe_lexlemma = ' '.join(filter(None, smwe_tok_lemmas))
                    assert len(toknums)>=smwe_lexlemma.count(' ')+1
                    sent['smwes'][smwe_group] = {'lexlemma': smwe_lexlemma,
                                                 'lexcat': smweCat,
                                                 # TODO: 'lexlemma_full': smweLemma
                                                 'ss': ss,
                                                 'ss2': ss2,
                                                 'toknums': toknums}
                    for i in toknums:
                        assert i not in toknum2smwe
                        toknum2smwe[i] = smwe_group
                    
                    # lexlemma will be checked against individual token lemmas in _postproc_sent()

                    del smweCat
                    del smweLemma
                    del smweLen
                    del smwe_group
                    del smwe_lexlemma
                    del smwe_tok_lemmas
                    del toknums
                else:
                    # no MWELemma, so ensure no MWECat or MWELen
                    assert regex_filter_uniq(r'^MWECat=', tok['misc'] or '', default=None) is None,'MWECat without MWELemma'
                    assert regex_filter_uniq(r'^MWELen=', tok['misc'] or '', default=None) is None,'MWELen without MWELemma'
                    
                    if tokNum not in toknum2smwe: # not in an SMWE; record as an SWE
                        # in the new format we don't have a lexcat stored for SWE, so we infer it
                        if tok['xpos'] in ('PRP$','WP$'):
                            lc = 'PRON.POSS'
                        elif tok['xpos']=='TO':
                            lc = 'INF.P' if (ss or '').startswith('p.') else 'INF'
                        elif tok['upos']=='PART' and tok['lemma']=='not':
                            lc = 'ADV'
                        elif tok['xpos']=='POS':
                            lc = 'POSS'
                        elif tok['upos'] in ('ADV','SCONJ') and (ss or '').startswith(('p.','??')):
                            lc = 'P'
                        elif tok['upos'] in ('AUX',) and (ss or '').startswith('v.'):
                            lc = 'V'
                        elif tok['upos'] in ('SYM',) and (ss or '').startswith('n.'):
                            lc = 'N'
                        elif (ss or '').startswith('`j'): # UD VERB treated as adjective for supersense annotation
                            lc = 'ADJ'
                            ss = None   # not a proper supersense
                        elif (ss or '').startswith('`d'): # UD single-word discourse expression excluded from regular supersense annotation
                            lc = 'DISC'
                            ss = None   # not a proper supersense
                        elif (ss or '').startswith('`c'): # UD ADP excluded from regular supersense annotation as a coordinator ("versus")
                            lc = 'CCONJ'
                            ss = None   # not a proper supersense
                        elif not ss and (tok['upos'],tok['lemma']) in [('NOUN', 'other'), ('NOUN', 'one'), ('NOUN', 'etc.')]:
                            lc = 'PRON'
                        elif not ss and tok['xpos']=='IN' and tok['lemma']=='for':
                            lc = 'INF'
                        else:
                            lc = {'ADP': 'P', 'NOUN': 'N', 'PROPN': 'N', 'VERB': 'V'}.get(tok['upos'],tok['upos'])
                        sent['swes'][tokNum] = {'lexlemma': tok['lemma'],
                                                'lexcat': lc,
                                                'ss': ss,
                                                'ss2': ss2,
                                                'toknums': [tokNum]}
                    else:
                        assert ss is None and ss2 is None,f'Non-initial token of SMWE should not have supersense {(tok,toknum2smwe)}'

                if (g := toknum2smwe.get(tokNum)) is not None:
                    position = sent['smwes'][g]['toknums'].index(tokNum) + 1
                    tok['smwe'] = (g, position)
                else:
                    tok['smwe'] = None


                #########################
                # process weak expression
                #########################

                if (wmweLemma := regex_filter_uniq(r'^MWELemma\[weak\]=', tok['misc'] or '', default=None)):
                    wmweLemma = wmweLemma[15:]
                    # starting an SMWE
                    wmwe_tok_lemmas = parse_mwe_lemma(wmweLemma)
                    wmweLen = regex_filter_uniq(r'^MWELen\[weak\]=', tok['misc'])
                    assert re.match(r'^[1-9]\d*', wmweLen[13:]),wmweLen
                    wmweLen = int(wmweLen[13:])
                    assert wmweLen>=2,wmweLen
                    assert wmweLen==len(wmwe_tok_lemmas),(wmweLen,wmwe_tok_lemmas)
                    wmweCat = regex_filter_uniq(r'^MWECat\[weak\]=', tok['misc'], default=None)
                    if wmweCat: # MWECat[weak] is optional
                        wmweCat = wmweCat[13:]
                    wmwe_group = len(sent['smwes']) + len(sent['wmwes']) + 1
                    wmwe_lexlemma = ' '.join(filter(None, wmwe_tok_lemmas))
                    toknums = [i for i,lem in enumerate(wmwe_tok_lemmas, start=tokNum) if lem is not None]
                    assert 2<=len(toknums)<=wmweLen
                    assert len(toknums)==wmwe_lexlemma.count(' ')+1
                    sent['wmwes'][wmwe_group] = {'lexlemma': wmwe_lexlemma,
                                                 # TODO: 'lexlemma_full': smweLemma
                                                 'toknums': toknums,
                                                 'lexcat': wmweCat}
                    for i in toknums:
                        assert i not in toknum2wmwe
                        toknum2wmwe[i] = wmwe_group

                    # lexlemma will be checked against individual token lemmas in _postproc_sent()

                    del wmweCat
                    del wmweLemma
                    del wmweLen
                    del wmwe_group
                    del wmwe_lexlemma
                    del wmwe_tok_lemmas
                    del toknums
                else:
                    # no MWELemma[weak], so ensure no MWECat[weak] or MWELen[weak]
                    assert regex_filter_uniq(r'^MWECat\[weak\]=', tok['misc'] or '', default=None) is None,'MWECat[weak] without MWELemma[weak]'
                    assert regex_filter_uniq(r'^MWELen\[weak\]=', tok['misc'] or '', default=None) is None,'MWELen[weak] without MWELemma[weak]'

                if (g := toknum2wmwe.get(tokNum)) is not None:
                    position = sent['wmwes'][g]['toknums'].index(tokNum) + 1
                    tok['wmwe'] = (g, position)
                else:
                    tok['wmwe'] = None


            if not misc:
                del tok['misc'] # exclude from output

            if isEllipsis or isMWT:
                sent['etoks'].append(tok)
            else:
                sent['toks'].append(tok)
    if sent:
        if store_conllulex: sent['conllulex'] = sent_conllulex
        _postproc_sent(sent)
        yield sent

    if lc_tbd>0:
        print('Tokens with lexcat TBD:', lc_tbd, file=sys.stderr)
        assert False,'PLACEHOLDER LEXCATS ARE DISALLOWED'

def print_sent_json(sent):
    list_fields = ("toks", "etoks")
    dict_fields = ("swes", "smwes", "wmwes")

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

def print_json(sents):
    print('[')
    first = True
    for sent in sents:
        # specially format the output
        if first:
            first = False
        else:
            print(',')
        print_sent_json(sent)
    print(']')

if __name__ == '__main__':
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("inF", type=FileType(encoding="utf-8"))
    argparser.add_argument("--no-morph-syn", action="store_false", dest="morph_syn")
    argparser.add_argument("--no-misc", action="store_false", dest="misc")
    argparser.add_argument("--no-validate-pos", action="store_false", dest="validate_pos")
    argparser.add_argument("--no-validate-type", action="store_false", dest="validate_type")
    argparser.add_argument("--store-conllulex", choices=(False, 'full', 'toks'))
    print_json(load_sents(**vars(argparser.parse_args())))
