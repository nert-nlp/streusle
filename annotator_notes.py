#!/usr/bin/env python3


"""
Given a STREUSLE 4 JSON file, augments it with annotators' sentence-level and lexical-level 
comments/notes from CSV files. The sentence-level JSON field is called "note" and the 
lexical-level field is called "annotator_cluster".

@author: Nathan Schneider (@nschneid)
@since: 2018-06-15
"""

import csv, json, os, sys
from collections import defaultdict
from itertools import chain

toknote_files = ['prepv-tokens.csv',
         'psst-tokens-revisions.csv',
         'allbacktick-tokens-revisions.csv']
         
sentnote_files = ['current-psst_20150830.sentnotes.csv']

# CSV field names
SENTID = 'sent ID'
SENTNOTE = 'sent_note'
TOKID = 'sent ID' # sentID:tokID
TOKNOTE = 'note'

# Assemble the sentence-level notes
sentnotes = {}  # sentID -> str

for f in sentnote_files:
    with open(f, 'r', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sentid = row[SENTID]
            note = row[SENTNOTE]
            if not note.strip(): continue
            if sentid not in sentnotes:
                sentnotes[sentid] = note
            else:
                assert False,(sentnotes[sentid],note)

# Assemble the token-level (actually lexical-level) notes
toknotes = defaultdict(dict)    # sentID -> tokID -> str

for f in toknote_files:
    with open(f, 'r', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tokid = row[TOKID]    # token id
            note = row[TOKNOTE]
            if not note.strip(): continue
            if f.startswith('prepv'):
                note = 'prepV?: ' + note            
            
            sentid, toknum = tokid.split(':')
            toknum = int(toknum) + 1 # index of first token in lexical expression; sst format indices start at 1
            if tokid not in toknotes:
                toknotes[sentid][toknum] = note
            else:
                assert False,(toknotes[tokid],note)

#for k,v in sentnotes.items():
#    print(k,v, sep='\t')
#for k,v in toknotes.items():
#    print(k,v, sep='\t')

# Apply notes to the JSON
with open(sys.argv[1], 'r', encoding='utf8') as inF:
    data = json.load(inF)

nSent = nLex = 0
for sent in data:
    sentid = sent['streusle_sent_id']
    if sentid in sentnotes:
        sent['note'] = sentnotes[sentid]
        nSent += 1
    if sentid in toknotes:
        notetoknums = set(toknotes[sentid].keys())
        for lexe in chain(sent["swes"].values(), sent["smwes"].values()):
            toknums = set(lexe["toknums"])
            intersect = toknums & notetoknums
            if intersect:
                note = ' | '.join(toknotes[sentid][i] for i in sorted(intersect))
                if len(intersect)>1:
                    print(note, file=sys.stderr)
                lexe["annotator_cluster"] = note
                nLex += 1

print(nSent, nLex, file=sys.stderr)

print(json.dumps(data, indent=1))
