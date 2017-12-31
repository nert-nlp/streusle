"""
Information about and utilities for supersense categories for lexical expressions in the corpus.

@author: Nathan Schneider (@nschneid)
@since: 2017-12-31
"""

import sys

# Adposition (preposition/postposition) and case supersenses

PSS_TREE = {
    'p.Circumstance': {
        'p.Temporal': {
            'p.Time': {
                'p.StartTime': {},
                'p.EndTime': {}},
            'p.Frequency': {},
            'p.Duration': {},
            'p.Interval': {}},
        'p.Locus': {
            'p.Source': {},
            'p.Goal': {}},
        'p.Path': {
            'p.Direction': {},
            'p.Extent': {}},
        'p.Means': {},
        'p.Manner': {},
        'p.Explanation': {
            'p.Purpose': {}}},
    'p.Participant': {
        'p.Causer': {
            'p.Agent': {
                'p.Co-Agent': {}}},
        'p.Theme': {
            'p.Co-Theme': {},
            'p.Topic': {}},
        'p.Stimulus': {},
        'p.Experiencer': {},
        'p.Originator': {},
        'p.Recipient': {},
        'p.Cost': {},
        'p.Beneficiary': {},
        'p.Instrument': {}},
    'p.Configuration': {
        'p.Identity': {},
        'p.Species': {},
        'p.Gestalt': {
            'p.Possessor': {},
            'p.Whole': {}},
        'p.Characteristic': {
            'p.Possession': {},
            'p.Part/Portion': {
                'p.Stuff': {}}},
        'p.Accompanier': {},
        'p.InsteadOf': {},
        'p.ComparisonRef': {},
        'p.RateUnit': {},
        'p.Quantity': {
            'p.Approximator': {}},
        'p.SocialRel': {
            'p.OrgRole': {}}},
}

PSS_PARENTS = {}
PSS_DEPTH = {}

queue = [[ss,None,PSS_TREE[ss]] for ss in PSS_TREE]
while queue:
    ss, par, descendants = queue.pop()
    PSS_PARENTS[ss] = par
    PSS_DEPTH[ss] = 1 if par is None else PSS_DEPTH[par] + 1
    queue.extend([[ch,ss,descendants[ch]] for ch in descendants])
del queue, ss, par, descendants

PSS = set(PSS_PARENTS.keys())

assert len(PSS_DEPTH)==len(PSS)==50
assert max(PSS_DEPTH.values())==4
assert min(PSS_DEPTH.values())==1

def coarsen_pss(ss, depth):
    coarse = ss
    while PSS_DEPTH[coarse]>depth:
        coarse = PSS_PARENTS[coarse]
    return coarse
