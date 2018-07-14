#!/bin/bash
set -eux

# Sanity check
./conllulex2json.py streusle.conllulex > /dev/null

mkdir -p {train,dev,test}

./stats.sh streusle.conllulex

python split.py streusle.conllulex ud_train_sent_ids.txt > train/streusle.ud_train.conllulex

python split.py streusle.conllulex ud_dev_sent_ids.txt > dev/streusle.ud_dev.conllulex

python split.py streusle.conllulex ud_test_sent_ids.txt > test/streusle.ud_test.conllulex

cd train
../stats.sh streusle.ud_train.conllulex
cd -

cd dev
../stats.sh streusle.ud_dev.conllulex
cd -

cd test
../stats.sh streusle.ud_test.conllulex
cd -

echo "Done with release.sh"
