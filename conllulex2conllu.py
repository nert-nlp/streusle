desc = \
"""
Produces an integrated .conllu file where the lexical semantic information
is encoded via attributes in the MISC column.

MWE attributes
--------------

  - `MWECat` (lexical category of the MWE)
      UPOS values: `ADJ`, `ADV`, `AUX`, `CCONJ`, `DET`, `INTJ`, `NUM`, `PRON`,
        `SCONJ`, `SYM`
      Other values: `DISC` (discourse), `INF.P` (SNACS-labeled infinitival idiom),
        `N` (common or proper multiword noun expression), `P` (multiword preposition),
        `PP` (idiomatic prepositional phrase), and the verbal MWE subtypes:
        `V.IAV`, `V.LVC.cause`, `V.LVC.full`, `V.VID`, `V.VPC.full`, `V.VPC.semi`
  - `MWELemma` (sequence of word lemmas and gap-lengths, e.g. "go out of <1> way"
      for "went out of their way")
  - `MWEString` (surface forms if different from `MWELemma` beyond capitalization).
      N.B. `goeswith` tokens are separated by spaces in `MWEString` but not `MWELemma`.
  - `MWELen` (length of span from first to last token of the MWE)

The attributes are placed on the first word of the MWE.
Plain `MWECat`, `MWELemma`, `MWELen` togther represent a strong expression.
A weak expression is represented with `MWECat[weak]`, `MWELemma[weak]`, `MWELen[weak]`.

Supersense attributes
---------------------

  - `Supersense` (if there is only one, i.e. all nouns/verbs and many prepositions),
      *OR* `Supersense[coding]` (a.k.a. function) and `Supersense[scene]` (a.k.a. role).
      Noun and verb supersenses start with `n.` and `v.` respectively.
      SNACS supersenses start with `p.`, except for the special labels `` `$ ``
      (possessive slot in idiom) and `??` (ungrammatical/unintelligible).
      Other special labels are `` `d `` (single-word discourse expression tagged as a noun,
      verb, or preposition/possessive) and `` `j `` (single-word adjectival expression
      tagged as a verb).
  - `PRel[config]`, `PRel[gov]`, `PRel[obj]` (structure of the prepositional/possessive 
      relation associated with a SNACS supersense; some constructions lack a governor
      [approximator or PP idiom] or an object [intransitive P])

@author: Nathan Schneider (@nschneid)
@since: 2025-07-19
"""

import re
from collections import defaultdict
from argparse import ArgumentParser, FileType

from conllulex2json import load_sents
from govobj import add_gov_obj

def load_ss(exp, all_toks, target):
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
        elif exp['lexcat']=='ADJ' and all_toks[exp['toknums'][0]-1]['upos']=='VERB':
            target['Supersense'] = '`j'

def load_mwe(exp, all_toks, target, weak=False):
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
            # probably a 2-token goeswith expression so not a real MWE.
            # a few exceptions contain a goeswith within a larger MWE:
            if ' '.join(target[MWELemma_KEY]) in {'Award Dance Centre', 'in the meantime', 'go downhill', 'forget that'}:
                pass
            else:
                assert target[MWELen_KEY]=='2',(i,exp['toknums'],target,lemma_nongap_parts)
                target.clear()
                break
        else:
            part = lemma_nongap_parts.pop(0)
            target[MWELemma_KEY].append(part)
        prevI = i
    if target:
        target[MWELemma_KEY] = ' '.join(target[MWELemma_KEY])
        target[MWEString_KEY] = ' '.join(target[MWEString_KEY])
        if target[MWEString_KEY].lower()==target[MWELemma_KEY].lower():
            del target[MWEString_KEY]   # only include MWEString= if distinct from MWELemma= (inflection, typo)

if __name__ == '__main__':
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("inF", type=FileType(encoding="utf-8"))
    for sent in load_sents(argparser.parse_args().inF, store_conllulex='full'):
        conllulex: str = sent['conllulex']
        add_gov_obj(sent)   # add govobj info
        miscattrs = defaultdict(dict)
        swes, smwes, wmwes = sent['swes'], sent['smwes'], sent['wmwes']

        for swe in swes.values():
            target = miscattrs[swe['toknums'][0]]
            load_ss(swe, sent['toks'], target)
            #print(swe['toknums'][0], target)
        for smwe in smwes.values():
            target = miscattrs[smwe['toknums'][0]]
            load_ss(smwe, sent['toks'], target)
            load_mwe(smwe, sent['toks'], target)
        for wmwe in wmwes.values():
            target = miscattrs[wmwe['toknums'][0]]
            load_mwe(wmwe, sent['toks'], target, weak=True)
            
            #print(smwe['toknums'][0], target)
        for ln in conllulex.splitlines():
            if '\t' in ln:
                # remove extra columns
                ln = '\t'.join(ln.split('\t')[:10])
                if (m := re.match('^([0-9]+)\t', ln)):
                    tokid = m.group(1)
                    if (newattrs := miscattrs[int(tokid)]):
                        tailstripped = ln.strip()[:-1] if ln.strip()[-1]=='_' else ln.strip()+'|'
                        updatedln = tailstripped + '|'.join(k+'='+v for k,v in sorted(newattrs.items()))
                        ln = updatedln
            print(ln)
        print()
