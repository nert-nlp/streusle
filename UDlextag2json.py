#!/usr/bin/env python3

import json
import re
import sys
from argparse import ArgumentParser, FileType
from collections import defaultdict
from itertools import chain

from lexcatter import supersenses_for_lexcat, ALL_LEXCATS
from mwerender import render, render_sent
from streuseval import parse_mwe_links, form_groups
from supersenses import ancestors, makesslabel
from tagging import sent_tags

desc = \
"""
Defines a function to read a .UDlextag file sentence-by-sentence into a data structure,
unpacking the lextags into structured lexical annotations.
If the script is called directly, outputs the data as JSON.

Adapted from conllulex2json.py.
See conllulex2UDlextag.py for an explanation of the .UDlextag format.

@author: Nathan Schneider (@nschneid)
@since: 2019-06-20
"""

def load_sents(inF, morph_syn=True, misc=True, ss_mapper=None, validate_pos=True, validate_type=True):
    """Given a .UDlextag file (or iterable over lines), return an iterator over sentences.

    @param morph_syn: Whether to include CoNLL-U morphological features
    and syntactic dependency relations, if available.
    POS tags and lemmas are always included.
    @param misc: Whether to include the CoNLL-U miscellaneous column, if available.
    @param ss_mapper: A function to apply to supersense labels to replace them
    in the returned data structure. Applies to all supersense labels (nouns,
    verbs, prepositions). Not applied if the supersense slot is empty.
    @param validate_pos: Validate consistency of lextag with UPOS
    @param validate_type: Validate SWE-specific or SMWE-specific tags only apply to the corresponding MWE type
    """

    lc_tbd = 0

    def _unpack_lextags(sent):
        """At this point the sentence will be a collection of tokens, which will have
        lextags but no other STREUSLE info. The parts of the lextag have been parsed into tok['_lextag']."""

        # Infer MWE groupings from lextags
        mweflags = [tok['_lextag']['mweflag'] for tok in sent['toks'] if '_lextag' in tok]
        mweflags = ['O'] + mweflags # so token offsets in groups are 1-based
        links = parse_mwe_links(mweflags)
        sgroups = form_groups([(a,b) for a,b,s in links if s=='_'])
        maxgroups = form_groups([(a,b) for a,b,s in links]) # maximal groups: treat weak links like strong links
        wgroups = [g for g in maxgroups if g not in sgroups]

        # Register strong, then weak MWEs in data structure

        # Ordering MWEs by first token offset (tiebreaker to strong MWE):
        xgroups = [(min(sg),'s',sg) for sg in sgroups] + [(min(wg),'w',wg) for wg in wgroups]

        mwe_group = 1
        for tok1Num,x,g in sorted(xgroups):
                sent[x+'mwes'][mwe_group]['lexlemma'] = ''
                for mwe_position,tokNum in enumerate(sorted(g), start=1):
                    sent['toks'][tokNum-1][x+'mwe'] = mwe_group, mwe_position
                    sent[x+'mwes'][mwe_group]['toknums'].append(tokNum)
                    sent[x+'mwes'][mwe_group]['lexlemma'] += ' ' + sent['toks'][tokNum-1]['lemma']
                sent[x+'mwes'][mwe_group]['lexlemma'] = sent[x+'mwes'][mwe_group]['lexlemma'][1:] # delete leading space
                assert ' ' in sent[x+'mwes'][mwe_group]['lexlemma']
                mwe_group += 1
        del mwe_group

        # Deal with single-word expressions, and move lexcat/supersenses
        # from the token to the lexical expression
        for tok in sent['toks']:
            assert '_lextag' in tok

            if not tok['smwe']:   # token not part of a strong MWE
                tokNum = tok['#']
                sent['swes'][tokNum]['lexlemma'] = tok['lemma']
                assert ' ' not in sent['swes'][tokNum]['lexlemma']
                sent['swes'][tokNum]['toknums'].append(tokNum)

            if tok['wmwe'] and tok['wmwe'][1]==1: # first token in weak MWE
                #assert tok['wcat'] and tok['wcat']!='_'    # eventually it would be good to have a category for every weak expression
                sent['wmwes'][tok['wmwe'][0]]['lexcat'] = tok['wcat'] if tok['_lextag'].get('wcat') else None

            if tok['_lextag']['lexcat']:    # first token in a strong expression (SW or MW)
                einfo = tok['_lextag']
                assert einfo['lexcat']!='_',einfo

                # place to unpack lexcat/supersense info to (lexlemma is already unpacked)
                dest = sent['smwes'][tok['smwe'][0]] if tok['smwe'] else sent['swes'][tok['#']]

                dest['lexcat'] = einfo['lexcat']
                dest['ss'] = ss_mapper(einfo['ss']) if einfo['ss']!='_' else None
                dest['ss2'] = ss_mapper(einfo['ss2']) if einfo['ss2']!='_' else None

        for swe in sent['swes'].values():
            assert len(swe['toknums'])==1,swe
        for smwe in sent['smwes'].values():
            assert smwe['toknums']
        for wmwe in sent['wmwes'].values():
            assert wmwe['toknums']

        for tok in sent['toks']:
            del tok['_lextag']
            if not tok['smwe']:
                assert sent['swes'][tok['#']]['lexcat'],sent['swes']
            else:
                assert sent['smwes'][tok['smwe'][0]]['lexcat'],sent['smwes']


    def _postproc_sent(sent):
        nonlocal lc_tbd

        assert 'sent_id' in sent,sent

        # check that tokens are numbered from 1, in order
        for i,tok in enumerate(sent['toks'], 1):
            assert tok['#']==i

        # check that MWEs are numbered from 1 based on first token offset
        xmwes =  [(e["toknums"][0], 's', mwenum) for mwenum,e in sent['smwes'].items()]
        xmwes += [(e["toknums"][0], 'w', mwenum) for mwenum,e in sent['wmwes'].items()]
        xmwes.sort()
        for k,mwe in chain(sent['smwes'].items(), sent['wmwes'].items()):
            assert xmwes[int(k)-1][2]==k,f"In {sent['sent_id']}, MWEs are not numbered in the correct order: use normalize_mwe_numbering.py to fix"

        # check that lexical & weak MWE lemmas are correct
        lexes_to_validate = chain(sent['swes'].values(), sent['smwes'].values()) if validate_type else []
        for lexe in lexes_to_validate:
            sent['toks'][lexe['toknums'][0]-1]
            assert lexe['lexlemma']==' '.join(sent['toks'][i-1]['lemma'] for i in lexe['toknums']),f"In {sent['sent_id']}, MWE lemma is incorrect: {lexe} vs. {sent['toks'][lexe['toknums'][0]-1]}"
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
            if validate_pos and upos!=lc and lc!='PP' and (upos,lc) not in {('NOUN','N'),('PROPN','N'),('VERB','V'),
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
            assert len(smwe['toknums'])>1
        for wmwe in sent['wmwes'].values():
            assert len(wmwe['toknums'])>1,f"In {sent['sent_id']}, weak MWE has only one token according to group indices: {wmwe}"
            assert wmwe['lexlemma']==' '.join(sent['toks'][i-1]['lemma'] for i in wmwe['toknums']),(wmwe,sent['toks'][wmwe['toknums'][0]-1])
        # we already checked that noninitial tokens in an MWE have _ as their lemma

        # check lextags
        smweGroups = [smwe['toknums'] for smwe in sent['smwes'].values()]
        wmweGroups = [wmwe['toknums'] for wmwe in sent['wmwes'].values()]
        if 'mwe' not in sent:
            sent['mwe'] = render_sent(sent, False, False)
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
    for ln in chain(inF, [""]):  # Add empty line at the end to avoid skipping the last sent
        ln = ln.strip()
        if not ln:
            if sent:
                _unpack_lextags(sent)
                _postproc_sent(sent)
                yield sent
                sent = {}
            continue

        if ln.startswith('#'):
            if ln.startswith('# newdoc ') or ln.startswith('# newpar '): continue
            m = re.match(r'^# (\w+) = (.*)$', ln)
            k, v = m.group(1), m.group(2)
            assert k not in ('toks', 'swes', 'smwes', 'wmwes')
            sent[k] = v
        else:   # regular and ellipsis tokens
            if 'toks' not in sent:
                sent['toks'] = []   # excludes ellipsis tokens, so they don't interfere with indexing
                sent['etoks'] = []  # ellipsis tokens only
                sent['mwtoks'] = [] # multiword tokens
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
            isMWT = isEllipsis = False
            if re.match(r'^\d+$', tokNum):  # single word
                sent_conllulex += ln + '\n'
                tokNum = int(tokNum)
            else:
                if '-' in tokNum:   # multiword token e.g. 3-4: applies to words with clitics
                    # these just have the surface form, no lemma POS etc.
                    isMWT = True
                    part1, part2 = tokNum.split('-')
                if '.' in tokNum:   # ellipsis node indices are like 24.1
                    isEllipsis = True
                    assert not isMWT
                    part1, part2 = tokNum.split('.')

                if store_conllulex=='full': sent_conllulex += ln + '\n'
                part1 = int(part1)
                part2 = int(part2)
                tokNum = (part1, part2, tokNum) # ellipsis token offset is a tuple. include the string for convenience

            tok['#'] = tokNum
            tok['word'], tok['lemma'], tok['upos'], tok['xpos'] = conllu_cols[1:5]
            if not isMWT:
                assert tok['lemma']!='_' and tok['upos']!='_',tok
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

            if not (isEllipsis or isMWT):
                # Load STREUSLE-specific columns
                #tok['smwe'], tok['lexcat'], tok['lexlemma'], tok['ss'], tok['ss2'], \
                #    tok['wmwe'], tok['wcat'], tok['wlemma'], tok['lextag'] = lex_cols

                # initialize before setting lextag so JSON order will put lextag last
                tok['smwe'] = None
                tok['wmwe'] = None

                # .UDlextag: all but the last should be empty
                assert lex_cols[:-1]==['']*8
                assert lex_cols[-1]
                lt = tok['lextag'] = lex_cols[-1]

                # map the supersenses in the lextag
                for m in re.finditer(r'\b[a-z]\.[A-Za-z/-]+', tok['lextag']):
                    lt = lt.replace(m.group(0), ss_mapper(m.group(0)))
                for m in re.finditer(r'\b([a-z]\.[A-Za-z/-]+)\|\1\b', lt):
                    # e.g. p.Locus|p.Locus due to abstraction of p.Goal|p.Locus
                    lt = lt.replace(m.group(0), m.group(1)) # simplify to p.Locus
                tok['lextag'] = lt

                parts = lt.split('-', 2)
                assert 1<=len(parts)<=3,parts
                mweflag = parts[0]
                if len(parts)==1:
                    lexcat = sspart = None
                else:
                    lexcat = parts[1]
                    if len(parts)==3:
                        sspart = parts[2]
                    else:
                        sspart = None

                if sspart:
                    if '|' in sspart:
                        ss, ss2 = sspart.split('|')
                    else:
                        ss = sspart
                        if ss.startswith('p.') or ss=='`$': # copy
                            ss2 = ss
                        else:
                            ss2 = None
                else:
                    ss = ss2 = None

                tok['_lextag'] = {'mweflag': mweflag, 'lexcat': lexcat, 'ss': ss, 'ss2': ss2}
                # these will be moved to the lexical expression level in _unpack_lextags()

            if isEllipsis:
                sent['etoks'].append(tok)
            else:
                sent['toks'].append(tok)

    if lc_tbd>0:
        print('Tokens with lexcat TBD:', lc_tbd, file=sys.stderr)
        assert False,'PLACEHOLDER LEXCATS ARE DISALLOWED'

if __name__=='__main__':
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("inF", type=FileType(encoding="utf-8"))
    argparser.add_argument("--no-morph-syn", action="store_false", dest="morph_syn")
    argparser.add_argument("--no-misc", action="store_false", dest="misc")
    argparser.add_argument("--no-validate-pos", action="store_false", dest="validate_pos")
    argparser.add_argument("--no-validate-type", action="store_false", dest="validate_type")
    args = argparser.parse_args()

    print('[')
    list_fields = ("toks", "etoks")
    dict_fields = ("swes", "smwes", "wmwes")
    first = True
    for sent in load_sents(**vars(argparser.parse_args())):
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
