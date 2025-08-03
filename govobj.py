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

- the cat *in front of* the car:         gov=cat,     obj=car, config=default
- the cat sitting *in front of* the car: gov=sitting, obj=car, config=default
- the cat is *in front of* the car:      gov=cat,     obj=car, config=predicative

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

COPULAR STRANDING:
- the city I'm *in*:          gov=I, obj=city, config=predicative+stranded

AS-AS:
- eat *as* much as you can:            gov=eat,  obj=much,  config=default
- he is *as* tall as a horse:          gov=he,   obj=tall,  config=predicative
- he is as tall *as* a horse:          gov=tall, obj=horse, config=default
- he is as tall *as* a horse is wide:  gov=tall, obj=horse, config=subordinating


(Not handled: "the store is a pleasure to be in", obj=store)

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

def enhance(sent):
    """
    For tokens where deprel is "conj", use Enhanced Dependencies to get a propagated head.
    """
    for tok in sent['toks']:
        if tok['deprel']=='conj':
            assert tok['edeps']
            edeps = [ed for ed in tok['edeps'].split('|') if ':conj' not in ed]
            tok['bhead'] = tok['head']
            tok['bdeprel'] = tok['deprel']
            if not edeps:   # essentially a root
                tok['head'] = 0
                tok['deprel'] = 'root'
            else:   # arbitrarily choose the first of the enhanced deprels that are not conj
                ed = edeps[0].split(':')
                tok['head'] = int(ed[0].split('.')[0])  # if a copy node, e.g. "7.1", set head to 7
                tok['deprel'] = ed[1]

def deenhance(sent):
    """
    Reinstate Basic Dependencies deprels.
    """
    for tok in sent['toks']:
        if 'bhead' in tok:
            tok['head'] = tok['bhead']
            tok['deprel'] = tok['bdeprel']
            del tok['bhead']
            del tok['bdeprel']

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

def findobl(tok, sent):
    t = tok['#']
    for tok2 in sent['toks']:
        if tok2['head']==t and tok2['deprel'] in {'obl:npmod'}:
            return tok2
    return None

def findgovobj(pexpr, sent):
    plemma = pexpr['lexlemma']
    t1 = pexpr['toknums'][0]
    tlast = pexpr['toknums'][-1]
    tok1 = sent['toks'][t1-1]
    toklast = sent['toks'][tlast-1]
    prel = tok1['deprel']

    config = None   # possible non-None values: possessive, subordinating, stranded, predicative
    if prel=='nmod:poss':
        config = 'possessive'
    elif prel=='mark':
        config = 'subordinating'

    # pptop: the highest node in the PP or subordinate clause (not counting extracted objects)

    otok = None
    if tlast>t1 and toklast['head']>0 and toklast['deprel'] in {'case', 'mark'}:
        # multiword prep, e.g. 'out of', 'in front of', 'as long as'
        otok = sent['toks'][toklast['head']-1]

    if prel in {'case', 'mark'}:
        pptop = sent['toks'][tok1['head']-1] if tok1['head']>0 else None
        if otok is None:
            otok = pptop

        # We need a bunch of heuristics to deal with syntactically weird constructions/expressions.
        # Note that the governor of a SNACS (p.* supersense) expression shouldn't be another SNACS expression, with a few rare exceptions:
        # - copular intransitive P + PP: I was in two weeks AGO: gov = "in"; "they were out FOR the day": gov = "out"
        # - possessives in idiomatic PPs: "on_ our _way", "on_ my _own", etc.

        if tok1['lemma']=='as' and sent['toks'][pptop['head']-1]['lemma']=='as': # 2nd AS in as-as construction
            pptop = sent['toks'][pptop['head']-1]   # essentially treat the object of the first AS as the governor of the 2nd AS. "as tall AS a horse": gov = tall, obj = horse
        elif prel=='case' and sent['toks'][pptop['head']-1]['upos']=='ADV' and pptop['deprel'] in ('obl', 'nmod') \
            and sent['toks'][pptop['head']-1]['lemma'] in ('back', 'down', 'out', 'over', 'away', 'home') \
            and not (sent['toks'][pptop['head']-1]['smwe'] and sent['toks'][pptop['head']-1]['smwe'][1]>1) \
            and not findcop(sent['toks'][pptop['head']-1], sent):
            # correct for weird (and inconsistent) UD analysis where intransitive adposition (ADV) has a PP complement:
            # "got back FROM france", "made back IN the 60s", "drive 10 minutes more down TO Stevens_Creek", "over BY 16th and 15th"
            pptop = sent['toks'][pptop['head']-1]
            assert not findcop(pptop, sent),(plemma,pptop)
    elif plemma in ('ago', 'hence'):    # we consider these postpositions, UD considers them adverbs with extent modifiers (obl:npmod)
        pptop = tok1
        otok = findobl(tok1, sent)
    elif prel=='advmod' and tok1['head'] > t1:
        pptop = sent['toks'][tok1['head']-1]
        if tok1['lemma']=='as': # first AS in as-as construction, as_soon_as, as_long_as
            otok = pptop    # "tall" in "as tall as a horse"
        elif tok1['head'] in pexpr['toknums']:    # idiomatic PPs of the form advmod(w2,w1): just_about, out_there, up_front, at_first
            if sent['toks'][tok1['head']-1]['head'] > tok1['head'] and sent['toks'][tok1['head']-1]['deprel']=='advmod':    # just_about
                otok = pptop    # "everything" in "just about everything"
            # else out_there, up_front, at_first: no obj
        elif pptop['upos']=='ADV':  # "back home", "down there" (also "over and over")
            pass    # treat "back", "down" as intransitive particles (otok = None), use governor of "home"/"there" as the governor of the preposition
        elif len(pexpr['toknums'])==1 and sent['toks'][t1+1-1]['upos']=='ADP' and sent['toks'][t1+1-1]['head']==tok1['head']:   # "back between" X and Y, "bank in June", "back to me"
            # treat "back" as intransitive particle (otok = None)
            pass
        elif len(pexpr['toknums'])==2 and sent['toks'][pexpr['toknums'][1]-1]['head']==t1 and sent['toks'][pexpr['toknums'][1]-1]['deprel']=='fixed':
            if plemma=='at least':  # "at_least pretend to be helpful", fixed(at, least): no object
                pptop = tok1
                # Note that Approximator "at_least" is right-headed: "at least 10 more minutes": case(least, at)
            else:   # "all_of 10 minutes", "less_than an hour" (Approximators): treat as transitive P with no governor
                otok = pptop
                pptop = tok1
        elif plemma in ('about', 'around', 'like', 'over'): # single-word Approximators: "about", "around", "like", "over".
            #assert pexpr['ss']=='p.Approximator'
            # In UD treated as advmod of the measured expression. We treat as transitive P with no governor.
            otok = pptop
            pptop = tok1

        elif len(pexpr['toknums'])>1:
            pass
        else:   # adverb fronted before verb: "We have since moved", "I've never before felt...", "never before has...", "off we went"
            pptop = tok1    # intransitive
    else:
        pptop = tok1
        #if otok is None, no (local) object/complement

    gtok = sent['toks'][pptop['head']-1] if pptop['head']>0 else None

    # is it a stranded preposition?
    # UD-EWT is actually inconsistent: sometimes it promotes the preposition
    # as if the NP is elided; in other cases there is a nonprojective `case`
    # dependency (the "right" way): https://github.com/UniversalDependencies/UD_English-EWT/issues/87
    if tok1['xpos']=='IN':
        if prel not in {'case', 'mark'}:
            # the ellipsis analysis
            if gtok and gtok['deprel'] in {'acl:relcl', 'acl', 'advcl'}:
                # (some other gtok['deprel'] values aren't handled: weirdness mainly with coordination and copular constructions)
                config = 'stranded'

                # preposition stranding in relative clause or adjective raising (exclude particle in relative clause)
                otok = sent['toks'][gtok['head']-1] if gtok['head']>0 else None
                if gtok['deprel']=='advcl': # adjective raising: e.g. "She was easy to work with": otok is "easy"
                    # (not foolproof)
                    subjtok = findsubj(otok, sent)
                    otok = subjtok  # "She"; may be None
            elif prel=='acl:relcl': # stranding in copular relative clause, e.g. "the city I'm in"
                config = 'stranded'
                otok = gtok
        elif otok['#'] < tok1['#']: # head is to the left
            config = 'stranded'

    # is it a predicative PP or subordinate copular clause?
    coptok = findcop(pptop, sent)
    if coptok:
        if config=='subordinating':
            otok = coptok   # subordinate copular clause: use copula as the object instead of the content predicate
        elif not config or config=='stranded':    # technically a preposition can be both stranded and predicative: "the worst store I have been in". just label it stranded.
            config = 'predicative+stranded' if config=='stranded' else 'predicative'
            # look for subject
            subjtok = findsubj(pptop, sent)
            gtok = subjtok  # may be None

    if not config:
        config = 'default'

    if gtok==otok!=None:
        # Approximators ("about 4 bucks"): remove the governor
        gtok = None

    pexpr['heuristic_relation'] = {
             'gov': gtok['#']     if gtok else None,
        'govlemma': gtok['lemma'] if gtok else None,
             'obj': otok['#']     if otok else None,
        'objlemma': otok['lemma'] if otok else None,
          'config': config
    }

    #print(sent['mwe'], (gtok['word'], plemma, otok['word']), config)

def add_gov_obj(sent):
    enhance(sent)   # apply Enhanced Dependencies instead of superficial conj relations for coordination
    for lexe in chain(sent['swes'].values(), sent['smwes'].values()):
        if lexe['lexcat'] in {'P','PP','INF.P','POSS','PRON.POSS'}:
            gov = findgovobj(lexe, sent)
    deenhance(sent) # now that we've extracted prepositional/possessive gov & obj, revert to Basic Dependencies in the output

if __name__=='__main__':
    with open(sys.argv[1], encoding='utf-8') as inF:
        data = json.load(inF)

    for sent in data:
        add_gov_obj(sent)

    print(json.dumps(data, indent=1))
