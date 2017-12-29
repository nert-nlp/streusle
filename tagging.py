#!/usr/bin/env python3
#coding=utf-8

import os, sys

I_BAR, I_TILDE, i_BAR, i_TILDE = 'I_', 'I~', 'i_', 'i~'

def sent_tags(nWords, anno, smwes, wmwes):
    """Convert a sentence's MWE analysis to a BIO-style tag sequence."""
    
    tagging = []


    parents = {}
    gapstrength = {}    # offset -> kind of gap ('_' or '~'), if the offset lies with a gap

    # process strong groups
    for grp in smwes:
        g = sorted(grp)
        skip = False
        for i,j in zip(g[:-1],g[1:]):
            if j>i+1:
                if i in gapstrength:    # gap within a gap
                    print('Simplifying: removing gappy group that is wholly contained within another gap:', g, anno, file=sys.stderr)
                    skip = True
                    break
        if skip: continue

        for i,j in zip(g[:-1],g[1:]):
            assert j not in parents
            parents[j] = i, '_'
            if j>i+1:
                for h in range(i+1,j):
                    gapstrength[h] = '_'

    # process weak groups, skipping any that interleave with (are only partially contained in a gap of)
    # a strong group
    for grp in wmwes:
        g = sorted(grp)
        skip = False
        for i in g:
            if i in gapstrength and any(j for j in g if j not in gapstrength):
                print('Simplifying: removing weak group that interleaves with a strong gap:', g, anno, file=sys.stderr)
                skip = True
                break
        if skip: continue
        for i,j in zip(g[:-1],g[1:]):
            if j>i+1:
                if i in gapstrength:    # gap within a gap
                    print('Simplifying: removing gappy group that is wholly contained within another gap:', g, anno, file=sys.stderr)
                    skip = True
                    break
        if skip: continue

        for i,j in zip(g[:-1],g[1:]):
            if j not in parents:
                parents[j] = i, '~'
            else:
                assert parents[j][0]==i,(j,parents[j],i,g,anno)
            if j>i+1:
                for h in range(i+1,j):
                    gapstrength.setdefault(h,'~')

    allparents = set(list(zip(*parents.values()))[0]) if parents else set()

    for i in range(nWords):
        parent, strength = parents.get(i+1,(0,''))
        amInGap = (i+1 in gapstrength)
        if parent==0:
            if i+1 in allparents:
                tag = ('b' if amInGap else 'B') #+labelFlag
            else:
                tag = ('o' if amInGap else 'O') #+labelFlag
        elif strength=='_': # do not attach label to strong MWE continuations
            tag = i_BAR if amInGap else I_BAR
        else:
            assert strength=='~'
            tag = (i_TILDE if amInGap else I_TILDE) #+labelFlag
        
        tagging.append(tag)
    
    return tagging
