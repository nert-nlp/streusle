"""
This script finds incorrect annotations wrt "SCONJ"
according to the following rules and exports an
updated version.

- When/ADV/advmod did you arrive/VERB/root?             (question)
- Call me when/SCONJ/mark you arrive/VERB/advcl.        (subordinate advcl)
- Tell me when/SCONJ/obj you arrived/VERB/acl:relcl.    (free relative)
"""

import argparse

p = argparse.ArgumentParser()
p.add_argument("file", help="the streusle.conllulex file")
opts = p.parse_args()


with open(opts.file, "r", encoding="utf-8") as fconll:
	lines = [line.strip() for line in fconll.readlines()]
	for i in range(len(lines)):
		if "\t" in lines[i]:
			fields = lines[i].split("\t")
			tok = fields[1]         # e.g. when, where
			upos = fields[3]        # e.g. ADV, SCONJ
			dep = fields[7]         # e.g. advmod, mark, obj
			lexcat = fields[11]     # e.g. ADV, SCONJ
			lextag = fields[-1]     # e.g. O-ADV, O-SCONJ

			if tok.lower() == "when" or tok.lower() == "where":
				if dep == "advmod":
					upos = "ADV"
					lexcat = "ADV"
				elif dep == "mark" or dep == "obj":
					upos = "SCONJ"
					lexcat = "SCONJ"
					if lextag == "O-ADV":
						lextag = "O-SCONJ"

			fields = fields[:3] + [upos] + fields[4:11] + [lexcat] + fields[12:-1] + [lextag]
			lines[i] = "\t".join(fields)

	# write the updated annos to a file
	with open("streusle_updated.conllulex", "w", encoding="utf-8") as fout:
		for line in lines:
			fout.writelines(line+"\n")
