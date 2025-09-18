#!/usr/bin/env python3

import json
import re
import sys
from argparse import ArgumentParser, FileType
from collections import defaultdict
from itertools import chain
from typing import Literal

from lexcatter import supersenses_for_lexcat, ALL_LEXCATS
from mwerender import render
from supersenses import ancestors, makesslabel
from tagging import sent_tags

desc = \
"""
Defines a function to read a .conllulex file sentence-by-sentence into a data structure.
If the script is called directly, outputs the data as JSON.
Also performs validation checks on the input.

@author: Nathan Schneider (@nschneid)
@since: 2017-12-29
"""




def load_sents(inF, morph_syn=True, misc=True, ss_mapper=None,
               store_conllulex: Literal[False, 'full', 'toks'] = False,
               validate_pos=True, validate_type=True):
    """Given a .conllulex or .json file, return an iterator over sentences.
    If a .conllulex file, performs consistency checks.

    @param morph_syn: Whether to include CoNLL-U morphological features
    and syntactic dependency relations, if available.
    POS tags and lemmas are always included.
    @param misc: Whether to include the CoNLL-U miscellaneous column, if available.
    @param ss_mapper: A function to apply to supersense labels to replace them
    in the returned data structure. Applies to all supersense labels (nouns,
    verbs, prepositions). Not applied if the supersense slot is empty.
    @param store_conllulex: If input is .conllulex, whether to store the sentence's
    input lines as a string in the returned data structure--'full' to store all
    lines (including metadata and ellipsis nodes), 'toks' to store regular tokens only.
    @param validate_pos: Validate consistency of lextag with UPOS
    @param validate_type: Validate SWE-specific or SMWE-specific tags only apply to the corresponding MWE type
    Has no effect if input is JSON.
    """
    if store_conllulex: assert store_conllulex in {'full', 'toks'}

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

            if not misc:
                for tok in sent['toks']:
                    tok.pop('misc', None)

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
        for k,mwe in chain(sent['smwes'].items(), sent['wmwes'].items()):
            assert int(k)-1<len(xmwes),f"In {sent['sent_id']}, MWE index {k} exceeds number of MWEs in the sentence"
            assert xmwes[int(k)-1][2]==k,f"In {sent['sent_id']}, MWEs are not numbered in the correct order: use normalize_mwe_numbering.py to fix"

        # check that lexical & weak MWE lemmas are correct
        lexes_to_validate = chain(sent['swes'].values(), sent['smwes'].values()) if validate_type else []
        for lexe in lexes_to_validate:
            assert lexe['lexlemma']==' '.join(lem for i in lexe['toknums'] for lem in [sent['toks'][i-1]['lemma']] if lem!='_'),f"In {sent['sent_id']}, MWE lemma is incorrect: {lexe} vs. {sent['toks'][lexe['toknums'][0]-1]}"
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
                sslabel = makesslabel(lexe)
                if sslabel:
                    fulllextag += '-' + sslabel

                if tok['wmwe']:
                    wmweNum, position = tok['wmwe']
                    wmwe = sent['wmwes'][wmweNum]
                    wcat = wmwe['lexcat']
                    if wcat and position==1:
                        fulllextag += '+'+wcat

            assert tok['lextag']==fulllextag,f"In {sent['sent_id']}, the full tag at the end of the line is inconsistent with the rest of the line ({fulllextag} expected): {tok}"

        # check rendered MWE string
        s = render([tok['word'] for tok in sent['toks']],
                   smweGroups, wmweGroups)
        if sent['mwe']!=s:
            caveat = ' (may be due to simplification)' if '$1' in sent['mwe'] else ''
            print(f'MWE string mismatch{caveat}:', s,sent['mwe'],sent['sent_id'], file=sys.stderr)

    if ss_mapper is None:
        ss_mapper = lambda ss: ss

    sent = {}
    sent_conllulex = ''

    for ln in chain(inF, [""]):  # Add empty line at the end to avoid skipping the last sent
        ln = ln.strip()
        if not ln:
            if sent:
                if store_conllulex: sent['conllulex'] = sent_conllulex
                _postproc_sent(sent)
                yield sent
                sent = {}
                sent_conllulex = ''
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
                sent['swes'] = defaultdict(lambda: {'lexlemma': None, 'lexcat': None, 'ss': None, 'ss2': None, 'toknums': []})
                sent['smwes'] = defaultdict(lambda: {'lexlemma': None, 'lexcat': None, 'ss': None, 'ss2': None, 'toknums': []})
                sent['wmwes'] = defaultdict(lambda: {'lexlemma': None, 'toknums': []})
            assert ln.count('\t')==18,ln

            cols = ln.split('\t')
            conllu_cols = cols[:10]
            lex_cols = cols[10:]

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
            if misc:
                tok['misc'] = conllu_cols[9]
            for nullable_conllu_fld in ('xpos', 'feats', 'edeps', 'misc'):
                if nullable_conllu_fld in tok and tok[nullable_conllu_fld]=='_':
                    tok[nullable_conllu_fld] = None

            if not isEllipsis and not isMWT:
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
                        #assert ' ' in tok['lexlemma']   # false for goeswith MWEs. Anyway lexlemmas are checked in _postproc_sent()
                        sent['smwes'][smwe_group]['lexlemma'] = tok['lexlemma']
                        assert tok['lexcat'] and tok['lexcat']!='_'
                        sent['smwes'][smwe_group]['lexcat'] = tok['lexcat']
                        sent['smwes'][smwe_group]['ss'] = ss_mapper(tok['ss']) if tok['ss']!='_' else None
                        sent['smwes'][smwe_group]['ss2'] = ss_mapper(tok['ss2']) if tok['ss2']!='_' else None
                    else:
                        assert tok['lexlemma']=='_',f"In {sent['sent_id']}, token is non-initial in a strong MWE, so lexlemma should be '_': {tok}"
                        assert tok['lexcat']=='_',f"In {sent['sent_id']}, token is non-initial in a strong MWE, so lexcat should be '_': {tok}"
                else:
                    tok['smwe'] = None
                    assert tok['lexlemma']==tok['lemma'],f"In {sent['sent_id']}, single-word expression lemma \"{tok['lexlemma']}\" doesn't match token lemma \"{tok['lemma']}\""
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
                    assert tok['wlemma']=='_',f"In {sent['sent_id']}, \"{tok['wlemma']}\" is present in the weak multiword expression lemma field, but token is not part of any weak MWE"
                    assert tok['wcat']=='_',f"In {sent['sent_id']}, \"{tok['wcat']}\" is present in the weak multiword expression category field, but token is not part of any weak MWE"
                del tok['wlemma']
                del tok['wcat']

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
