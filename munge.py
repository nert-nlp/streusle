import csv, json, os, sys

# example sentence in sst
# ewtb.r.001325.3\t
# The best climbing club around .\t
# {"_": [],
# "labels":
# {"5": ["around", "Locus"],
# "4": ["club", "GROUP"],
# "3": ["climbing", "ACT"]},
# "~": [],
# "words":
# [["The", "DT"], ["best", "JJS"], ["climbing", "NN"], ["club", "NN"], ["around", "RB"], [".", "."]]}
from collections import OrderedDict

from supersenses import PSS, PSS_REMOVED

SPECIAL_LABELS = {'`', '`a', '`c', '`d', '`i', '`j', '`n', '`o', '`r', '`v', '`$', '??'}

token_ids = []
jsons = {}
sents = {}

invalid_labels = set()
modified_tokens = set()

# read streusle.sst
with open('streusle_v3.sst','r') as tsv:
    for line in tsv:
        row = line.split('\t')
        print( row )
        token_ids.append(row[0])
        sents[row[0]] = row[1]
        jsons[row[0]] = json.loads(row[2], object_pairs_hook=OrderedDict) # use ordered dict to preserve key order

# I edited the files to make the column names consistent
files = ['psst-tokens_genitive.ablodgett.csv',
         'psst-tokens-revisions.csv',
         'allbacktick-tokens-revisions.csv']

for f in files:
    with open(f, 'r', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # we need id, token_index, v2_scene, v2_func
            tmp = row['sent ID']    # token id
            id = tmp[:tmp.index(':')] # sentence id
            token_index = int(tmp[tmp.index(':')+1:]) + 1 # indices of preposition (may be more than one token; sst format indices start at 1) 
           
            v2_scene = row['v2 Scene Role']
            v2_func = row['v2 Prep Function']
            v2 = v2_scene+'|'+v2_func if len(v2_func)>0 else v2_scene # scene|function, e.g., Locus|Source
            prep = row['token']

            if tmp in modified_tokens:
                other_label = jsons[id]["labels"][str(token_index)][1]
                if not v2 or other_label==v2: continue
                print(f'Token {tmp} appears in {f} with label "{v2}" as well as another file with label "{other_label}"', file=sys.stderr)
                
            modified_tokens.add(tmp)

            if v2_scene in PSS_REMOVED or v2_func in PSS_REMOVED:
                print(f'v1 label on token {tmp} in {f}: {v2}', file=sys.stderr)
            # skip non-standard labels
            if 'p.'+v2_scene not in PSS and v2_scene not in SPECIAL_LABELS:
                invalid_labels.add(v2_scene)
                continue 
            elif v2_func and 'p.'+v2_func not in PSS:
                invalid_labels.add(v2_func)
                continue
            
            print(id + ' ' + prep + ' ' + v2)
            
            # edit json
            # example: str(token_index)='5', prep_token='around', v2='Locus'
            prep_token = row['token'].split()[0] # just the first token of multiword prepositions
            jsons[id]['labels'][str(token_index)] = [prep_token, v2]
            print(jsons[id]['labels'][str(token_index)])

# write streusle.sst
with open('streusle_v4.sst','w+') as tsv:
    for id in token_ids:
        # sort labels by token offset
        jsons[id]['labels'] = {k: jsons[id]['labels'][k] for k in sorted(jsons[id]['labels'], key=lambda k: int(k))}
        tsv.write(id+'\t'+sents[id]+'\t'+json.dumps(jsons[id])+'\n')

print(invalid_labels, file=sys.stderr)

# example input
# ewtb.r.001325.2\t
# My 8 year_old daughter loves this place .\t
# {"labels":
# {"8": ["place", "LOCATION"],
# "3": ["year", "PERSON"],
# "5": ["daughter", "PERSON"],
# "6": ["loves", "emotion"]},
# "_": [[3, 4]],
# "words": [["My", "PRP$"], ["8", "CD"], ["year", "NN"], ["old", "JJ"], ["daughter", "NN"], ["loves", "VBZ"], ["this", "DT"], ["place", "NN"], [".", "."]],
# "~": []}


# example output
# ewtb.r.001325.2\t
# My 8 year_old daughter loves this place .\t
# {"labels":
# {"6": ["loves", "emotion"],
# "5": ["daughter", "PERSON"],
# "8": ["place", "LOCATION"],
# "1": ["My", "SocialRel|Possessor"],
# "3": ["year", "PERSON"]},
# "words": [["My", "PRP$"], ["8", "CD"], ["year", "NN"], ["old", "JJ"], ["daughter", "NN"], ["loves", "VBZ"], ["this", "DT"], ["place", "NN"], [".", "."]],
# "_": [[3, 4]], "~": []}