#!/usr/bin/env python3

import sys, re, json, fileinput, glob

from helpers import sentences, streusle_annos

REVIEWSDIR='UD_English-EWT/not-to-release/sources/reviews'

EWT_HAS_STREUSLE = True    # If false, need to copy over all STREUSLE annotations.

STREUSLE_CONLLU=sys.argv[1]

# load UD data

ud = {}
udDocs = glob.glob(f'{REVIEWSDIR}/*.xml.conllu')
for udDoc in udDocs:
    for sent in sentences(udDoc):
        ud[sent.meta_dict['sent_id']] = (udDoc, sent)

nSentsChanged = nToksChanged = nToksAdded = nTagsChanged = nLemmasChanged = nMorphChanged = nDepsChanged = nEDepsChanged = nAutoLemmaFix = nAutoUPOSLexcatFix = nMiscChanged = 0
for sent in sentences(STREUSLE_CONLLU):
    # "old" = from local STREUSLE repo, "new" = from EWT repo
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
                elif tok.misc==newudtok.misc:
                    print(oldud, newud, sep='\n', file=sys.stderr)
                    assert False,'Unexpected change in UD (see last 2 data lines above)'
                
                if tok.misc!=newudtok.misc:
                    if not EWT_HAS_STREUSLE:
                        omisc = '' if tok.misc=='_' else tok.misc
                        nmisc = '' if newudtok.misc=='_' else newudtok.misc
                        # ensure the only changes to MISC are the STREUSLE fields
                        streusle_fields = streusle_annos(omisc)
                        other_change = False
                        if omisc:
                            for x in omisc.split('|'):
                                if not (x in streusle_fields or x in nmisc.split('|')):
                                    other_change = True
                                    break
                        if nmisc:
                            for x in nmisc.split('|'):
                                if x not in omisc.split('|'):
                                    other_change = True
                                    break

                        # record the changes
                        if streusle_fields:
                            if not other_change:
                                # auto-add the STREUSLE fields
                                newudtok.misc = tok.misc
                            elif tok.misc=='Supersense=n.LOCATION' and newudtok.misc=='Superlocation=Yes':
                                newudtok.misc = 'Superlocation=Yes|Supersense=n.LOCATION'
                            elif tok.misc=='SpaceAfter=No|Supersense=n.LOCATION' and newudtok.misc=='SpaceAfter=No|Superlocation=Yes':
                                newudtok.misc = 'SpaceAfter=No|Superlocation=Yes|Supersense=n.LOCATION'
                            else:
                                # need to manually merge as there are both STREUSLE and new non-STREUSLE MISC fields
                                print(tok, newudtok, sep='\n', file=sys.stderr)
                                assert False,'Unexpected change in MISC: need to manually update the local STREUSLE file first'
                        elif other_change:
                            nMiscChanged += 1
                    else:
                        nMiscChanged += 1
            else:
                nToksAdded += 1

        print(newudtok)
        # NOTE: lemmas updated in column 3 need to be manually fixed in the STREUSLE columns
        # These will be caught by running conllu2json.py
    if sentChanged:
        nSentsChanged += 1
    print()

print(f'Changes to {nToksChanged} tokens ({nToksAdded} new tokens + {nTagsChanged} tags + {nDepsChanged} additional deps + {nLemmasChanged} additional lemmas + {nMorphChanged} additional morphology + {nEDepsChanged} additional enhanced deps + {nMiscChanged} total MISC) in {nSentsChanged} sentences', file=sys.stderr)
print(f'{nAutoLemmaFix} STREUSLE single-word lemmas were automatically fixed, but multiword lemmas may need to be fixed manually', file=sys.stderr)
print(f'{nAutoUPOSLexcatFix} single-word UPOS/Lexcat tags were automatically fixed, but multiword lemmas may need to be fixed manually', file=sys.stderr)
