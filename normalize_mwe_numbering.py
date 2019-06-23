#!/usr/bin/env python3
"""
Given a .conllulex file, apply a consistent ordering to MWEs based
primarily on the first token offset in each expression,
and secondarily on strong vs. weak (strong comes before weak).

Args: inputfile

@since: 2019-06-22
@author: Nathan Schneider (@nschneid)
"""

import os, sys, fileinput, re, json, csv
from collections import defaultdict
from itertools import chain

from conllulex2json import load_sents, print_json

inFname, = sys.argv[1:]

nSentsRenumbered = 0
nMWEsRenumbered = 0

with open(inFname, encoding='utf-8') as inF:
    sents = list(load_sents(inF))
    for sent in sents:
        smwes = sent["smwes"]
        wmwes = sent["wmwes"]
        allmwes = []
        for oldnum,e in smwes.items():
            allmwes.append((e["toknums"][0], 's', oldnum))
        for oldnum,e in wmwes.items():
            allmwes.append((e["toknums"][0], 'w', oldnum))
        allmwes.sort()
        current_sort = sorted(allmwes, key=lambda x: x[2])
        if allmwes!=current_sort:
            nSentsRenumbered += 1
            # renumber
            new_smwes = {}
            new_wmwes = {}
            for newnum,(tok1,s_or_w,oldnum) in enumerate(allmwes, start=1):
                if oldnum!=newnum:
                    nMWEsRenumbered += 1
                old_container = smwes if s_or_w=='s' else wmwes
                new_container = new_smwes if s_or_w=='s' else new_wmwes
                e = new_container[newnum] = old_container[oldnum]
                # update pointers from tokens
                for toknum in e["toknums"]:
                    pointer, position = sent["toks"][toknum-1][s_or_w+"mwe"]
                    assert pointer==oldnum
                    sent["toks"][toknum-1][s_or_w+"mwe"] = newnum, position
            assert len(new_smwes)==len(smwes)
            assert len(new_wmwes)==len(wmwes)
            sent["smwes"] = new_smwes
            sent["wmwes"] = new_wmwes

print_json(sents)

print(f'Renumbered {nMWEsRenumbered} MWEs in {nSentsRenumbered} sentences', file=sys.stderr)
