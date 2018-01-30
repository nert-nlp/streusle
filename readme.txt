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
0.9042769857	0.9135802469	0.9089048106

train
P	R	F
0.9652014652	0.9247642027	0.9445502408

dev
P	R	F
0.9014989293	0.917211329	0.909287257
