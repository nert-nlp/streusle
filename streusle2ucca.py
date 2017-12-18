import sys
import json
import copy
import argparse

from operator import itemgetter
from collections import defaultdict

import uccaapp as ua
import uccaapp.api as uapi
import uccaapp.upload_task as uup



EXT_TO_INT_IDS = {}
EXT_TO_INT_IDS["42416"] = 2898
EXT_TO_INT_IDS["34501"] = 2784

LABEL_TO_CAT = {"ANIMAL": "n", "ARTIFACT": "n", "ATTRIBUTE": "n", "ACT": "n", "COGNITION": "n", "COMMUNICATION": "n", "BODY": "n", "EVENT": "n", \
      "FEELING": "n", "FOOD": "n", "GROUP": "n", "LOCATION": "n", "MOTIVE": "n", "NATURAL OBJECT": "n", "OTHER": "n", "PERSON": "n", "PHENOMENON": "n", "PLANT": "n", \
     "POSSESSION": "n", "PROCESS": "n", "QUANTITY": "n", "RELATION": "n", "SHAPE": "n", "STATE": "n", "SUBSTANCE": "n", "TIME": "n", \
     "body": "v",      "change": "v",     "cognition": "v",      "communication": "v",       "competition": "v",       "consumption": "v", \
      "contact": "v",       "creation": "v",      "emotion": "v",      "motion": "v",      "perception": "v",      "possession": "v",      "social": "v",     "stative": "v", \
    "1DTrajectory": "p",       "2DArea": "p",       "Accompanier": "p",       "Activity": "p",        "Age": "p",      "Agent": "p",       "Approximator": "p", \
     "Attribute": "p",       "Beneficiary": "p",        "Causer": "p",       "Circumstance": "p",        "ClockTimeCxn": "p",       "Co-Agent": "p",        "Co-Participant": "p", \
      "Co-Theme": "p",      "Comparison/Contrast": "p",        "Contour": "p",        "Course": "p",       "DeicticTime": "p",      "Destination": "p", \
     "Direction": "p",       "Donor/Speaker": "p",      "Duration": "p",       "Elements": "p",       "EndState": "p",       "EndTime": "p",       "Experiencer": "p", \
      "Explanation": "p",       "Extent": "p",        "Frequency": "p",       "Function": "p",        "Goal": "p",       "InitialLocation": "p",       "Instance": "p", \
       "Instrument": "p",      "Location": "p",       "Locus": "p",       "Manner": "p",        "Material": "p",       "Means": "p",       "Patient": "p", \
      "Possessor": "p",       "ProfessionalAspect": "p",      "Purpose": "p",       "Quantity": "p",       "Recipient": "p",       "Reciprocation": "p", \
     "RelativeTime": "p",       "Scalar/Rank": "p",       "Source": "p",       "Species": "p",       "StartState": "p",       "StartTime": "p",       "State": "p", \
     "Stimulus": "p",      "Superset": "p",      "Theme": "p",      "Time": "p",      "Topic": "p",       "Value": "p",        "ValueComparison": "p",       "Via": "p",       "Whole": "p", \
      "??": "p",       "`": "p",       "`a": ".",       "`d": "p",       "`i": "p",       "`j": ".",       "`o": ".",       "`r": "."}

mwe_layer = {'id': 64, 'name': 'Multiword Expressions', 'description': '<p>Strong MWEs (including single-word expressions) and weak MWEs<br/></p>', 'type': 'ROOT', 'tooltip': 'Strong MWEs (including single-word expressions) and weak MWEs', 'parent': None, 'children': [{'id': 68, 'name': 'SNACS fourth attempt (coarsening layer?)', 'type': 'COARSENING'}, {'id': 65, 'name': 'SNACS second try', 'type': 'REFINEMENT'}, {'id': 67, 'name': 'SNACS third attempt', 'type': 'REFINEMENT'}, {'id': 70, 'name': 'SNACS with all backtick categories', 'type': 'REFINEMENT'}], 'projects': [{'id': 78, 'name': 'MWEs second try'}], 'categories': [{'id': 54, 'name': 'Adpositional Expression (Strong)', 'shortcut_key': 'p', 'was_default': False, 'description': '<p>Adposition (preposition/postposition) or case marker: single-word or strong multiword expression<br/></p><p><br/></p><p><br/></p>', 'abbreviation': 'P', 'tooltip': 'Adposition (preposition/postposition) or case marker: single-word or strong multiword expression'}, {'id': 53, 'name': 'Verbal Expression (Strong)', 'shortcut_key': 'v', 'was_default': False, 'description': '<p>Verb: single-word or strong multiword expression<br/></p>', 'abbreviation': 'V', 'tooltip': 'Verb: single-word or strong multiword expression'}, {'id': 52, 'name': 'Nominal Expression (Strong)', 'shortcut_key': 'n', 'was_default': False, 'description': '<p>Noun: single-word or strong multiword expression</p><p><br/></p><p><br/></p>', 'abbreviation': 'N', 'tooltip': 'Noun: single-word or strong multiword expression'}, {'id': 56, 'name': 'Other strong expression', 'shortcut_key': '.', 'was_default': False, 'description': '<p>Other expression (single-word or strong multiword)<br/></p>', 'abbreviation': '.', 'tooltip': 'Other strong expression'}, {'id': 108, 'name': 'Verbal Expression (Weak)', 'shortcut_key': 'c', 'was_default': False, 'description': '<p>Verb: weak multiword expression<br/></p>', 'abbreviation': 'C', 'tooltip': 'Verb: weak multiword expression'}, {'id': 109, 'name': 'Adpostitional Expression (Weak)', 'shortcut_key': 'o', 'was_default': False, 'description': '<p>Adposition (preposition/postposition) or case marker: weak multiword expression<!--EndFragment--><br/><br/><br/></p>', 'abbreviation': 'O', 'tooltip': 'Adposition (preposition/postposition) or case marker: weak multiword expression'}, {'id': 110, 'name': 'Other Weak MWE', 'shortcut_key': ',', 'was_default': False, 'description': '<p>Other Weak Multiword Expression (not nominal, verbal, or prepositional)<br/></p>', 'abbreviation': ',', 'tooltip': 'Other Weak MWE (not nominal, verbal, or prepositional)'}, {'id': 107, 'name': 'Nominal Expression (Weak)', 'shortcut_key': 'b', 'was_default': False, 'description': '<p>Noun: weak multiword expression<br/></p>', 'abbreviation': 'B', 'tooltip': 'Noun: weak multiword expression'}], 'restrictions': [{'type': 'FORBID_ANY_CHILD', 'categories_1': [{'id': 54, 'shortcut_key': 'p', 'selected': False, 'abbreviation': 'P', 'name': 'Adpositional Expression (Strong)'}, {'id': 53, 'shortcut_key': 'v', 'selected': False, 'abbreviation': 'V', 'name': 'Verbal Expression (Strong)'}, {'id': 52, 'shortcut_key': 'n', 'selected': False, 'abbreviation': 'N', 'name': 'Nominal Expression (Strong)'}, {'id': 56, 'shortcut_key': '.', 'selected': False, 'abbreviation': '.', 'name': 'Other strong expression'}], 'categories_2': []}, {'type': 'FORBID_CHILD', 'categories_1': [{'id': 108, 'shortcut_key': 'c', 'selected': True, 'abbreviation': 'C', 'name': 'Verbal Expression (Weak)'}, {'id': 109, 'shortcut_key': 'o', 'selected': True, 'abbreviation': 'O', 'name': 'Adpostitional Expression (Weak)'}, {'id': 110, 'shortcut_key': ',', 'selected': True, 'abbreviation': ',', 'name': 'Other Weak MWE'}, {'id': 107, 'shortcut_key': 'b', 'selected': True, 'abbreviation': 'B', 'name': 'Nominal Expression (Weak)'}], 'categories_2': [{'id': 108, 'shortcut_key': 'c', 'selected': True, 'abbreviation': 'C', 'name': 'Verbal Expression (Weak)'}, {'id': 109, 'shortcut_key': 'o', 'selected': True, 'abbreviation': 'O', 'name': 'Adpostitional Expression (Weak)'}, {'id': 110, 'shortcut_key': ',', 'selected': True, 'abbreviation': ',', 'name': 'Other Weak MWE'}, {'id': 107, 'shortcut_key': 'b', 'selected': True, 'abbreviation': 'B', 'name': 'Nominal Expression (Weak)'}]}], 'is_active': True, 'created_by': {'id': 29, 'first_name': 'Jakob', 'last_name': 'Prange', 'name': 'Jakob Prange'}, 'created_at': '2017-10-20T18:42:17.793133Z', 'updated_at': '2017-10-20T18:42:17.845194Z', 'slotted': False}
CAT_SHORTCUT_TO_INT_ID = {}
for cat in mwe_layer["categories"]:
    CAT_SHORTCUT_TO_INT_ID[cat["shortcut_key"]] = cat["id"]
    
ref_layer = {'id': 70, 'name': 'SNACS with all backtick categories', 'description': '<p>SNACS with all backtick categories<br/></p>', 'type': 'REFINEMENT', 'tooltip': 'SNACS with all backtick categories', 'parent': {'id': 64, 'name': 'Multiword Expressions', 'description': '<p>Strong MWEs (including single-word expressions) and weak MWEs<br/></p>', 'type': 'ROOT', 'tooltip': 'Strong MWEs (including single-word expressions) and weak MWEs', 'parent': None, 'children': [{'id': 68, 'name': 'SNACS fourth attempt (coarsening layer?)', 'type': 'COARSENING'}, {'id': 65, 'name': 'SNACS second try', 'type': 'REFINEMENT'}, {'id': 67, 'name': 'SNACS third attempt', 'type': 'REFINEMENT'}, {'id': 70, 'name': 'SNACS with all backtick categories', 'type': 'REFINEMENT'}], 'projects': [{'id': 78, 'name': 'MWEs second try'}], 'categories': [{'id': 54, 'name': 'Adpositional Expression (Strong)', 'shortcut_key': 'p', 'was_default': False, 'description': '<p>Adposition (preposition/postposition) or case marker: single-word or strong multiword expression<br/></p><p><br/></p><p><br/></p>', 'abbreviation': 'P', 'tooltip': 'Adposition (preposition/postposition) or case marker: single-word or strong multiword expression'}, {'id': 53, 'name': 'Verbal Expression (Strong)', 'shortcut_key': 'v', 'was_default': False, 'description': '<p>Verb: single-word or strong multiword expression<br/></p>', 'abbreviation': 'V', 'tooltip': 'Verb: single-word or strong multiword expression'}, {'id': 52, 'name': 'Nominal Expression (Strong)', 'shortcut_key': 'n', 'was_default': False, 'description': '<p>Noun: single-word or strong multiword expression</p><p><br/></p><p><br/></p>', 'abbreviation': 'N', 'tooltip': 'Noun: single-word or strong multiword expression'}, {'id': 56, 'name': 'Other strong expression', 'shortcut_key': '.', 'was_default': False, 'description': '<p>Other expression (single-word or strong multiword)<br/></p>', 'abbreviation': '.', 'tooltip': 'Other strong expression'}, {'id': 108, 'name': 'Verbal Expression (Weak)', 'shortcut_key': 'c', 'was_default': False, 'description': '<p>Verb: weak multiword expression<br/></p>', 'abbreviation': 'C', 'tooltip': 'Verb: weak multiword expression'}, {'id': 109, 'name': 'Adpostitional Expression (Weak)', 'shortcut_key': 'o', 'was_default': False, 'description': '<p>Adposition (preposition/postposition) or case marker: weak multiword expression<!--EndFragment--><br/><br/><br/></p>', 'abbreviation': 'O', 'tooltip': 'Adposition (preposition/postposition) or case marker: weak multiword expression'}, {'id': 110, 'name': 'Other Weak MWE', 'shortcut_key': ',', 'was_default': False, 'description': '<p>Other Weak Multiword Expression (not nominal, verbal, or prepositional)<br/></p>', 'abbreviation': ',', 'tooltip': 'Other Weak MWE (not nominal, verbal, or prepositional)'}, {'id': 107, 'name': 'Nominal Expression (Weak)', 'shortcut_key': 'b', 'was_default': False, 'description': '<p>Noun: weak multiword expression<br/></p>', 'abbreviation': 'B', 'tooltip': 'Noun: weak multiword expression'}], 'restrictions': [{'type': 'FORBID_ANY_CHILD', 'categories_1': [{'id': 54, 'shortcut_key': 'p', 'selected': False, 'abbreviation': 'P', 'name': 'Adpositional Expression (Strong)'}, {'id': 53, 'shortcut_key': 'v', 'selected': False, 'abbreviation': 'V', 'name': 'Verbal Expression (Strong)'}, {'id': 52, 'shortcut_key': 'n', 'selected': False, 'abbreviation': 'N', 'name': 'Nominal Expression (Strong)'}, {'id': 56, 'shortcut_key': '.', 'selected': False, 'abbreviation': '.', 'name': 'Other strong expression'}], 'categories_2': []}, {'type': 'FORBID_CHILD', 'categories_1': [{'id': 108, 'shortcut_key': 'c', 'selected': True, 'abbreviation': 'C', 'name': 'Verbal Expression (Weak)'}, {'id': 109, 'shortcut_key': 'o', 'selected': True, 'abbreviation': 'O', 'name': 'Adpostitional Expression (Weak)'}, {'id': 110, 'shortcut_key': ',', 'selected': True, 'abbreviation': ',', 'name': 'Other Weak MWE'}, {'id': 107, 'shortcut_key': 'b', 'selected': True, 'abbreviation': 'B', 'name': 'Nominal Expression (Weak)'}], 'categories_2': [{'id': 108, 'shortcut_key': 'c', 'selected': True, 'abbreviation': 'C', 'name': 'Verbal Expression (Weak)'}, {'id': 109, 'shortcut_key': 'o', 'selected': True, 'abbreviation': 'O', 'name': 'Adpostitional Expression (Weak)'}, {'id': 110, 'shortcut_key': ',', 'selected': True, 'abbreviation': ',', 'name': 'Other Weak MWE'}, {'id': 107, 'shortcut_key': 'b', 'selected': True, 'abbreviation': 'B', 'name': 'Nominal Expression (Weak)'}]}], 'is_active': True, 'created_by': {'id': 29, 'first_name': 'Jakob', 'last_name': 'Prange', 'name': 'Jakob Prange'}, 'created_at': '2017-10-20T18:42:17.793133Z', 'updated_at': '2017-10-20T18:42:17.845194Z', 'slotted': False}, 'children': [], 'projects': [{'id': 82, 'name': 'Preposition Supersenses (all backtick)'}], 'categories': [{'id': 119, 'name': '`r'}, {'id': 118, 'name': '`o'}, {'id': 117, 'name': '`j'}, {'id': 116, 'name': '`i'}, {'id': 115, 'name': '`d'}, {'id': 114, 'name': '`a'}, {'id': 113, 'name': '`'}, {'id': 112, 'name': '??'}, {'id': 111, 'name': '?'}, {'id': 69, 'name': 'Path'}, {'id': 75, 'name': 'Participant'}, {'id': 100, 'name': 'InsteadOf'}, {'id': 58, 'name': 'Circumstance'}, {'id': 102, 'name': 'RateUnit'}, {'id': 105, 'name': 'SocialRel'}, {'id': 106, 'name': 'OrgRole'}, {'id': 104, 'name': 'Approximator'}, {'id': 78, 'name': 'Co-Agent'}, {'id': 79, 'name': 'Theme'}, {'id': 80, 'name': 'Co-Theme'}, {'id': 81, 'name': 'Topic'}, {'id': 82, 'name': 'Stimulus'}, {'id': 83, 'name': 'Experiencer'}, {'id': 73, 'name': 'Explanation'}, {'id': 84, 'name': 'Originator'}, {'id': 85, 'name': 'Recipient'}, {'id': 86, 'name': 'Cost'}, {'id': 87, 'name': 'Beneficiary'}, {'id': 88, 'name': 'Instrument'}, {'id': 89, 'name': 'Configuration'}, {'id': 90, 'name': 'Identity'}, {'id': 91, 'name': 'Species'}, {'id': 92, 'name': 'Gestalt'}, {'id': 94, 'name': 'Whole'}, {'id': 95, 'name': 'Characteristic'}, {'id': 96, 'name': 'Possession'}, {'id': 93, 'name': 'Possessor'}, {'id': 97, 'name': 'Part/Portion'}, {'id': 98, 'name': 'Stuff'}, {'id': 99, 'name': 'Accompanier'}, {'id': 101, 'name': 'ComparisonRef'}, {'id': 103, 'name': 'Quantity'}, {'id': 59, 'name': 'Temporal'}, {'id': 61, 'name': 'StartTime'}, {'id': 62, 'name': 'EndTime'}, {'id': 63, 'name': 'Frequency'}, {'id': 60, 'name': 'Time'}, {'id': 64, 'name': 'Duration'}, {'id': 65, 'name': 'Interval'}, {'id': 66, 'name': 'Locus'}, {'id': 67, 'name': 'Source'}, {'id': 68, 'name': 'Goal'}, {'id': 70, 'name': 'Direction'}, {'id': 71, 'name': 'Extent'}, {'id': 72, 'name': 'Manner'}, {'id': 74, 'name': 'Purpose'}, {'id': 76, 'name': 'Causer'}, {'id': 77, 'name': 'Agent'}], 'restrictions': [{'type': 'FORBID_ANY_CHILD', 'categories_1': [{'id': 54, 'shortcut_key': 'p', 'selected': False, 'abbreviation': 'P', 'name': 'Adpositional Expression (Strong)'}, {'id': 53, 'shortcut_key': 'v', 'selected': False, 'abbreviation': 'V', 'name': 'Verbal Expression (Strong)'}, {'id': 52, 'shortcut_key': 'n', 'selected': False, 'abbreviation': 'N', 'name': 'Nominal Expression (Strong)'}, {'id': 56, 'shortcut_key': '.', 'selected': False, 'abbreviation': '.', 'name': 'Other strong expression'}], 'categories_2': []}], 'is_active': True, 'created_by': {'id': 29, 'first_name': 'Jakob', 'last_name': 'Prange', 'name': 'Jakob Prange'}, 'created_at': '2017-11-28T02:45:54.940012Z', 'updated_at': '2017-11-28T02:45:54.942103Z', 'slotted': True}
CAT_TO_INT_ID = {}
for cat in ref_layer["categories"]:
    CAT_TO_INT_ID[cat["name"]] = cat["id"]

def label_to_cat(string, default="."):
    first = string[0]
    if first in "?`":
        return "."
    if first.isupper():
        if string[1].isupper():
            return "n"
        else:
            return "p"
    elif first.islower():
        return "v"
    else:
        return default

class SSTPassage:
    def __init__(self, passage_id, filename, upload=False, project=78, source=13, tok_task=None, ann_task=None, ref_task=None, tokenize=True, annotate=True, refine=True, username="", password="", verbose=False):
        self.sentences = []
        self.ID = passage_id
        
#         self.tok_task = tok_task
#         self.ann_task = ann_task
#         self.ref_task = ref_task
        self.tokens = []
        self.annotation_units = []
        self.refined_annotation_units = []
        
        self.offsets = []
        with open(filename) as f:
            local_offset = 0
            for line in f:
                sent = self.read_line(line)
                sent["offset"] = local_offset
                self.sentences.append(sent)
                self.offsets.append(local_offset)
                local_offset += len(sent["words"])
        
        if upload:
            self.server_accessor = uapi.ServerAccessor(server_address="http://ucca.development.cs.huji.ac.il", \
                                email=username, password=password, \
                                auth_token="", project_id=project, source_id=source, verbose=verbose)
            self.project = self.server_accessor.get_project(78)
            self.passage = self.server_accessor.get_passage(EXT_TO_INT_IDS[self.ID])
        else:
            self.server_accessor = None
            self.project = None
            self.passage = None
        
        if tokenize:
            self.tokens = self.tokenize()
            if upload:
                if tok_task == None:
                    d = {'parent': None, \
                     'children': [], \
                     'type': 'TOKENIZATION', \
                     'status': 'NOT_STARTED', \
                    'project': self.project, \
    #                  'user': self.user, \
                    'passage': self.passage, \
                     'is_demo': False, \
                     'manager_comment': 'test', \
                     'user_comment': '', \
                     'out_of_date': False, \
                     'obseleted_by': None, \
                     'parent_obseleted_by': None, \
                     'is_active': True}
    #                  'created_by': self.user}
    
                    self.tok_task = self.server_accessor.create_tokenization_task(**d)
                else:
                    self.tok_task = self.server_accessor.get_task(tok_task)
                
                if self.tok_task["status"] != "SUBMITTED":
                    self.server_accessor.submit_tokenization_task(id=self.tok_task["id"], tokens=self.tokens, user_comment="uploaded automatically")
                self.user_tok_task = self.server_accessor.get_user_task(self.tok_task["id"])
      
            if annotate:
                self.annotation_units = self.annotate()
                if upload:
                    if ann_task == None:
                        d = {'parent': self.tok_task, \
                         'children': [], \
                         'type': 'ANNOTATION', \
                         'status': 'NOT_STARTED', \
                        'project': self.project,\
    #                      'user': self.user, \
                        'passage': self.passage, \
                         'is_demo': False, \
                         'manager_comment': 'test', \
                         'user_comment': '', \
                         'out_of_date': False, \
                         'obseleted_by': None, \
                         'parent_obseleted_by': None, \
                         'is_active': True}                    
    #                      'created_by': self.user}
                        self.ann_task = self.server_accessor.create_annotation_task(**d)
                    else:
                        self.ann_task = self.server_accessor.get_task(ann_task)
                        
                    if self.ann_task["status"] != "SUBMITTED":
                        self.server_accessor.submit_annotation_task(id=self.ann_task['id'], annotation_units=self.annotation_units, user_comment="uploaded automatically")
                    self.user_ann_task = self.server_accessor.get_user_task(self.ann_task["id"])

                if refine:
                    self.refined_annotation_units = self.refine()
                    if upload:
                        if ref_task == None:
                            d = { #'parent': self.ann_task, \
                             'children': [], \
                             'type': 'ANNOTATION', \
                             'status': 'NOT_STARTED', \
    #                          'project': self.ref_project,\
    #                          'user': self.user, \
    #                          'passage': self.passage, \
                             'is_demo': False, \
                             'manager_comment': 'test', \
                             'user_comment': '', \
                             'out_of_date': False, \
                             'obseleted_by': None, \
                             'parent_obseleted_by': None, \
                             'is_active': True}                        
    #                          'created_by': self.user}
                            self.ref_task = self.server_accessor.create_annotation_task(**d)
                        else:
                            self.ref_task = self.server_accessor.get_task(ref_task)
                #             
                        if self.ref_task["status"] != "SUBMITTED":
                            self.server_accessor.submit_annotation_task(id=self.ref_task['id'], annotation_units=self.refined_annotation_units, user_comment="uploaded automatically")
                        self.user_ref_task = self.server_accessor.get_user_task(self.ref_task["id"])

        
        
    def read_line(self, line):
        sent_id, _, _json = line.strip().split("\t")
        d = json.loads(_json)
        d["text"] = " ".join([word[0] for word in d["words"]])
        d["id"] = sent_id
        return d
        
    
    def tokenize(self):
        tokens = []
        ind = 0
        id = 1
        for sen in self.sentences:
            for word in sen["text"].split(" "):
                tok = {}
                tok["text"] = word
                tok["start_index"] = ind
                tok["end_index"] = ind + len(word)-1
                tok["id"] = id
                
                tokens.append(tok)
                
                id +=1
                ind = tok["end_index"] + 1

        return tokens
            
    def annotate(self):        
        annotation_units = [{'annotation_unit_tree_id': "0", \
#                             'task_id': self.ann_task["id"], \
                            'gui_status': 'OPEN', \
                            'is_remote_copy': False, \
                            'parent_id': None, \
                            'comment': '', \
                            'type': 'REGULAR', \
                            "categories": [], \
                            "children_tokens": []}]
        
        first_tok_id = self.tokens[0]["id"]
        global_offset = first_tok_id - 1
        ann_unit_tree_id = 1
        ann_unit_tree_parents = {}
        ann_unit_tree_children = {}
        for sent in self.sentences:
            seen = set()
            
            for ext_tok_id, (wrd, pos) in enumerate(sent["words"], start=1):
                int_tok_id = ext_tok_id + global_offset + sent["offset"]
                
                # weak expressions
                for _mwe in sent["~"]:
                    mwe = sorted(_mwe)
                    if mwe[0] == ext_tok_id:
                        ann_unit = {'annotation_unit_tree_id': str(ann_unit_tree_id), \
#                             'task_id': self.ann_task["id"], \
                            'gui_status': 'OPEN', \
                            'is_remote_copy': False, \
                            'parent_id': "0", \
                            'comment': '', \
                            'type': 'REGULAR'}
                        ann_unit["categories"] = [{"id": CAT_SHORTCUT_TO_INT_ID[","]}]
                        ann_unit["children_tokens"] = []
                        ann_unit_tree_children[ann_unit_tree_id] = 1
                        for ext_child_id in mwe:
                            int_child_id = ext_child_id + global_offset + sent["offset"]
                            ann_unit_tree_parents[int_child_id] = ann_unit_tree_id
                            ann_unit["children_tokens"].append({"id": int_child_id})
                        ann_unit["children_tokens"].sort(key=itemgetter("id"), reverse=False)
                        annotation_units.append(ann_unit)
                        ann_unit_tree_id += 1
                        break
                
                # strong expressions
                if int_tok_id not in seen: 
                    if int_tok_id in ann_unit_tree_parents.keys():
                        tree_parent = ann_unit_tree_parents[int_tok_id]
                        tree_id = str(tree_parent) + "-" + str(ann_unit_tree_children[tree_parent])
                        ann_unit_tree_children[tree_parent] += 1
                    else:
                        tree_parent = None
                        tree_id = str(ann_unit_tree_id)
                        ann_unit_tree_id += 1
                        
                    ann_unit = {'annotation_unit_tree_id': tree_id, \
#                                 'task_id': self.ann_task["id"], \
                                'gui_status': 'OPEN', \
                                'is_remote_copy': False, \
                                'parent_id': tree_parent, \
                                'comment': '', \
                                'type': 'REGULAR'}
                    if str(ext_tok_id) in sent["labels"].keys():
#                         cat = LABEL_TO_CAT.get(sent["labels"][str(ext_tok_id)][1], ".")
                        cat = label_to_cat(sent["labels"][str(ext_tok_id)][1], ".")
                    else:
                        cat = "."
                    ann_unit["categories"] = [{"id": CAT_SHORTCUT_TO_INT_ID[cat], "slot": 1}]
                    ann_unit["children_tokens"] = [{"id": int_tok_id}]
                    for _mwe in sent["_"]:
                        mwe = sorted(_mwe)
                        if mwe[0] == int(ext_tok_id):
                            for ext_child_id in mwe[1:]:
                                int_child_id = ext_child_id + global_offset + sent["offset"]
                                seen.add(int_child_id)
                                ann_unit["children_tokens"].append({"id": int_child_id})
                            break
                    ann_unit["children_tokens"].sort(key=itemgetter("id"), reverse=False)
                    annotation_units.append(ann_unit)
                    
            return annotation_units
        
    def refine(self):
        annotation_units = copy.deepcopy(self.annotation_units)
        
        first_tok_id = self.tokens[0]["id"]
        global_offset = first_tok_id - 1
        ext_sent_id = 0
        sent = self.sentences[0]
        current_offset = 0
        next_offset = len(self.sentences[0]["words"])
        for i, ann_unit in enumerate(annotation_units):
            children_tokens = ann_unit["children_tokens"]
            categories = ann_unit["categories"]
            if children_tokens:
                first = sorted(children_tokens, key=itemgetter("id"))[0]["id"] - global_offset
                
                if categories[0]["id"] == 54:
                    sent_labels = sent["labels"]
                    ext_tok_id = str(first - current_offset)
                    if ext_tok_id in sent_labels.keys():
                        wrd, labels = sent_labels[ext_tok_id]
                        
                        _labels = labels.split("|")
                        annotation_units[i]["categories"][0]["slot"] = 3
                        annotation_units[i]["categories"] += [{"id": CAT_TO_INT_ID[cat], "slot": j} for j, cat in enumerate(_labels, start=1)] # + categories

                if first >= next_offset:
                    ext_sent_id += 1
                    try:
                        sent = self.sentences[ext_sent_id]
                    except IndexError:
                        break
                    else:
                        current_offset = next_offset
                        next_offset += len(sent["words"])
         
        return annotation_units
        
def main():
    parser = argparse.ArgumentParser(description='Convert Streusle .sst files into UCCAApp json objects in a breeze!')
    parser.add_argument('file', type=str, help='path to the .sst file containing the Streusle passage')
    parser.add_argument('-i', '--id', type=str, help='the passage ID as assigned in the UD/Streusle corpus')
    parser.add_argument('-u', '--upload', action='store_true', help='upload the generated json objects directly to UCCAApp. *requires login credentials*')
    parser.add_argument('-n', '--username', type=str, help='UCCAApp username (email)')
    parser.add_argument('-p', '--password', type=str, help='UCCAApp password')
    parser.add_argument('-t', '--tokenization', type=int, help='existing tokenization task id to use')
    parser.add_argument('-a', '--annotation', type=int, help='existing annotation task id to use')
    parser.add_argument('-r', '--refinement', type=int, help='existing refinement task id to use')
    parser.add_argument('-v', '--verbose', action='store_true', help='')

    args = parser.parse_args()
    
    sst = SSTPassage(args.id, args.file, \
                     upload=args.upload, \
                     tok_task=args.tokenization, \
                     ann_task=args.annotation, \
                     ref_task=args.refinement, \
                     username=args.username, \
                     password=args.password, \
                     verbose=args.verbose)
    
#     sst.tokens = sst.tokenize()
#     sst.annotation_units = sst.annotate()
#     sst.refined_annotation_units = sst.refine()
    
    print(sst.tokens)
    print(sst.annotation_units)
    print(sst.refined_annotation_units)
        
        
if __name__ == "__main__":
    main()
  