#!/usr/bin/env python3
"""
Given a STREUSLE JSON file, adds syntactic governor and object information
to prepositional/possessive expressions by processing the (basic) UD syntax tree.
There are heuristics to account for predicative PPs, preposition stranding,
possessives, subordinators, etc. See the examples below:

TRANSITIVE P + NP:
- the cat *in* the car:         gov=cat,     obj=car, config=default
- the cat sitting *in* the car: gov=sitting, obj=car, config=default
- the cat is *in* the car:      gov=cat,     obj=car, config=predicative

[Note that the obj slot will contain the syntactic object even for
an idiomatic multiword PP.]

INTRANSITIVE P:
- the cat is going *inside*: gov=going, obj=NONE, config=default
- the cat is *inside*:       gov=cat,   obj=NONE, config=predicative
- it took *about* a year:    gov=year,  obj=NONE, config=default

POSSESSIVE:
- the cat *'s* fur: gov=fur, obj=cat,  config=possessive
- *his* fur:        gov=fur, obj=NONE, config=possessive
  [The possessive marker is the pronoun; there is no separate object.]

SUBORDINATION:
- we arrived *before* eating: gov=arrived, obj=eating, config=subordinating
- we arrived *before* we ate: gov=arrived, obj=ate,    config=subordinating
- we arrived *before* we were hungry: gov=arrived, obj=were, config=subordinating
- we arrived *to* eat dinner: gov=arrived, obj=eat,    config=subordinating
- we arrived *to* be first in line: gov=arrived, obj=be, config=subordinating

STRANDING:
- everyone I work *with*:     gov=work, obj=everyone, config=stranded
- she is easy to work *with*: gov=work, obj=she,      config=stranded


JSON output sample for 'my grandfather'--the added information is under "heuristic_relation":

{...
 "swes": {
   "1": {
    "lexlemma": "my", "lexcat": "PRON.POSS", "ss": "p.SocialRel", "ss2": "p.Possessor",
    "toknums": [1],
    "heuristic_relation": {
      "gov": 2,    "govlemma": "grandfather",
      "obj": null, "objlemma": null,
      "config": "possessive"
    }
   },
   "2": {
    "lexlemma": "grandfather", "lexcat": "N", "ss": "n.PERSON", "ss2": null,
    "toknums": [2]
   }
 }
 ...
}

@author: Nathan Schneider (@nschneid)
@since: 2018-01-31
"""

import sys, json
from collections import Counter
from itertools import chain

def findsubj(tok, sent):
    t = tok['#']
    for tok2 in sent['toks']:
        if tok2['head']==t and tok2['deprel'] in {'nsubj','nsubj:pass','csubj','csubj:pass','expl'}:
            return tok2
    return None

def findcop(tok, sent):
    t = tok['#']
    for tok2 in sent['toks']:
        if tok2['head']==t and tok2['deprel'] in {'cop'}:
            return tok2
    return None

def findgovobj(pexpr, sent):
    plemma = pexpr['lexlemma']
    t1 = pexpr['toknums'][0]
    tok1 = sent['toks'][t1-1]
    prel = tok1['deprel']

    config = None   # possible non-None values: possessive, subordinating, stranded, predicative
    if prel=='nmod:poss':
        config = 'possessive'
    elif prel=='mark':
        config = 'subordinating'

    # pptop: the highest node in the PP or subordinate clause (not counting extracted objects)

    if prel in {'case', 'mark'}:
        pptop = sent['toks'][tok1['head']-1] if tok1['head']>0 else None
        otok = pptop
    else:
        pptop = tok1
        otok = None   # no (local) object/complement

    gtok = sent['toks'][pptop['head']-1] if pptop['head']>0 else None

    # is it a stranded preposition?
    if prel not in {'case', 'mark'} and tok1['xpos']=='IN' and gtok and gtok['deprel'] in {'acl:relcl', 'acl', 'advcl'}:
            # (some other gtok['deprel'] values aren't handled: weirdness mainly with coordination and copular constructions)
            config = 'stranded'

            # preposition stranding in relative clause or adjective raising (exclude particle in relative clause)
            otok = sent['toks'][gtok['head']-1] if gtok['head']>0 else None
            if gtok['deprel']=='advcl': # adjective raising: e.g. "She was easy to work with": otok is "easy"
                # (not foolproof)
                subjtok = findsubj(otok, sent)
                otok = subjtok  # "She"; may be None

    # is it a predicative PP or subordinate copular clause?
    coptok = findcop(pptop, sent)
    if coptok:
        if config=='subordinating':
            otok = coptok   # subordinate copular clause: use copula as the object instead of the content predicate
        elif not config:    # technically a preposition can be both stranded and predicative: "the worst store I have been in". just label it stranded.
            config = 'predicative'
            # look for subject
            subjtok = findsubj(pptop, sent)
            gtok = subjtok  # may be None

    if not config:
        config = 'default'

    pexpr['heuristic_relation'] = {
             'gov': gtok['#']     if gtok else None,
        'govlemma': gtok['lemma'] if gtok else None,
             'obj': otok['#']     if otok else None,
        'objlemma': otok['lemma'] if otok else None,
          'config': config
    }

    #print(sent['mwe'], (gtok['word'], plemma, otok['word']), config)

with open(sys.argv[1], encoding='utf-8') as inF:
    data = json.load(inF)

for sent in data:
    for lexe in chain(sent['swes'].values(), sent['smwes'].values()):
        if lexe['lexcat'] in {'P','PP','INF.P','POSS','PRON.POSS'}:
            gov = findgovobj(lexe, sent)

print(json.dumps(data, indent=1))
