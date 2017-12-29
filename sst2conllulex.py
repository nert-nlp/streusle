#!/usr/bin/env python3
"""
Given input in the .sst format, converts to the .conllulex format
(an extension of the tabular .conllu format with additional columns
for lexical semantics).

A path to the reviews subdirectory of the UD_English repository
is specified in a global variable.
"""

REVIEWSDIR = 'UD_English/not-to-release/sources/reviews'

import fileinput, json, re, sys

from lexcatter import compute_lexcat
from tagging import sent_tags

sentSSTData = []
docids = set()

for ln in fileinput.input():
    if ln.strip():
        sentid, mweMarkup, data = ln.strip().split('\t')
        data = json.loads(data)
        # STREUSLE sentence ID: ewtb.r.093655.7
        corpid, subcorpid, docid, sentnum = sentid.split('.')
        assert (corpid,subcorpid)==('ewtb','r'),sentid # reviews
        # infer UD sentence ID: reviews-093655-0007
        udsentid = f'reviews-{docid}-{int(sentnum):04}'
        sentSSTData.append((sentid, udsentid, mweMarkup, data))
        docids.add(docid)

ud = {}

for docid in docids:
    udFP = f'{REVIEWSDIR}/{docid}.xml.conllu'
    with open(udFP) as udF:
        udsentid = None
        sentMetaLines = []
        sentTokLines = []
        lemmas = []
        poses = []
        rels = []
        for ln in udF:
            if not ln.strip():
                assert udsentid is not None
                ud[udsentid] = (sentMetaLines, sentTokLines, lemmas, poses, rels)
                sentid = None
                sentMetaLines = []
                sentTokLines = []
                lemmas = []
                poses = []
                rels = []
                continue
            ln = ln.strip()

            if ln.startswith('#'):
                if ln.startswith('# sent_id = '):
                    udsentid = ln.split()[-1]
                    subcorpid, docid_, sentnum = udsentid.split('-')
                    assert docid_==docid
                    assert subcorpid=='reviews'
                sentMetaLines.append(ln)
            else:
                assert ln.count('\t')==9,ln
                if re.match(r'^\d+\t', ln):
                    lemmas.append(ln.split('\t')[2])
                    poses.append(ln.split('\t')[3:5])
                    rels.append(ln.split('\t')[6:8])
                    rels[-1][0] = int(rels[-1][0])
                sentTokLines.append(ln)

N_NEW_COLS = 9

for sentid, udsentid, mweMarkup, data in sentSSTData:
    data["wmwecat"] = []   # no weak MWE syntactic categories in this release
    udMetaLines, udTokLines, udLemmas, poses, rels = ud[udsentid]
    for ln in udMetaLines:
        print(ln)
    print(f'# streusle_sent_id = {sentid}')
    print(f'# mwe = {mweMarkup}')
    smweGroup = {}
    smweGroupToks = {}
    lexLemmas = {}
    wmweGroup = {}
    wmweGroupToks = {}
    wLemmas = {}
    i = 1
    for i,sg in enumerate(data["_"], 1):
        for j,o in enumerate(sg, 1):
            assert o not in smweGroup
            smweGroup[o] = f'{i}:{j}'
            smweGroupToks[o] = sg
        lexLemmas[sg[0]] = ' '.join(udLemmas[j-1] for j in sg)
    for h,wg in enumerate(data["~"], i+1):
        for j,o in enumerate(wg, 1):
            assert o not in wmweGroup
            wmweGroup[o] = f'{h}:{j}'
            wmweGroupToks[o] = wg
        wLemmas[wg[0]] = ' '.join(udLemmas[j-1] for j in wg)

    tagging = sent_tags(len(data["words"]), mweMarkup,
                        set(map(tuple,smweGroupToks.values())),
                        set(map(tuple,wmweGroupToks.values())))

    for ln in udTokLines:
        tokNum, form, lemma, upos, xpos, feats, head, deprel, deps, misc = ln.split('\t')
        if re.match(r'^\d+$', tokNum):
            tokNum = int(tokNum)
            offset0 = tokNum-1
            if data["words"][offset0] != [form, xpos]:
                # Most of the time the UD wordform and XPOS will match
                # what is stored in the .sst file.
                # Exceptions: ASCII normalization and tag fixes.
                print(data["words"][offset0], [form, xpos], file=sys.stderr)
            # TODO: if data["lemmas"]: assert data["lemmas"][offset0] == lemma
            smwe = smweGroup.get(tokNum, '_')
            lexlemma = lexLemmas.get(tokNum, '_')
            wmwe = wmweGroup.get(tokNum, '_')
            wlemma = wLemmas.get(tokNum, '_')
            #lexcat = data["lexcat"].get(str(tokNum), '_') # TODO: is lexcat ever manually specified, or always inferred from UD + MWE annotations?


            #wcat = data["wcat"].get(str(tokNum), '_')  # TODO
            wcat = '_'
            ss = data["labels"].get(str(tokNum), '__')[1]
            if ss=='NATURAL OBJECT':
                ss = 'NATURALOBJECT'

            lexcat = compute_lexcat(tokNum, smwe, smweGroupToks.get(tokNum), ss, lexlemma, poses, rels)

            PSS = ('P','PP','INF.P','POSS','PRON.POSS')
            if '|' in ss:
                assert lexcat in PSS,lexcat
                ss1, ss2 = ss.split('|')
                ss1 = 'p.'+ss1
                ss2 = 'p.'+ss2
            elif lexcat in PSS:
                ss1 = ss2 = 'p.'+ss
            else:   # noun, verb expressions only have 1 supersense
                if ss!='_':
                    if ss.isalpha() and ss.isupper():
                        ss = 'n.'+ss
                    elif ss.isalpha() and ss.islower():
                        ss = 'v.'+ss
                    else:
                        try:
                            assert ss[0]=='`' or ss=='??',ss
                        except AssertionError as ex:
                            print(ex, file=sys.stderr)
                        if ss[0]=='`' and ss!='`$':
                            ss = '_'    # most backtick labels redundant with lexcat
                ss1 = ss
                ss2 = '_'

            tag = tagging[offset0]
            fulllextag = tag

            if lexcat!='_':
                fulllextag += '-'+lexcat
            if ss1!='_':
                fulllextag += '-'+ss1
                if ss2!='_' and ss2!=ss1:
                    fulllextag += '|'+ss2
            if wcat!='_':
                fulllextag += '+'+wcat

            newFields = [smwe, lexcat, lexlemma, ss1, ss2, wmwe, wcat, wlemma, fulllextag]
            print(ln + '\t' + '\t'.join(newFields))
        else:   # an ellipsis node, e.g. 10.1
            print(ln + '\t' + '\t'.join('_'*N_NEW_COLS))
    print()
