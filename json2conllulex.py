#!/usr/bin/env python3
"""
Given a file in the STREUSLE JSON format, convert it to the .conllulex format.
Relies on sentence IDs being in the format DOCID-SENTNUM, where SENTNUM contains no hyphens.

Args: inputfile

@since: 2019-06-22
@author: Nathan Schneider (@nschneid)
"""

import os, sys, fileinput, re, json, csv
from collections import defaultdict
from itertools import chain

CONLLU = ('ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC')
         # 1     2       3        4       5       6        7       8         9       10
STREUSLE = ('SMWE', 'LEXCAT', 'LEXLEMMA', 'SS', 'SS2', 'WMWE', 'WCAT', 'WLEMMA', 'LEXTAG')
           # 11      12        13          14    15     16      17      18        19

FIELDS = CONLLU + STREUSLE

# Naming is slightly different for some fields
CONLLU_TO_JSON_FIELDS = {'ID': '#', 'FORM': 'word', 'DEPS': 'edeps'}

def build_conllulex(sents):
    result = ''
    curDocId = None
    for sent in sents:
        # headers
        sent_id = sent["sent_id"]
        doc_id, sent_num = sent_id.rsplit('-', 1)
        if doc_id!=curDocId:
            result += f'# newdoc id = {doc_id}\n'
            curDocId = doc_id
        result += f'# sent_id = {sent_id}\n'
        result += f'# text = {sent["text"]}\n'
        result += f'# streusle_sent_id = {sent["streusle_sent_id"]}\n'
        result += f'# mwe = {sent["mwe"]}\n'

        # body

        # merge regular, ellipsis, multiword tokens
        toks = sent["toks"]
        for etok in reversed(chain(sent["etoks"],sent["mwtoks"])):
            before, subnum, s = etok["#"]
            etok["#"] = s
            toks.insert(before, etok)
        for tok in toks:
            isSpecial = isinstance(tok["#"], str)   # ellipsis or multiword token
            if isSpecial: assert '.' in tok["#"] or '-' in tok["#"]
            row = []
            for fld in CONLLU:
                v = tok[CONLLU_TO_JSON_FIELDS.get(fld, fld.lower())]
                if not v and v!=0:
                    assert isSpecial or fld in ('FEATS', 'MISC'),(fld,v)
                    v = '_'
                row.append(str(v))

            # SMWE
            if isSpecial:
                # this is an ellipsis token. it doesn't have any lexical semantic info
                row.extend(list('_'*9))
                result += '\t'.join(row) + '\n'
                continue
            elif tok["smwe"]:
                mweNum, position = tok["smwe"]
                row.append(f'{mweNum}:{position}') # e.g. 2:1
                if position==1:
                    lexe = sent["smwes"][str(tok["smwe"][0])]
                else:
                    lexe = None # we already printed info about this lexical expression
            else:
                row.append('_')
                lexe = sent["swes"][str(tok["#"])]

            # Properties of the (strong) lexical expression:
            # LEXCAT, LEXLEMMA, SS, SS2
            if lexe:
                assert lexe["lexcat"] and lexe["lexlemma"]
                row.extend([lexe["lexcat"], lexe["lexlemma"]])
                row.append(lexe["ss"] or '_')
                row.append(lexe["ss2"] or '_')
            else:
                row.extend(list('_'*4))

            # WMWE, WCAT, WLEMMA
            if tok["wmwe"]:
                mweNum, position = tok["wmwe"]
                row.append(f'{mweNum}:{position}')
                if position==1:
                    wmwe = sent["wmwes"][str(mweNum)]
                    assert wmwe["lexlemma"]
                    row.extend([wmwe["lexcat"] or '_', wmwe["lexlemma"]])
                else:
                    row.extend(['_', '_'])
            else:
                row.extend(['_', '_', '_'])

            # LEXTAG
            assert tok["lextag"]
            row.append(tok["lextag"])

            result += '\t'.join(row) + '\n'

        result += '\n'

    return result

if __name__=='__main__':
    inFname, = sys.argv[1:]

    with open(inFname, encoding='utf-8') as inF:
        sents = json.load(inF)
        output = build_conllulex(sents)
        print(output, end='')
