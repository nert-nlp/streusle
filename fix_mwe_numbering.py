#!/usr/bin/env python3
import fileinput, sys, json, re

"""Ensure MWE groups in a sentence are numbered from 1"""

sent = ''
for ln in fileinput.input():
    if not ln.strip():
        if sent:
            if '\t2:1\t' in sent and '\t1:1\t' not in sent:
                print('Adjusting MWE group identifiers in', sent[:sent.index('\n')], file=sys.stderr)
                i = 2
                while f'\t{i}:1\t' in sent:
                    j = 1
                    while f'\t{i}:{j}\t' in sent:
                        sent = sent.replace(f'\t{i}:{j}\t', f'\t{i-1}:{j}\t')
                        j += 1
                    i += 1
            print(sent)
            sent = ''
        continue
    sent += ln
assert not sent