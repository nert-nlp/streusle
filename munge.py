import csv, json, os

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


token_ids = set()
jsons = {}
sents = {}

# read streusle.sst
with open('streusle_v3.sst','r') as tsv:
    for line in tsv:
        row = line.split('\t')
        print( row )
        token_ids.add(row[0])
        sents[row[0]] = row[1]
        jsons[row[0]] = json.loads(row[2])

acceptible_labels = ['Circumstance', 'Temporal', 'Time', 'StartTime', 'EndTime', 'DeicticTime', 'Frequency', 'Duration', 'Locus', 'Source', 'Goal', 'Path', 'Direction', 'Extent', 'Means', 'Manner', 'Explanation', 'Purpose', 'Causer', 'Agent', 'Co-Agent', 'Theme', 'Co-Theme', 'Topic', 'Stimulus', 'Experiencer', 'Originator', 'Recipient', 'Cost', 'Beneﬁciary', 'Instrument', 'Identity', 'Species', 'Gestalt', 'Possessor', 'Whole', 'Characteristic', 'Possession', 'Part/Portion', 'Stuff', 'Accompanier', 'InsteadOf', 'ComparisonRef', 'RateUnit', 'Quantity', 'Approximator', 'SocialRel', 'OrgRole']

# I edited the files to make the column names consistent
files = ['psst-tokens_genitive.ablodgett.csv',
         'psst-tokens-revisions.csv',
         'allbacktick-tokens-revisions.csv']

for f in files:
    with open(f, 'r', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # we need id, token_index, v2_scene, v2_func
            tmp = row['sent ID']
            id = tmp[:tmp.index(':')] # sentence id
            token_index = int(tmp[tmp.index(':')+1:]) + 1 # indices of preposition (may be more than one token; sst format indices start at 1) 
           
            v2_scene = row['v2 Scene Role']
            v2_func = row['v2 Prep Function']
            v2 = v2_scene+'|'+v2_func if len(v2_func)>0 else v2_scene # scene|function, e.g., Locus|Source
            prep = row['token']
            
            # skip non-standard labels
            if not v2_scene in acceptible_labels: continue 
            
            print(id + ' ' + prep + ' ' + v2)
            
            # edit json
            # example: str(token_index)='5', prep_token='around', v2='Locus'
            prep_token = row['token'].split()[0] # just the first token of multiword prepositions
            # if token not in 'labels', add it
            if not str(token_index) in jsons[id]['labels']:
                jsons[id]['labels'][str(token_index)] = [prep_token, v2]
            else:
                jsons[id]['labels'][str(token_index)][1] = v2
            print(jsons[id]['labels'][str(token_index)])

# write streusle.sst
with open('streusle_v4_test.sst','w+') as tsv:
    for id in sorted(token_ids):
        tsv.write(id+'\t'+sents[id]+'\t'+json.dumps(jsons[id])+'\n')
end


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