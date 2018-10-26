import sys
import json
import glob
import pickle

from collections import Counter
from collections import defaultdict

from ucca import convert as uconv
from ucca import constructions as uconstr
from ucca import layer0 as ul0

import helpers

try:
    streusle_file = 'streusle.govobj.json' # sys.argv[1]
    ucca_files = '/home/jakob/nert/corpora/UCCA_English-EWT/sentences_by_ud/*' # sys.argv[2]
    streusle2ucca_file = '/home/jakob/nert/corpora/UCCA_English-EWT/streusle2ucca.txt' # sys.argv[3]
except:
    print('usage: python3 govobj-ucca.py streusle.govobj.json sentences_by_ud streusle2ucca.txt', file=sys.stderr)
    exit(1)


s2u = {}
u2s = {}
    

with open(streusle2ucca_file) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        _s, _u = line.split()
        s, u = int(_s), int(_u)
        s2u[s] = u
        u2s[u] = s


streusle_id2sent = {}
with open(streusle_file) as f:
    for sent in json.load(f):
        streusle_id2sent[sent['streusle_sent_id']] = sent

def get_heads(node):
    if node.is_scene():
        return [node.process or node.state]
    else:
        return node.centers
    

def get_head_terminals(node):
    result = []
    agenda = [node]
    while agenda:
        current = agenda.pop()
        if current.terminals:
            result.extend(current.terminals)
        else:
            agenda.extend(get_heads(current))
    return sorted(result, key=lambda x: x.position)

def get_text(node):
    return ' '.join([t.text for t in sorted(node.get_terminals(), key=lambda x: x.position)])

def success(pss_unit, ucca_edge, marked_edge, ground_edge, cat):
    ss = pss_unit['ss']
    prep = pss_unit['lexlemma']
    lexcat = pss_unit['lexcat']
    toknums = ' '.join(str(x) for x in pss_unit['toknums'])
    gov, obj = pss_unit['heuristic_relation'].get('govlemma', ''), pss_unit['heuristic_relation'].get('objlemma', '')
    gov_i, obj_i = pss_unit['heuristic_relation']['gov'], pss_unit['heuristic_relation']['obj']
    gov_t, obj_t = streusle_sent['toks'][gov_i-1] if gov_i != None else {}, streusle_sent['toks'][obj_i-1] if obj_i != None else {}
    gov_upos, obj_upos = gov_t.get('upos'), obj_t.get('upos')
    marked_text, marked_tag = get_text(marked_edge.child), marked_edge.tag
    ground_text, ground_tag = get_text(ground_edge.child), ground_edge.tag
    if ucca_edge:
        ucca_unit, ucca_tag = str(ucca_edge.child), ucca_edge.tag
    else:
        ucca_unit, ucca_tag = '', ''
    print('\t'.join(str(x) for x in [streusle_id, name,'SUCCESS',cat,toknums,prep,ucca_unit,ucca_tag,lexcat,ss,marked_text,marked_tag,obj,obj_upos,ground_text,ground_tag,gov,gov_upos,streusle_sent_text, passage]))

def fail(pss_unit, ucca_edge, message, **args):
    ss = pss_unit['ss']
    prep = pss_unit['lexlemma']
    lexcat = pss_unit['lexcat']
    toknums = ' '.join(str(x) for x in pss_unit['toknums'])
    gov, obj = pss_unit['heuristic_relation']['govlemma'], pss_unit['heuristic_relation']['objlemma']
    gov_i, obj_i = pss_unit['heuristic_relation']['gov'], pss_unit['heuristic_relation']['obj']
    gov_t, obj_t = streusle_sent['toks'][gov_i-1] if gov_i != None else {}, streusle_sent['toks'][obj_i-1] if obj_i != None else {}
    gov_upos, obj_upos = gov_t.get('upos'), obj_t.get('upos')
    if ucca_edge:
        ucca_unit, ucca_tag = str(ucca_edge.child), ucca_edge.tag
    else:
        ucca_unit, ucca_tag = '', ''
    print('\t'.join(str(x) for x in [streusle_id, name,'FAIL',message,toknums,prep,ucca_unit,ucca_tag,lexcat,ss,'','',obj,obj_upos,'','',gov,gov_upos,streusle_sent_text, passage]))

def warn(pss_unit, ucca_edge, message, **args):
    ss = pss_unit['ss']
    prep = pss_unit['lexlemma']
    lexcat=pss_unit['lexcat']
    toknums = ' '.join(str(x) for x in pss_unit['toknums'])
    gov, obj = pss_unit['heuristic_relation']['govlemma'], pss_unit['heuristic_relation']['objlemma']
    gov_i, obj_i = pss_unit['heuristic_relation']['gov'], pss_unit['heuristic_relation']['obj']
    gov_t, obj_t = streusle_sent['toks'][gov_i-1] if gov_i != None else {}, streusle_sent['toks'][obj_i-1] if obj_i != None else {}
    gov_upos, obj_upos = gov_t.get('upos'), obj_t.get('upos')
    if ucca_edge:
        ucca_unit, ucca_tag = str(ucca_edge.child), ucca_edge.tag
    else:
        ucca_unit, ucca_tag = '', ''
    print('\t'.join(str(x) for x in [streusle_id, name,'WARNING',message,toknums,prep,ucca_unit,ucca_tag,lexcat,ss,'','',obj,obj_upos,'','',gov,gov_upos,streusle_sent_text, passage]))
    
unit_counter = 0
#gov_and_obj_counter = 0
considered_counter = 0
considered = []
linked_as_expected_counter = 0
successful_units = 0
unsuccessful_units = 0
mwe_una_miss = 0
a_b_miss = 0
c_miss = 0
d_miss = 0
e_miss = 0
f_miss = 0
no_match = 0
deductable_multiple_fails = 0
ucca_categories = Counter()

to_SNACS = defaultdict(lambda: defaultdict(int))
to_UCCA = defaultdict(lambda: defaultdict(int))

print('\t'.join(str(x) for x in ['streusle_id', 'ucca_id','code','message','toknums','prep','ucca_unit','ucca_tag','lexcat','ss','marked_text','marked_tag','obj','obj_upos','ground_text','ground_tag','gov','gov_upos','sentence', 'passage']))

for filename in glob.glob(ucca_files):
    name = filename.split('/')[-1].rsplit('.', maxsplit=1)[0]
    passage_id, offset = name[:-3], name[-3:]
    streusle_id = f'ewtb.r.{str(u2s[int(passage_id)]).zfill(6)}.{int(offset)+1}'

    passage = uconv.pickle2passage(filename)

    terminals = sorted([n for n in passage.nodes.values() if type(n) == ul0.Terminal], key=lambda x: x.position)
    edges = uconstr.extract_edges(passage)

    streusle_sent = streusle_id2sent[streusle_id]
    tokens = [tok['word'] for tok in streusle_sent['toks']]
    streusle_sent_text = ' '.join(tokens)
    
    assert len(terminals) == len(tokens), f'unequal number of UCCA terminals and tokens: {terminals}, {tokens}'
    
    for unit in list(streusle_sent['swes'].values()) + list(streusle_sent['smwes'].values()):

        #if unit['lexlemma'] == 'to':
        #    unit_terminals = [terminals[toknum-1] for toknum in unit['toknums']]
        #    preterminals = set(unit_terminals[0].parents)
        #    for pt in preterminals:
        #        if len(pt.terminals) > len(toknums):
        #            #warn(unit, None, f'PSS-bearing token(s) are part of a larger unanalyzable unit: [{lexlemma}] in {passage}')
        #            continue
        #        for incoming in pt.incoming:
        #            parent = incoming.parent
        #            to_SNACS[unit['lexcat']][incoming.tag] += 1
        #            to_UCCA[incoming.tag][unit['lexcat']] += 1
                    
        
        if 'heuristic_relation' not in unit: continue
        unit_counter += 1

        ss = unit['ss']
        lexcat = unit['lexcat']
        lexlemma = unit['lexlemma']
        toknums = unit['toknums']
        span = f'{toknums[0]}-{toknums[-1]}'
        rel = unit['heuristic_relation']
        gov, govlemma, obj, objlemma = rel.get('gov', None), rel.get('govlemma', None), rel.get('obj', None), rel.get('objlemma', None)
        if lexcat == 'PP':
            obj, objlemma = None, None
        config = rel['config']

        unit_terminals = [terminals[toknum-1] for toknum in toknums]
        preterminals = set(unit_terminals[0].parents)


        successes_for_unit = 0
        fails_for_unit = 0
        
        # check whether STREUSLE mwe is UNA unit in UCCA
        if len(toknums) > 1:
            for t in unit_terminals[1:]:
                preterminals.intersection_update(set(t.parents))
            if not preterminals:
                fail(unit, None, f'terminals comprising strong MWE are not unanalyzable: [{lexlemma}] in {passage}')
                mwe_una_miss += 1
                fails_for_unit += 1

        for pt in preterminals:
            if len(pt.terminals) > len(toknums):
                warn(unit, None, f'PSS-bearing token(s) are part of a larger unanalyzable unit: [{lexlemma}] in {passage}')
            for incoming in pt.incoming:
                
                parent = incoming.parent
                
                # X is a unit (`pt`) and has PSS L (`ss`); Y is X's parent (`parent`)

                # if X is R
                if incoming.tag == 'R':

                    if not (gov and obj):
                        missing = [n for n,x in [('gov',gov), ('obj',obj)] if not x]
                        warn(unit, incoming, f'unit is R, so we expect it to have both gov and obj, but it\'s missing {missing}: [{pt}] in {passage}')

                    gov_or_obj = [x for x in (gov, obj) if x]

                    # B. Configurative or circumstantial modifier of a non-scene
                    centers = parent.centers
                    if parent.process:
                        centers.append(parent.process)
                    if parent.state:
                        centers.append(parent.state)
                    # if Y has a unique C child H
                    if len(centers) == 1:
                        center = centers[0]
                    else:
                        fail(unit, incoming, f'more than one center: {centers} in parent')
                        a_b_miss += 1
                        fails_for_unit += 1
                        continue
                            
                    # if Y contains both X's gov G and obj O
                    if all(terminals[related-1] in parent.get_terminals() for related in gov_or_obj):
                        center_head_terminals = get_head_terminals(center)
                        assert len(center_head_terminals) == 1
                        center_ind = terminals.index(center_head_terminals[0])
                        if obj and center_ind != obj-1:
                            non_center = terminals[obj-1]
                        elif not gov or center_ind != gov-1:
                            non_center = terminals[gov-1]
                        else:
                            fail(unit, incoming, f'non_center is neither gov nor obj: {parent}')
                            a_b_miss += 1
                            fails_for_unit += 1
                            continue
                        non_center_sibling_edge = None
                        center_sibling_edge = None
                        for edge in parent.outgoing:
                            if non_center in edge.child.get_terminals():
                                non_center_sibling_edge = edge
                            if center_head_terminals[0] in edge.child.get_terminals():
                                center_sibling_edge = edge
                        assert non_center_sibling_edge, f'can\'t find sibling of X containing non-center terminal: X=[{get_text(pt)}], center sibling=[{get_text(center)}], non-center terminal=[{get_text(non_center)}] in [{passage}]'
                        if non_center_sibling_edge.tag in ('Q', 'E'):
                            marked = non_center_sibling_edge
                            ground = center_sibling_edge
                            success(unit, incoming, marked, ground, 'B')
                            successes_for_unit += 1
                                

                    # A. Participant or circumstantial modifier of a scene
                    for grandparent_edge in parent.incoming:
                        if grandparent_edge.parent.is_scene():
                            index_in_parent = sorted(parent.children, key=lambda x: x.start_position).index(pt)
                            if index_in_parent == 0 or index_in_parent == len(parent.children)-1:
                                p_or_s = grandparent_edge.parent.process or grandparent_edge.parent.state
                                if p_or_s != parent:
                                    ground = None
                                    for edge in p_or_s.incoming:
                                        if edge.parent == grandparent_edge.parent:
                                            ground = edge
                                    marked = grandparent_edge
                                    success(unit, incoming, marked, ground, 'A')
                                    successes_for_unit += 1
                                else:
                                    warn(unit, grandparent_edge, f'P/S contains R: [{parent}] in {passage}')
                        elif not all(terminals[related-1] in parent.get_terminals() for related in gov_or_obj):
                            warn(unit, incoming, f'gov or obj are not covered by parent unit in non-scene parent unit. There is likely an error in either the annotation or the govobj heuristic: [{parent}] in [{grandparent_edge.parent}]')
                                
                    if successes_for_unit == 0:
                        fail(unit, incoming, f'unit is R, but neither cat A nor B: [{pt}] in {parent}')
                        a_b_miss += 1
                        fails_for_unit += 1
                    
                        
                # C. Predication
                elif incoming.tag == 'S':
                    # if not (gov and obj):
                    #    missing = [n for n,x in [('gov',gov), ('obj',obj)] if not x]
                    #    fail(unit, incoming, f'unit is S, so we expect it to have both gov and obj, but it\'s missing {missing}: [{pt}] in {passage}')

                    #elif len(parent.participants) != 2:
                    #    fail(unit, incoming, f'unit is S, so we expect it to have exactly 2 A siblings, got {len(parent.participants)}: [{pt}] in {passage}')

                    # else:
                    start_position = incoming.child.start_position
                    sorted_as = sorted([out for out in parent.outgoing if out.child in parent.participants], key=lambda x: x.child.start_position)
                    ground = None
                    for a in sorted_as[::-1]:
                        if a.child.start_position < start_position:
                            ground = a
                            break
                    marked = None
                    for a in sorted_as:
                        if a.child.start_position > start_position:
                            marked = a
                            break
                    if not marked and obj:
                        fail(unit, incoming, f'unit is S, but not cat C (unit is not followed by an A, but has an OBJ): [{pt}] in {parent}')
                        c_miss += 1
                        fails_for_unit += 1
                        
                    else:
                        if not marked:
                            marked = incoming
                        if not ground:
                            ground = incoming
                        # ground, marked = sorted_as
                        success(unit, incoming, marked, ground, 'C')
                        successes_for_unit += 1

                    #if successes_for_unit == 0:
                    #    fail(unit, incoming, f'unit is S, but not cat C: [{pt}] in {parent}')
                    #    c_miss += 1
                    #    fails_for_unit += 1

                # D. Linkage
                elif incoming.tag == 'L':
                    if not obj:
                        fail(unit, incoming, f'unit is L, so we expect it to have an obj, but it doesn\'t: [{pt}] in {passage}')
                        d_miss += 1
                        fails_for_unit += 1

                    else:
                        parent_children = sorted(parent.outgoing, key=lambda x: x.child.start_position)
                        index_in_parent = parent_children.index(incoming)
                        next_hs = [sibling for sibling in parent_children[index_in_parent+1:] if sibling.tag == 'H']
                        assert next_hs
                        marked = next_hs[0]
                        previous_hs = [sibling for sibling in parent_children[:index_in_parent] if sibling.tag == 'H']
                        if previous_hs:
                            ground = previous_hs[-1]
                        else:
                            ground = next_hs[1]
                        success(unit, incoming, marked, ground, 'D')
                        successes_for_unit += 1

                    #if successes_for_unit == 0:
                    #    fail(unit, incoming, f'unit is L, but not cat D: [{pt}] in {parent}')
                    #    d_miss += 1
                    #    fails_for_unit += 1

                # E. Intransitive prepositions, particles
                elif incoming.tag in ('D', 'E'):
                    if obj:
                        fail(unit, incoming, f'unit is D or E, so we expect it to not have an obj, but it does: [{unit}] in {passage}')
                        e_miss += 1
                        fails_for_unit += 1
                    else:
                        p_or_s = parent.process or parent.state or parent.centers[0]
                        ground = None
                        for edge in p_or_s.incoming:
                            if edge.parent == parent:
                                ground = edge
                        success(unit, incoming, incoming, ground, 'E')
                        successes_for_unit += 1

                # F. Possessive pronouns
                elif incoming.tag == 'A':
                    if obj:
                        fail(unit, incoming, f'unit is A, so we expect it to not have an obj, but it does: [{unit}] in {passage}')
                        f_miss += 1
                        fails_for_unit += 1
                    elif lexcat != 'PRON.POSS':
                        fail(unit, incoming, f'unit is A, so we expect it to be PRON.POSS, got {lexcat}: [{unit}] in {passage}')
                        f_miss += 1
                        fails_for_unit += 1
                    else:
                        p_or_s = parent.process or parent.state
                        ground = None
                        for edge in p_or_s.incoming:
                            if edge.parent == parent:
                                ground = edge
                        success(unit, incoming, incoming, ground, 'F')
                        successes_for_unit += 1
                        
                else:
                    fail(unit, incoming, f'unit not R, S, L, D, E, or A: [{pt}]_{incoming.tag} in {parent}')
                    ucca_categories[incoming.tag] += 1
                    no_match += 1
                    fails_for_unit += 1

        if successes_for_unit >= 1:
            successful_units += 1
            if successes_for_unit > 1:
                warn(unit, None, f'found more than 1 plausible configuration (this may be due to remote or implicit edges): {passage}')
            deductable_multiple_fails += fails_for_unit
                
        else:
            unsuccessful_units += 1

        deductable_multiple_fails += max(0, fails_for_unit - 1)
        
print('\n\n')
print(f'total units\t{unit_counter}')
#print(f'gov and obj present\t{gov_and_obj_counter}')
print(f'successful units\t{successful_units}')
print(f'unsuccessful units\t{unsuccessful_units}={unit_counter-successful_units}={mwe_una_miss+a_b_miss+c_miss+d_miss+e_miss+f_miss+no_match-deductable_multiple_fails}')
print(f'\tMWE but not UNA\t{mwe_una_miss}')
print(f'\tR but A and B miss\t{a_b_miss}')
print(f'\tS but C miss\t{c_miss}')
print(f'\tL but D miss\t{d_miss}')
print(f'\tD or E but E miss\t{e_miss}')
print(f'\tA but F miss\t{f_miss}')
print(f'\tnot R or S or L or D\t{no_match}\t{ucca_categories}')
print('---------------------------------')
print(f'\tdeductable (multiple fails or fail and success for single unit)\t{deductable_multiple_fails}')
#print(f'config considered {tuple(considered)}: {considered_counter}')
#print(f'linked as expected: {linked_as_expected_counter}')



# print(json.dumps(to_SNACS, indent=2))
# print(json.dumps(to_UCCA, indent=2))
