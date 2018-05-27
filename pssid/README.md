# Heuristics for automatically identifying adpositional expressions

Automatically (heuristically) identified single-word and multi-word prepositional expressions.
Each token has an additional column (the 20th column for the .conllulex format) containing its predicted category.
The value can be one of the following:
* -: is not and does not belong to a prepositional expression
* *: is a single-word prepositional expression
* N:1**: is the first word in a multi-word prepositional expression (where N >= 1 is the index of the multiword expression in the current sentence)
* N:M: is the Mth word in a multi-word prepositional expression (where M > 1 and N >= 1 is the index of the multiword expression in the current sentence)

Note that only tokens with labels ending in an asterisk (*) should get a supersense.

## Usage
```
python identify.py [-h] [-f TRAINING_FILE] [-M MODEL_FILE] [-o MODEL_OUT] [-m]
                   [-l MWE_LIST] [-i MWE_ANTI_LIST] [-e] [-a] [-b] [-c] [-d]
		   [-n CONTEXT] [-s] [-p P_MWE_MIN] [-P NON_P_MWE_MIN]
		   [--advcl-min ADVCL_MIN] [--acl-min ACL_MIN] [-L] [-g]
		   file
```
```
positional arguments:
   file                  path to the .conllulex file

optional arguments:
   -h, --help            show this help message and exit
   -f TRAINING_FILE, --training-file TRAINING_FILE
                         path to the training .conllulex file
   -M MODEL_FILE, --model-file MODEL_FILE
                         path to the model file (read)
   -o MODEL_OUT, --model-out MODEL_OUT
                         path to the model file (write)
   -m, --mwe             also look for mwes
   -l MWE_LIST, --mwe-list MWE_LIST
                         read lexical list of MWEs from file MWE_LIST
   -i MWE_ANTI_LIST, --mwe-anti-list MWE_ANTI_LIST
                         read lexical list of MWEs to EXCLUDE from file
                         MWE_ANTI_LIST
   -e, --eval            output evaluation instead of annotated lines; works
                         ONLY with full .conllulex format
   -a, --tp              true positives
   -b, --fp              false positives
   -c, --fn              false negatives
   -d, --tn              true negatives
   -n CONTEXT, --context CONTEXT
                         number of context lines to print before and after
			 target (only has effect when used with --tp, --fp,
			 --fn, or --tn)
   -s, --sst             output .sst format instead of .conlluX format
   -p P_MWE_MIN, --p-mwe-min P_MWE_MIN
                         threshold for prepositional MWE lexicon
   -P NON_P_MWE_MIN, --non-p-mwe-min NON_P_MWE_MIN
                         threshold for non-prepositional MWE lexicon
   --advcl-min ADVCL_MIN
                         threshold for advcl heads that take non-prepositional
			 infinitival complements
   --acl-min ACL_MIN     threshold for acl heads that take non-prepositional
                         infinitival complements
   -L, --lexcat          output lexical categories
   -g, --gold            re-use gold standard annotation

```

## Files

### STREUSLE splits with autoid annotation

* streusle.ud_dev.auto_id.conllulex
* streusle.ud_test.auto_id.conllulex
* streusle.ud_train.auto_id.conllulex

These files have been generated with the default settings provided by the F1-score-optimized model, using the following command:

```
python identify.py ../train/streusle.ud_train.conllulex -m --model-file models/streusle.ud_train.bestF.model > streusle.ud_train.auto_id.conllulex
python identify.py ../test/streusle.ud_test.conllulex -m --model-file models/streusle.ud_train.bestF.model > streusle.ud_test.auto_id.conllulex
python identify.py ../dev/streusle.ud_dev.conllulex -m --model-file models/streusle.ud_train.bestF.model > streusle.ud_dev.auto_id.conllulex
```

### Pretrained models

* models/streusle.ud_train.bestF.model: optimized for F1 score
* models/streusle.ud_train.bestR.model: optimized for recall


## Performance

### strict evaluation as used in Schneider et al., 2018

|       | P     | R     | F     |
|:----  |:-----:|:-----:|:-----:|
| test  | 0.888 | 0.896 | 0.892 |

### relaxed evaluation

|       | P     | R     | F     |
|:----  |:-----:|:-----:|:-----:|
| test  | 0.906 | 0.914 | 0.910 |
| train | 0.965 | 0.925 | 0.945 |
| dev   | 0.903 | 0.917 | 0.910 |
