#!/usr/bin/env python3
"""
Given a file exported from Excel as "CSV UTF-18 (Comma-delimited)", 
convert it to .conllulex. See EXCEL.md for instructions.

Args: inputfile, outputfile

@since: 2018-05-28
@author: Nathan Schneider (@nschneid)
"""

import os, sys, fileinput, re, json, csv

inFname, outFname = sys.argv[1:]

# Excel-output CSV is UTF-8 with BOM
with open(inFname, encoding='utf-8-sig') as inF, open(outFname, 'w') as outF:
    reader = csv.reader(inF, delimiter=',', dialect='excel')
    next(reader)  # swallow header row
    next(reader)  # and blank line after header row
    for row in reader:
        if row[0].startswith('#'):
            assert not ''.join(row[1:])
            o = row[0]
        elif not ''.join(row):  # blank line
            o = ''
        else:
            o = '\t'.join(row)
        outF.write(o + '\n')
    outF.write('\n')
