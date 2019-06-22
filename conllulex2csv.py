#!/usr/bin/env python3
"""
Given a .conllulex file, convert it to a CSV format readable by Excel.
See EXCEL.md for instructions.

Args: inputfile, outputfile

@since: 2018-05-28
@author: Nathan Schneider (@nschneid)
"""

import os, sys, fileinput, re, json, csv
from collections import defaultdict
from itertools import chain

CONLLU = ('ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC')
         # 1     2       3        4       5       6        7       8         9       10
STREUSLE = ('SMWE', 'LEXCAT', 'LEXLEMMA', 'SS', 'SS2', 'WMWE', 'WCAT', 'WLEMMA', 'LEXTAG')
           # 11      12        13          14    15     16      17      18        19

FIELDS = CONLLU + STREUSLE


inFname, outFname = sys.argv[1:]

# Excel expects UTF-8 with BOM
with open(inFname, encoding='utf-8') as inF, open(outFname, 'w', encoding='utf-8-sig') as outF:
    writer = csv.writer(outF, quoting=csv.QUOTE_ALL, delimiter='\t', dialect='excel')
    writer.writerow(FIELDS)
    writer.writerow([])
    for ln in inF:
        row = ln.strip().split('\t')
        writer.writerow(row)
