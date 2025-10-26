#!/usr/bin/env python3
"""
Given a file in the STREUSLE JSON format, convert it to the .conllu format with STREUSLE annotations in MISC.
Relies on sentence IDs being in the format DOCID-SENTNUM, where SENTNUM contains no hyphens.

STREUSLE featurization code adapted from conllulex2conllu.py.
Other code adapted from json2conllulex.py.

Args: inputfile

@since: 2025-10-26
@author: Nathan Schneider (@nschneid)
"""

import os, sys, fileinput, re, json, csv
from typing import Any
from collections import defaultdict
from itertools import chain
from govobj import add_gov_obj

CONLLU = ('ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC')
         # 1     2       3        4       5       6        7       8         9       10

FIELDS = CONLLU

# Naming is slightly different for some fields
CONLLU_TO_JSON_FIELDS = {'ID': '#', 'FORM': 'word', 'DEPS': 'edeps'}

STREUSLE_FIELDS = 'MWECat', 'MWELemma', 'MWELen', 'MWEString', 'Supersense', 'PRel'

def load_ss(exp, all_toks, target: dict[str,str]):
    if exp['ss']:
        if exp['ss2'] and exp['ss2']!=exp['ss']:
            target['Supersense[scene]'] = exp['ss']
            target['Supersense[coding]'] = exp['ss2']
        else:
            target['Supersense'] = exp['ss']
    if 'heuristic_relation' in exp:
        assert exp['ss'].startswith(('p.', '`$', '??')),exp
        rel = exp['heuristic_relation']
        target['PRel[config]'] = rel['config']
        if rel['gov'] is not None:
            target['PRel[gov]'] = f'{rel['gov']}:{rel['govlemma']}'
        if rel['obj'] is not None:
            target['PRel[obj]'] = f'{rel['obj']}:{rel['objlemma']}'
    if not exp['ss'] and len(exp['toknums'])==1:
        if exp['lexcat']=='DISC':
            target['Supersense'] = '`d'
        if exp['lexcat']=='CCONJ' and all_toks[exp['toknums'][0]-1]['upos']=='ADP':
            target['Supersense'] = '`c'
        elif exp['lexcat']=='ADJ' and all_toks[exp['toknums'][0]-1]['upos']=='VERB':
            target['Supersense'] = '`j'

def load_mwe(exp, all_toks, target: dict[str,Any], weak=False):
    """`target` is dict[str,str] on input and output (for some keys the value is temporarily list[str])"""
    if not weak:
        target['MWECat'] = exp['lexcat']
        MWELen_KEY = 'MWELen'
        MWELemma_KEY = 'MWELemma'
        MWEString_KEY = 'MWEString'
    else:
        MWELen_KEY = 'MWELen[weak]'
        MWELemma_KEY = 'MWELemma[weak]'
        MWEString_KEY = 'MWEString[weak]'
    target[MWELen_KEY] = str(exp['toknums'][-1] - exp['toknums'][0] + 1)
    lemma_nongap_parts = exp['lexlemma'].split()
    target[MWELemma_KEY] = []
    target[MWEString_KEY] = []
    prevI = None
    for i in exp['toknums']:
        if prevI is not None and i > prevI+1:
            gaplen = i - prevI - 1
            target[MWELemma_KEY].append(f'<{gaplen}>')
            target[MWEString_KEY].append(f'<{gaplen}>')
        target[MWEString_KEY].append(all_toks[i-1]['word'])
        if not lemma_nongap_parts:
            pass
        else:
            part = lemma_nongap_parts.pop(0)
            target[MWELemma_KEY].append(part)
        prevI = i
    if target and MWELemma_KEY in target:
        target[MWELemma_KEY] = ' '.join(target[MWELemma_KEY])
        target[MWEString_KEY] = ' '.join(target[MWEString_KEY])
        if target[MWEString_KEY].lower()==target[MWELemma_KEY].lower():
            del target[MWEString_KEY]   # only include MWEString= if distinct from MWELemma= (inflection, typo)

def build_conllu(sents):
    result = ''
    curDocId = None
    for sent in sents:
        # featurize STREUSLE structured annotations into MISC format
        add_gov_obj(sent)   # add govobj info
        miscattrs: dict[int,dict[str,str]] = defaultdict(dict)
        swes, smwes, wmwes = sent['swes'], sent['smwes'], sent['wmwes']

        for swe in swes.values():
            target: dict[str,str] = miscattrs[swe['toknums'][0]]
            load_ss(swe, sent['toks'], target)
            #print(swe['toknums'][0], target)
        for smwe in smwes.values():
            target: dict[str,str] = miscattrs[smwe['toknums'][0]]
            load_ss(smwe, sent['toks'], target)
            load_mwe(smwe, sent['toks'], target)
        for wmwe in wmwes.values():
            target: dict[str,str] = miscattrs[wmwe['toknums'][0]]
            load_mwe(wmwe, sent['toks'], target, weak=True)


        # headers
        sent_id = sent["sent_id"]
        doc_id, sent_num = sent_id.rsplit('-', 1)
        if doc_id!=curDocId:
            result += f'# newdoc id = {doc_id}\n'
            curDocId = doc_id
        result += f'# sent_id = {sent_id}\n'
        for extra_meta_ln in sent.get("extra_meta",[]):
            result += extra_meta_ln + '\n'
        result += f'# text = {sent["text"]}\n'
        result += f'# streusle_sent_id = {sent["streusle_sent_id"]}\n'
        result += f'# mwe = {sent["mwe"]}\n'

        # body

        # merge regular and ellipsis tokens
        toks = sent["toks"]
        for etok in reversed(sent["etoks"]):
            part1, part2, s = etok["#"]
            etok["#"] = s
            toks.insert(part1-1 if '-' in s else part1, etok)
        for tok in toks:
            assert "misc" in tok,"Ensure JSON was generated with MISC column included"
            if (newattrs := miscattrs[tok["#"]]):
                if tok["misc"] is None:
                    tok["misc"] = []

                # strip out any preexisting STREUSLE annotations in MISC
                for i in range(len(tok["misc"])-1, -1, -1):
                    if tok["misc"][i].startswith(STREUSLE_FIELDS):
                        tok["misc"].pop(i)

                # insert current STREUSLE annotations
                tok["misc"].extend(k+'='+v for k,v in newattrs.items())
                tok["misc"].sort(key=lambda s: s[:s.index('=')])
            tok["misc"] = '_' if tok["misc"] is None else '|'.join(tok["misc"])

            isEllipsis = isMWT = False
            if isinstance(tok["#"], str):
                if '.' in tok["#"]:
                    isEllipsis = True
                elif '-' in tok["#"]:
                    isMWT = True

            row = []
            for fld in CONLLU:
                v = tok[CONLLU_TO_JSON_FIELDS.get(fld, fld.lower())]
                if not v and v!=0:
                    assert isEllipsis or isMWT or fld in ('FEATS', 'MISC'),(fld,v)
                    v = '_'
                row.append(str(v))

            result += '\t'.join(row) + '\n'

        result += '\n'

    return result

if __name__=='__main__':
    inFname, = sys.argv[1:]

    with open(inFname, encoding='utf-8') as inF:
        sents = json.load(inF)
        output = build_conllu(sents)
        print(output, end='')
