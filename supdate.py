#!/usr/bin/env python3
"""
Incorporate edits to annotations in the human-readable inline rendered format
(output by streusvis.py) and produce the modified corpus as JSON.

Usage:

  ./streusvis.py --sent-ids --lexcats --colorless streusle.conllulex > updates.tsv

  [manually edit annotations in updates.tsv]

  ./tupdate.py streusle.conllulex updates.tsv > streusle.new.json

updates.tsv must contain 2 tab-separated columns: sentence IDs and rendered sentences.
The rendered sentence may be split across multiple consecutive lines,
with the sentence ID specified only in the first of these.

The sentences in updates.tsv will be compared against the ones in streusle.conllulex,
and only the ones with modified annotations will be processed (so including
unmodified sentences in updates.tsv is optional).

This script will not add or delete sentences from the corpus, or alter
their tokenization or syntactic parse.

@author: Nathan Schneider (nschneid)
@since: 2019-09-16
"""

import sys, re

from conllulex2json import load_sents, print_json
from conllulex2UDlextag import simplify_to_UDlextag
from UDlextag2json import load_sents as load_UDlextag_sents
from mwerender import render, render_sent, unrender

conllulexFP, updatesFP = sys.argv[1:]

"""
ALGORITHM OVERVIEW

For any sentence where the lextags have changed:

a) Convert the JSON for the sentence to conllulex.
b) Strip out the lexical semantic analyses.
c) Parse (unrender) the human-readable string with MWEs, lextags, and supersenses
into a tagging.
c) Substitute the modified lextags in the last column.
d) Convert the modified UDlextag to JSON.
e) Re-render the sentence to make sure it matches what the user specified.
"""

"""
1. Load streusvis.py-created file with potential updates to be made.
It must contain 2 tab-separated columns: sentence IDs and rendered sentences.
The rendered sentence may be split across multiple consecutive lines,
with the sentence ID specified only in the first of these.
"""
updates = {}
with open(updatesFP, encoding='utf-8') as updatesF:
    sentid = None
    for ln in updatesF:
        if not ln.strip():
            sentid = None
            continue
        ln = ln.rstrip()
        s, r = ln.split('\t')
        if s:
            sentid = s
            assert sentid not in updates
            updates[sentid] = r
        else:   # continuation of second column from previous line
            assert sentid
            updates[sentid] += ' ' + r

"""
2. Scan the full corpus .conllulex for sentences with their original annotations.
If there was a change, parse the rendered lexical semantic analysis into tags,
substitute the tags in the UDlextag format, and parse the sentence to JSON in
order to update the fields: 'mwe', 'toks', 'swes', 'smwes', 'wmwes'
('etoks' etc. will be unaffected).
"""
sents = []
with open(conllulexFP, encoding='utf-8') as conllulexF:
    nUpdatedSents = 0
    for sent in load_sents(conllulexF, store_conllulex='toks'):
        sentid = sent['sent_id']
        if sentid in updates:
            # compare rendered strings to see whether there has been a change
            rendered_old = render_sent(sent, lexcats=True, supersenses=True)
            rendered_new = updates[sentid]
            if rendered_old!=rendered_new:  # there has been a change
                # parse the new rendered string
                toks = [tok['word'] for tok in sent['toks']]
                tagging = unrender(rendered_new, toks)  # this should fail if tokens have changed
                toks2, bios, lbls = zip(*tagging)
                assert toks==list(toks2),(toks,toks2)  # be super-duper sure tokens haven't changed
                labeled_bio = [bio+('-'+lbl if lbl else '') for bio,lbl in zip(bios,lbls)]

                # substitute new tagging in UDlextag format
                conllulex = sent['conllulex'].strip().split('\n')
                udlextag = simplify_to_UDlextag(conllulex)
                assert udlextag.count('\n')==len(toks),(udlextag.count('\n'),len(toks),udlextag)
                lines = udlextag.split('\n')
                for i in range(len(labeled_bio)):
                    ln = lines[i]
                    newtag = labeled_bio[i]
                    lines[i] = ln[:ln.rindex('\t')] + '\t' + newtag

                # parse the new CoNLL-U-Lex
                newsent = next(load_UDlextag_sents(lines))

                # update fields
                for fld in ('mwe', 'toks', 'swes', 'smwes', 'wmwes'):
                    sent[fld] = newsent[fld]

                # re-render the sentence as a sanity check
                rendered2 = render_sent(sent, lexcats=True, supersenses=True)
                assert rendered2==rendered_new

                nUpdatedSents += 1
        del sent['conllulex']
        sents.append(sent)

# output the modified corpus
print_json(sents)

print(f'Reviewed inputs for {len(updates)} sentences and implemented updates to {nUpdatedSents} of them', file=sys.stderr)
