Files
#####

streusle.ud_dev.auto_id.conllulex
streusle.ud_test.auto_id.conllulex
streusle.ud_train.auto_id.conllulex

README
######

Automatically (heuristically) identified single-word and multi-word prepositional expressions.
Each token has an additional column (the 20th column for the .conllulex format) containing its predicted category.
The value can be one of the following:

-    is not and does not belong to a prepositional expression
*    is a single-word prepositional expression
N:1**	is the first word in a multi-word prepositional expression (where N >= 1 is the index of the multiword expression in the current sentence)
N:M	is the Mth word in a multi-word prepositional expression (where M > 1 and N >= 1 is the index of the multiword expression in the current sentence)

Note that only tokens with labels ending in an asterisk (*) should get a supersense.


Statistics
##########

test
P	R	F
0.9061224489795918      0.9135802469135802      0.9098360655737705

train
P	R	F
0.9652014652014652      0.9247642026760254      0.9445502408423881

dev
P	R	F
0.9034334763948498      0.9172113289760349      0.9102702702702702
