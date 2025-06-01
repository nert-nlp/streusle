#!/usr/bin/env python3

import sys, re, json, fileinput, glob

from helpers import sentences

REVIEWSDIR='UD_English-EWT/not-to-release/sources/reviews'

CONLLULEX=sys.argv[1]

# load UD data

ud = {}
udDocs = glob.glob(f'{REVIEWSDIR}/*.xml.conllu')
for udDoc in udDocs:
    for sent in sentences(udDoc):
        ud[sent.meta_dict['sent_id']] = (udDoc, sent)

nSentsChanged = nToksChanged = nToksAdded = nTagsChanged = nLemmasChanged = nMorphChanged = nDepsChanged = nEDepsChanged = nAutoLemmaFix = nAutoUPOSLexcatFix = nMiscChanged = 0
for sent in sentences(CONLLULEX):
    newudDoc, newudsent = ud[sent.meta_dict['sent_id']]
    if len(sent.tokens)!=len(newudsent.tokens):
        print(f"Number of tokens for sentence {sent.meta_dict['sent_id']} has changed", file=sys.stderr)
    sentChanged = False
    oldudtoks = {t.offset: t for t in sent.tokens}
    assert len(oldudtoks)==len(sent.tokens)

    # ensure UD sentence metadata lines are present (before STREUSLE-specific metadata lines)
    assert len(newudsent.meta)<len(sent.meta)
    if sent.meta[:len(newudsent.meta)] != newudsent.meta:
        # incorporate new UD metadata
        for entry in newudsent.meta:
            print(entry)
        for entry in sent.meta:
            if entry not in newudsent.meta: # STREUSLE-specific (assumes UD lines already in STREUSLE are unchanged in new UD)
                print(entry)
    else:
        print(*sent.meta, sep='\n')

    for newudtok in newudsent.tokens:
        tok = oldudtoks.get(newudtok.offset)
        oldud = '\t'.join(tok.orig.split('\t')[:10]) if tok else None   # newud may be a new ellipsis node
        newud = '\t'.join(newudtok.orig.split('\t')[:10])
        if oldud!=newud:
            nToksChanged += 1
            sentChanged = True

            if tok:
                if tok.ud_pos=='ADJ' and newudtok.ud_pos=='VERB':
                    print(f'ADJ/VERB issue: need to revert to VERB in {newudDoc}: {tok.word}', file=sys.stderr)

                if tok.ud_pos!=newudtok.ud_pos or tok.ptb_pos!=newudtok.ptb_pos:
                    nTagsChanged += 1
                    print(oldud,newud, sep='\n', file=sys.stderr)
                elif tok.head!=newudtok.head or tok.deprel!=newudtok.deprel:
                    print(oldud,newud, sep='\n', file=sys.stderr)
                    nDepsChanged += 1
                elif tok.lemma!=newudtok.lemma:
                    print(oldud,newud, sep='\n', file=sys.stderr)
                    nLemmasChanged += 1
                elif tok.morph!=newudtok.morph:
                    nMorphChanged += 1
                elif tok.edeps!=newudtok.edeps:
                    nEDepsChanged += 1
                elif tok.misc!=newudtok.misc:
                    nMiscChanged += 1
                else:
                    print(oldud, newud, sep='\n', file=sys.stderr)
                    assert False,'Unexpected change in UD (see last 2 data lines above)'
            else:
                nToksAdded += 1

        if tok:
            streusle = tok.orig.split('\t')[10:]
            old_lexcat = streusle[1]
            old_strong_lemma = streusle[2]
            old_lextag = streusle[8]
            if old_strong_lemma!='_' and tok.lemma!=newudtok.lemma and old_strong_lemma==tok.lemma:
                streusle[2] = newudtok.lemma
                nAutoLemmaFix += 1
            if old_lexcat!='_' and old_lextag=='O-'+old_lexcat and tok.ud_pos!=newudtok.ud_pos:
                assert (old_lexcat==tok.ud_pos 
                    or old_lexcat=='PRON' and old_lextag=='O-PRON' and tok.ud_pos=='NOUN'
                    or old_lexcat=='DISC' and newudtok.ud_pos=='INTJ'),(old_lextag,tok.ud_pos,newudtok.ud_pos)
                # 'other', 'none', 'one' in some cases had UPOS NOUN/lexcat PRON

                newlexcat = {'ADP': 'P', 'NOUN': 'N', 'PROPN': 'N', 'VERB': 'V'}.get(newudtok.ud_pos, newudtok.ud_pos)
                if newlexcat=='N' and newudtok.lemma in ('etc.','etc','one'):
                    newlexcat = 'PRON'
                streusle[1] = newlexcat
                streusle[8] = 'O-'+newlexcat
                nAutoUPOSLexcatFix += 1
        else:
            streusle = '_'*9

        streusle = '\t'.join(streusle)
        print(f'{newud}\t{streusle}')
        # NOTE: lemmas updated in column 3 need to be manually fixed in the STREUSLE columns
        # These will be caught by running conllulex2json.py
    if sentChanged:
        nSentsChanged += 1
    print()

print(f'Changes to {nToksChanged} tokens ({nToksAdded} new tokens + {nTagsChanged} tags + {nDepsChanged} additional deps + {nLemmasChanged} additional lemmas + {nMorphChanged} additional morphology + {nEDepsChanged} additional enhanced deps + {nMiscChanged} additional MISC) in {nSentsChanged} sentences', file=sys.stderr)
print(f'{nAutoLemmaFix} STREUSLE single-word lemmas were automatically fixed, but multiword lemmas may need to be fixed manually', file=sys.stderr)
print(f'{nAutoUPOSLexcatFix} single-word UPOS/Lexcat tags were automatically fixed, but multiword lemmas may need to be fixed manually', file=sys.stderr)
