#!/usr/bin/env python3

import sys, re, json, fileinput, glob

from helpers import sentences

REVIEWSDIR='UD_English/not-to-release/sources/reviews'

CONLLULEX=sys.argv[1]

# load UD data

ud = {}
udDocs = glob.glob(f'{REVIEWSDIR}/*.xml.conllu')
for udDoc in udDocs:
    for sent in sentences(udDoc):
        ud[sent.meta_dict['sent_id']] = (udDoc, sent)

nSentsChanged = nToksChanged = nTagsChanged = nLemmasChanged = nDepsChanged = 0
for sent in sentences(CONLLULEX):
    # metadata shouldn't change (assume tokenization hasn't changed)
    print(*sent.meta, sep='\n')
    newudDoc, newudsent = ud[sent.meta_dict['sent_id']]
    assert len(sent.tokens)==len(newudsent.tokens)
    sentChanged = False
    for tok,newudtok in zip(sent.tokens,newudsent.tokens):
        oldud = '\t'.join(tok.orig.split('\t')[:10])
        newud = '\t'.join(newudtok.orig.split('\t')[:10])
        if oldud!=newud:
            nToksChanged += 1
            sentChanged = True
            if tok.ud_pos=='ADJ' and newudtok.ud_pos=='VERB':
                print(f'ADJ/VERB issue: need to revert to VERB in {newudDoc}: {tok.word}', file=sys.stderr)

            if tok.ud_pos!=newudtok.ud_pos or tok.ptb_pos!=newudtok.ptb_pos:
                nTagsChanged += 1
            elif tok.head!=newudtok.head or tok.deprel!=newudtok.deprel:
                print(oldud,newud,file=sys.stderr)
                nDepsChanged += 1
            elif tok.lemma!=newudtok.lemma:
                nLemmasChanged += 1
            else:
                assert False,(oldud,newud)
        streusle = '\t'.join(tok.orig.split('\t')[10:])
        print(f'{newud}\t{streusle}')
        # NOTE: lemmas updated in column 3 need to be manually fixed in the STREUSLE columns
        # These will be caught by running conllulex2json.py
    if sentChanged:
        nSentsChanged += 1
    print()

print(f'Changes to {nToksChanged} tokens ({nTagsChanged} tags + {nDepsChanged} additional deps + {nLemmasChanged} additional lemmas) in {nSentsChanged} sentences', file=sys.stderr)
