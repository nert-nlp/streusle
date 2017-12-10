import csv, json, os
os.chdir('C:\\Users\\Austin\\Desktop')

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
         'psst-tokens-revisions_2017-11-06.csv',
         'allbacktick-tokens-revisions_2017-11-06.csv']

for f in files:
    with open(f, 'r', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tmp = row['token ID']
            id = tmp[:tmp.index(':')] # sentence id
            length = len(row['token'].split())
            start = int(tmp[tmp.index(':')+1:]) + 1 # sst format indices start at 1
            tokens = range(start, start+length) # indices of preposition (may be more than one token)
            v2_scene = row['v2 Scene Role']
            v2_func = row['v2 Prep Function']
            v2 = v2_scene+'|'+v2_func if len(v2_func)>0 else v2_scene
            prep = row['token']
            if not v2_scene in acceptible_labels: continue
            print(id + ' ' + prep + ' ' + v2)
            # edit json
            for i,t in enumerate(tokens):
                # if token missing, add it
                if not str(t) in jsons[id]['labels']:
                    jsons[id]['labels'][str(t)] = [row['token'].split()[i], v2]
                print(jsons[id]['labels'][str(t)])
                jsons[id]['labels'][str(t)][1] = v2
                print(jsons[id]['labels'][str(t)])

# read streusle.sst
with open('streusle_v4.sst','w+') as tsv:
    for id in sorted(token_ids):
        tsv.write(id+'\t'+sents[id]+'\t'+json.dumps(jsons[id])+'\n')