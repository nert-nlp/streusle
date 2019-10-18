#!/usr/bin/env python3

import sys

from helpers import *

if len(sys.argv) < 3:
    print("usage: python split.py streusle.conllulex ud_{train, dev, test}_sent_ids.txt", file=sys.stderr)
    sys.exit(1)


sent_ids = set()
with open(sys.argv[2]) as f:
    for line in f:
        line = line.strip()
        if line:
            sent_ids.add(line.strip("# ").split(" = ")[1])

csplit = 0
call = 0
for sent in sentences(sys.argv[1]):
    call += 1
    if sent.meta_dict["sent_id"] in sent_ids:
        for line in sent.meta:
            print(line)
        for token in sent.tokens:
            print(token.orig)
        print()
        csplit += 1

print("{}/{}".format(csplit, call), file=sys.stderr)
