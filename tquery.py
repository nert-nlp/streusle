#!/usr/bin/env python3
"""
Query by token, filtering by matching against one or more fields of the input,
and optionally display fields as columns of output alongside the token in context.
By default, the first column is the sentence ID, the second column is the token offset(s),
and the third column is the token highlighted in context.
By default, 2 header rows are printed.

A sample of lines output by calling

  ./tquery.py streusle.json +ss=Manner +ss2!=Locus

reviews-116821-0011     3       p.Manner        p.ComparisonRef It tasted >> like << I just flew back home .
reviews-371300-0005     8-9     p.Manner        p.Manner        I was told to take my coffee >> to go << if I wanted to finish it .
reviews-048363-0016     7,9     p.Manner        p.Manner        Here I am now driving confidently >> on << my >> own << .

Interface: ./tquery [OPTIONS] streusle.json [+]<fldname>[<op><pattern>] [[+]<fldname2>[<op2><pattern2>] ...]

OPTIONS:
-H: omit header lines giving commit hash and call info, and column headers (these lines start with "#")
-I: case-sensitive filtering (case-insensitive by default)
-S: omit sentence IDs in output
-T: omit token numbers (offsets within the sentence) in output

fldname: one of the column names: w(ord), l(emma), upos, xpos, feats, head, deprel, edeps, misc, smwe, wmwe, lt (lextag)
or lc (lexcat), ll (lexlemma), ss = r (role), f (function)
g (governor lemma), o (object lemma), config (syntactic configuration). Can also specify a token-level property of the governor or object:
g.upos, o.lt, etc. (not currently supported for role/function/lexlemma/lexcat, which are stored at the lexical level; cannot be used recursively).

+fldname to print the value of the field in a column of output

op: if filtering on the field, one of: = (regex partial match), == (regex full match), != (inverse regex partial match), !== (inverse regex full match)

pattern: if filtering on the field, regex to match against the field's value; case-insensitive unless -I is specified

Note that for prepositions/possessives, lextag contains the full supersense labeling in "role|function" notation.
So lextag can be used to search for a supersense without specifying whether it occurs as role or function.

Properties of the governor and object cannot be referenced unless the govobj.py script has been run to add the information to the JSON.

An example use of this script to query preposition tokens:

    ./conllulex2json.py streusle.conllulex > streusle.json
    ./govobj.py streusle.json > streusle.go.json
    ./tquery.py streusle.go.json lc==PP? +ll +r +f +config!=subordinating +g +g.upos +o=. +o.upos > streusle.ptoks.tsv

Outputs the tokens annotated as P or (idiomatic) PP along with their role/function supersenses,
syntactic configuration (default, predicative, or stranded), and lemmas and POSes of the governor and (non-empty) object.

@author: Nathan Schneider (@nschneid)
@since: 2018-06-13
"""

import sys, json, fileinput, re
import shlex, subprocess
from itertools import chain

TKN_LEVEL_FIELDS = {'w': 'word', 'word': 'word', 'l': 'lemma', 'lemma': 'lemma',
                   'upos': 'upos', 'xpos': 'xpos', 'feats': 'feats',
                   'head': 'head', 'deprel': 'deprel', 'edeps': 'edeps',
                   'misc': 'misc', 'smwe': 'smwe', 'wmwe': 'wmwe', 'lextag': 'lextag', 'lt': 'lextag'}
LEX_LEVEL_FIELDS = {'lexcat': 'lexcat', 'lc': 'lexcat', 'lexlemma': 'lexlemma', 'll': 'lexlemma',
                   'r': 'ss', 'ss': 'ss', 'f': 'ss2', 'ss2': 'ss2'}
GOVOBJ_FIELDS = {'g': 'govlemma', 'govlemma': 'govlemma', 'o': 'objlemma', 'objlemma': 'objlemma', 'config': 'config'}
ALL_FIELDS = dict(**TKN_LEVEL_FIELDS, **LEX_LEVEL_FIELDS, **GOVOBJ_FIELDS)
RE_FLAGS = re.IGNORECASE   # case-insensitive by default

def tselect(jsonPath, fields, tknconstraints=[], lexconstraints=[], govobjconstraints=[]):

    with open(jsonPath, encoding='utf-8') as inF:
        data = json.load(inF)

    for sent in data:
        for lexe in chain(sent["swes"].values(), sent["smwes"].values()):
            fail = False
            myprints = {k: None for k in fields}
            # at the lexical expression level: lexcat, lexlemma, ss (role), ss2 (function), heuristic_relation["govlemma", "objlemma", "config"]
            for fld, matchX in lexconstraints:
                if matchX and not matchX(lexe[fld]):
                    fail = True
                    break
                if matchX is None:
                    myprints[fld] = lexe[fld]
            if govobjconstraints and not fail:
                if "heuristic_relation" not in lexe:
                    fail = True
                else:
                    govobj = lexe["heuristic_relation"]
                    for fld, matchX in govobjconstraints:
                        if '.' in fld:
                            assert fld.startswith('g.') or fld.startswith('o.')
                            i = govobj["gov"] if fld.startswith('g.') else govobj["obj"]
                            if i is None:
                                if matchX:
                                    fail = True
                                    break
                                else:
                                    go = {'': ''}
                                    f = ''
                            else:
                                go = sent["toks"][i-1]
                                f = fld.split('.',1)[1]
                        else:
                            go = govobj
                            f = fld

                        if matchX and not matchX(go[f]):
                            fail = True
                            break
                        if matchX is None:
                            myprints[fld] = go[f]
            if tknconstraints and not fail:
                toks = [sent["toks"][i-1] for i in lexe["toknums"]]
                for fld, matchX in tknconstraints:
                    combined = tuple(tok[fld] for tok in toks)
                    if len(combined)==1:
                        combined = combined[0]
                    # combined is a tuple if this is a multi-token expression,
                    # and just a single field value otherwise
                    if matchX and not matchX(str(combined)):
                        fail = True
                        break
                    if matchX is None:
                        myprints[fld] = combined

            if not fail:
                myprints['_sentid'] = sent["sent_id"]

                s = ''
                inmatch = False
                toknums = lexe["toknums"]
                for tok in sent["toks"]:
                    if tok["#"] in toknums:
                        if not inmatch:
                            inmatch = True
                            s += '>> '
                    else:
                        if inmatch:
                            inmatch = False
                            s += '<< '
                    s += tok["word"] + ' '
                if inmatch:
                    s += '<< '
                myprints['_context'] = s

                if 1 < len(toknums) == max(toknums)-min(toknums)+1:
                    myprints['_tokoffset'] = f'{min(toknums)}-{max(toknums)}'
                else:
                    myprints['_tokoffset'] = ','.join(map(str,lexe["toknums"]))

                yield myprints





if __name__=='__main__':


    printHeader = True
    printSentId = True
    printTokOffset = True


    args = sys.argv[1:]
    assert len(args)>=2

    while args[0].startswith('-'):
        flag = args.pop(0)
        if flag=='-H':  # no header info
            printHeader = False
        elif flag=='-I': # case-sensitive
            RE_FLAGS = 0
        elif flag=='-S':    # no sentence IDs
            printSentId = False
        elif flag=='-T':    # no token offsets
            printTokOffset = False
        else:
            raise ValueError(f'Invalid flag: {flag}')

    inFP = args.pop(0)
    tknconstraints, lexconstraints, govobjconstraints = [], [], []
    prints = [] # fields whose values are to be printed

    if printSentId:
        prints.append('_sentid')
    if printTokOffset:
        prints.append('_tokoffset')

    # parse the query (fields and constraints)
    for arg in args:
        printme = False
        if arg.startswith('+'):
            printme = True
            arg = arg[1:]

        if '=' in arg:
            fld, pattern = arg.split('=', 1)

            if fld.endswith('!'):
                op = '!='
                fld = fld[:-1]
                if pattern.startswith('='):
                    op += '='
                    pattern = '^' + pattern[1:] + '$'
                r = re.compile(pattern, RE_FLAGS)
                matchX = (lambda r: lambda s: s is None or r.search(s) is None)(r)
            elif pattern.startswith('='):
                op = '=='
                pattern = pattern[1:]
                r = re.compile('^'+pattern+'$', RE_FLAGS)
                matchX = (lambda r: lambda s: s is not None and r.search(s) is not None)(r)
            else:
                op = '='
                r = re.compile(pattern, RE_FLAGS)
                matchX = (lambda r: lambda s: s is not None and r.search(s) is not None)(r)

            if '.' in fld:
                prefix, fld = fld.split('.',1)
                prefix += '.'   # g. (governor) or o. (object)
            else:
                prefix = ''
            fld = ALL_FIELDS[fld]
            fld = prefix+fld
            if fld in TKN_LEVEL_FIELDS:
                tknconstraints.append((fld, matchX))
            elif fld in LEX_LEVEL_FIELDS:
                lexconstraints.append((fld, matchX))
            else:
                govobjconstraints.append((fld, matchX))
        else:
            assert printme
            fld = arg

        if printme:
            if '.' in fld:
                prefix, fld = fld.split('.',1)
                prefix += '.'   # g. (governor) or o. (object)
            else:
                prefix = ''
            fld = ALL_FIELDS[fld]
            fld = prefix+fld
            if fld not in prints:
                prints.append(fld)
            # to the "constraints", add a dummy item indicate that the field should be looked up for printing
            if fld in TKN_LEVEL_FIELDS:
                tknconstraints.append((fld, None))
            elif fld in LEX_LEVEL_FIELDS:
                lexconstraints.append((fld, None))
            else:
                govobjconstraints.append((fld, None))

    prints.append('_context')


    if printHeader:
        # for reproducibility, the git commit hash and the command line call to this script
        commitHash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
        sysCall = sys.argv[0] + " " + " ".join(map(shlex.quote, sys.argv[1:]))
        print(f'# {commitHash} ~ {sysCall}')

        # column headers
        print('# ' + '\t'.join(prints), sep='\t')

    n = 0
    for myprints in tselect(inFP, prints, tknconstraints=tknconstraints,
            lexconstraints=lexconstraints, govobjconstraints=govobjconstraints):

        print(*[myprints[f] for f in prints],
              #lexe["ss"]+('|'+lexe["ss2"] if lexe["ss2"] and lexe["ss2"]!=lexe["ss"] else ''),     # TODO: make a field for this
              sep='\t')
        n += 1

    print(f'{n} match' + ('es' if n!=1 else ''), file=sys.stderr)
