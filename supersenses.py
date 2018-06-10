"""
Information about and utilities for supersense categories for lexical expressions in the corpus.

@author: Nathan Schneider (@nschneid)
@since: 2017-12-31
"""

import sys

SPECIAL_LABELS = {'??', # a semantic supersense could not be assigned:
    # e.g. due to unintelligible/unclear context, missing word, or marginal or nonnative usage
                  '`$'} # opaque possessive slot in an idiom

# Noun supersenses

NSS = {'n.ACT', 'n.ANIMAL', 'n.ARTIFACT', 'n.ATTRIBUTE', 'n.BODY', 'n.COGNITION',
       'n.COMMUNICATION', 'n.EVENT', 'n.FEELING', 'n.FOOD', 'n.GROUP',
       'n.LOCATION', 'n.MOTIVE', 'n.NATURALOBJECT', 'n.OTHER', 'n.PERSON',
       'n.PHENOMENON', 'n.PLANT', 'n.POSSESSION', 'n.PROCESS', 'n.QUANTITY',
       'n.RELATION', 'n.SHAPE', 'n.STATE', 'n.SUBSTANCE', 'n.TIME'}

# Verb supersenses

VSS = {'v.body', 'v.change', 'v.cognition', 'v.communication', 'v.competition',
       'v.consumption', 'v.contact', 'v.creation', 'v.emotion', 'v.motion',
       'v.perception', 'v.possession', 'v.social', 'v.stative'}

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
            'p.PartPortion': {
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


ALL_SS = SPECIAL_LABELS | NSS | VSS | PSS

# v1 preposition supersenses (used in STREUSLE 3.0 but removed in v2)
PSS_REMOVED = {'1DTrajectory', '2DArea', '3DMedium',
    'Activity', 'Age', 'Asset', 'Attribute', 'ClockTimeCxn', 'Contour',
    'Co-Participant', 'Co-Patient', 'Comparison/Contrast', 'Course', 'Creator',
    'DeicticTime', 'Donor/Speaker', 'Function', 'Instance', 'Material',
    'State', 'StartState', 'EndState',
    'Location', 'InitialLocation', 'Destination',
    'Patient', 'ProfessionalAspect', 'Reciprocation', 'RelativeTime', 'Scalar/Rank',
    'Transit', 'Traversed', 'Value', 'ValueComparison', 'Via'}

# Note also that Part/Portion was renamed to PartPortion in STREUSLE 4.1

def coarsen_pss(ss, depth):
    coarse = ss
    while PSS_DEPTH[coarse]>depth:
        coarse = PSS_PARENTS[coarse]
    return coarse

def ancestors(ss):
    par = PSS_PARENTS[ss]
    if par is None:
        return []
    return [par] + ancestors(par)
