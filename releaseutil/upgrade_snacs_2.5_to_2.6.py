#!/usr/bin/env python3
"""Used for STREUSLE v4.5: Upgrade SNACS labels in provided .conllulex file from version 2.5 to 2.6, which involves renaming 2 labels."""
import fileinput
for ln in fileinput.input():
    if '\t' not in ln:
        print(ln, end='')
        continue
    parts = ln.split('\t')
    parts[13] = parts[13].replace('p.RateUnit','p.SetIteration').replace('p.Causer','p.Force')
    parts[14] = parts[14].replace('p.RateUnit','p.SetIteration').replace('p.Causer','p.Force')
    parts[18] = parts[18].replace('p.RateUnit','p.SetIteration').replace('p.Causer','p.Force')
    print('\t'.join(parts), end='')
