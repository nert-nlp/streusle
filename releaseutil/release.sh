#!/bin/bash
#
set -eux

export LC_COLLATE=C

RELUTILDIR='releaseutil'
# Run from the main release directory

# Sanity check
./conllu2json.py streusle.conllu > /dev/null

mkdir -p {train,dev,test}

$RELUTILDIR/stats.sh streusle.conllu

$RELUTILDIR/split.py streusle.conllu $RELUTILDIR/ud_train_sent_ids.txt > train/streusle.ud_train.conllu

$RELUTILDIR/split.py streusle.conllu $RELUTILDIR/ud_dev_sent_ids.txt > dev/streusle.ud_dev.conllu

$RELUTILDIR/split.py streusle.conllu $RELUTILDIR/ud_test_sent_ids.txt > test/streusle.ud_test.conllu

cd train
../$RELUTILDIR/stats.sh streusle.ud_train.conllu

../conllu2json.py streusle.ud_train.conllu > streusle.ud_train.json

#../govobj.py streusle.ud_train.json > streusle.ud_train.govobj.json

../streusvis.py --colorless --sent-ids --lexcats streusle.ud_train.json > streusle.ud_train.vis
cd -

cd dev
../$RELUTILDIR/stats.sh streusle.ud_dev.conllu

../conllu2json.py streusle.ud_dev.conllu > streusle.ud_dev.json

#../govobj.py streusle.ud_dev.json > streusle.ud_dev.govobj.json

../streusvis.py --colorless --sent-ids --lexcats streusle.ud_dev.json > streusle.ud_dev.vis
cd -

cd test
../$RELUTILDIR/stats.sh streusle.ud_test.conllu

../conllu2json.py streusle.ud_test.conllu > streusle.ud_test.json

#../govobj.py streusle.ud_test.json > streusle.ud_test.govobj.json

../streusvis.py --colorless --sent-ids --lexcats streusle.ud_test.json > streusle.ud_test.vis
cd -

echo "* [train](train/STATS.md), [dev](dev/STATS.md), [test](test/STATS.md)" >> STATS.md

echo "Done with release.sh"
