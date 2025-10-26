#!/usr/bin/env python3
"""
Given a .conllulex file, remove all STREUSLE columns except the lextag column
(the last one).

Args: inputfile

@since: 2019-06-20
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


def simplify_to_UDlextag(conllulexF):
    """
    Given a .conllulex file (or iterable over lines), clear the 8 columns
    containing MWE and supersense information, leaving only the full lextag
    column at the end.
    """
    result = ''
    for ln in conllulexF:
        row = ln.strip()
        if row and not row.startswith('#'):
            row = row.split('\t')
            row[10:18] = ['']*8 # retain the last column
            row = '\t'.join(row)
        result += row + '\n'
    return result

if __name__=='__main__':
    inFname, = sys.argv[1:]

    with open(inFname, encoding='utf-8') as inF:
        print(simplify_to_UDlextag(inF), end='')
