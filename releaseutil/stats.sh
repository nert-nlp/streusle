#!/bin/bash
# Arg: .conllu file, e.g. streusle.conllu
DATA=$1

echo "STREUSLE Stats" > STATS.md
echo "==============" >> STATS.md
echo "" >> STATS.md
DOCS=`fgrep '# newdoc id' $DATA | wc -l`
echo "* Documents:           $DOCS" >> STATS.md
SENTS=`fgrep '# sent_id' $DATA | wc -l`
echo "* Sentences:           $SENTS" >> STATS.md
WORDS=`egrep -v '^$' $DATA | egrep -v '^#' | egrep -v '^[0-9]+[-\.][0-9]' | wc -l`
echo "* Tokens:              $WORDS (excludes UD ellipsis nodes and UD multiword tokens)" >> STATS.md
LEMMAS=`egrep -v '^$' $DATA | egrep -v '^#' | egrep -v '^[0-9]+[-\.][0-9]' | cut -f3 | sort | uniq | wc -l`
echo "* Unique lemmas:       $LEMMAS" >> STATS.md
LEXTAGS=`egrep -v '^$' $DATA | egrep -v '^#' | egrep -v '^[0-9]+[-\.][0-9]' | cut -f19 | sort | uniq | wc -l`
echo "* Unique full lextags: $LEXTAGS" >> STATS.md
echo "* [LexCat](LEXCAT.txt)" >> STATS.md
echo "* [MWEs](MWES.txt)" >> STATS.md
echo "* [Supersenses](SUPERSENSES.txt)" >> STATS.md

echo -n "Strong MWEs: " > MWES.txt
SMWES=`egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | fgrep 'MWELemma=' | wc -l`
printf "%4d\n" "$SMWES" >> MWES.txt
echo -n "...not counting goeswith MWEs: " >> MWES.txt
SMWES=`egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep 'MWELemma=[^|]+ ' | wc -l`
printf "%4d\n" "$SMWES" >> MWES.txt

echo -n "Weak MWEs:   " >> MWES.txt
WMWES=`egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | fgrep 'MWELemma[weak]=' | wc -l`
printf "%4d\n" "$WMWES" >> MWES.txt
echo -n "...not counting goeswith MWEs: " >> MWES.txt
WMWES=`egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep 'MWELemma\[weak\]=[^|]+ ' | wc -l`
printf "%4d\n" "$WMWES" >> MWES.txt

echo "" >> MWES.txt

echo "MWE Gaps" >> MWES.txt
echo "========" >> MWES.txt
GAPS=`egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep -o 'MWELemma[^|]+' | egrep -o ' <[0-9]+>' | wc -l`
SGAPS=`egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep -o 'MWELemma=[^|]+' | egrep -o ' <[0-9]+>' | wc -l`
WGAPS=`egrep -v '^$' $DATA | egrep -v '^#' |  cut -f10 | egrep -o 'MWELemma\[weak\]=[^|]+' | egrep -o ' <[0-9]+>' | wc -l`
MULTIGAPS=`egrep -v '^$' $DATA | egrep -v '^#'  | cut -f10 | egrep -o 'MWELemma[^|]+' | egrep -o '.* <[0-9]+>.* <[0-9]+>.*' | wc -l`
echo -n "Strong gaps:   " >> MWES.txt
printf "%4d\n" "$SGAPS" >> MWES.txt
echo -n "Weak gaps:     " >> MWES.txt
printf "%4d\n" "$WGAPS" >> MWES.txt
echo -n "Total gaps:    " >> MWES.txt
printf "%4d\n" "$GAPS" >> MWES.txt
echo -n "Multi-gap MWEs:" >> MWES.txt
printf "%4d\n" "$MULTIGAPS" >> MWES.txt
egrep -v '^$' $DATA | egrep -v '^#'  | cut -f10 | egrep -o 'MWELemma[^|]+' | egrep -o '.* <[0-9]+>.* <[0-9]+>.*' >> MWES.txt
echo "NOTE: The weak/total gap counts now include any gaps for a strong MWE subsumed within a weak MWE (e.g. 'offer _ bang for _ buck' subsumes 'bang for _ buck', for a total gap count of 3)" >> MWES.txt

echo "" >> MWES.txt

echo "Strong MWE lengths" >> MWES.txt
echo "==================" >> MWES.txt
echo "There are ... MWEs ... lemmas long (omitting gaps):" >> MWES.txt
egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep -o 'MWELemma=[^|]+' | sed -E 's/ <[0-9]+>//g' | sed -E 's/\S//g' | awk '{ print length+1 }' | sort -n | uniq -c >> MWES.txt

echo "" >> MWES.txt

echo "Weak MWE lengths" >> MWES.txt
echo "================" >> MWES.txt
egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep -o 'MWELemma\[weak\]=[^|]+' | sed -E 's/ <[0-9]+>//g' | sed -E 's/\S//g' | awk '{ print length+1 }' | sort -n | uniq -c >> MWES.txt

echo "" >> MWES.txt

echo "Strong MWEs by MWECat" >> MWES.txt
echo "=====================" >> MWES.txt

egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep -o 'MWECat=[^|]+' | cut -d'=' -f2 | sort | uniq -c >> MWES.txt

echo "" >> MWES.txt

echo "Weak MWEs by MWECat (where present)" >> MWES.txt
echo "===================================" >> MWES.txt

egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep -o 'MWECat\[weak\]=[^|]+' | cut -d'=' -f2 | sort | uniq -c >> MWES.txt



#egrep -v '^$' $DATA | egrep -v '^#' | cut -f12 | sort | uniq -c > LEXCAT.txt



egrep -v '^$' $DATA | egrep -v '^#' | cut -f10 | egrep -o 'Supersense[^\|]+(\|Supersense[^\|]+)*' | sed -E 's/Supersense=(p.[^|]+)/Supersense[coding]=\1|Supersense[scene]=\1/g' | sed -E 's/(Supersense=[^|]+)/\1\t_/g' | sed -E 's/([^\|]+)\|([^\|]+)/\2\t\1/g' | sed -E 's/Supersense(\[coding\]|\[scene\])?=//g' | sort | uniq -c > SUPERSENSES.txt

NSS=`cut -f10 $DATA | egrep -o 'Supersense[^\|]+(\|Supersense[^\|]+)*' | egrep '=n.' | wc -l`

VSS=`cut -f10 $DATA | egrep -o 'Supersense[^\|]+(\|Supersense[^\|]+)*' | egrep '=v.' | wc -l`

PSS=`cut -f10 $DATA | egrep -o 'Supersense[^\|]+(\|Supersense[^\|]+)*' | egrep '=p.' | wc -l`

echo "========================" >> SUPERSENSES.txt

echo "$NSS n.*" >> SUPERSENSES.txt
echo "$VSS v.*" >> SUPERSENSES.txt
echo "$PSS p.*" >> SUPERSENSES.txt

# LexCat info is now only in json (for non-MWE tokens)

# echo "" >> SUPERSENSES.txt
# echo "n.* by LexCat" >> SUPERSENSES.txt
# echo "========================" >> SUPERSENSES.txt
# cut -f12,14-15 $DATA | fgrep $'\tn.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt

# echo "" >> SUPERSENSES.txt
# echo "v.* by LexCat" >> SUPERSENSES.txt
# echo "========================" >> SUPERSENSES.txt
# cut -f12,14-15 $DATA | fgrep $'\tv.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt

# echo "" >> SUPERSENSES.txt
# echo "p.* by LexCat" >> SUPERSENSES.txt
# echo "========================" >> SUPERSENSES.txt
# cut -f12,14-15 $DATA | fgrep $'\tp.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt

# echo "" >> SUPERSENSES.txt
# echo "p.* by LexCat + construal type" >> SUPERSENSES.txt
# echo "========================" >> SUPERSENSES.txt
# # for some bizarre reason, sed and sed -E with a backreference in the pattern don't work here
# cut -f12,14-15 $DATA | fgrep $'\tp.' | python3 -c "import fileinput, re
# for ln in fileinput.input():
# 	ln = ln.strip()
# 	congruent = re.sub(r'(p\.[A-Za-z-]+)\t\1', 'p.X ~> p.X', ln)
# 	if congruent!=ln: print(congruent)
# 	else: print(re.sub(r'(p\.[A-Za-z-]+)\tp\.[A-Za-z-]+', 'p.X ~> p.Y', ln))" | sort | uniq -c >> SUPERSENSES.txt

# echo "" >> SUPERSENSES.txt
# echo "p.* by LexCat + spatiotemporality" >> SUPERSENSES.txt
# echo "(TMP = Time|Frequency|Duration|Interval|Temporal, LOC=Locus|Source|Path|Goal|Direction|Extent [not necessarily concrete])" >> SUPERSENSES.txt
# echo "========================" >> SUPERSENSES.txt
# cut -f12,14-15 $DATA | fgrep $'\tp.' | python3 -c "import fileinput, re
# for ln in fileinput.input():
# 	ln = ln.strip()
# 	lc, r, f = ln.split('\t')
# 	if r in ('p.Time', 'p.Frequency', 'p.Duration', 'p.Interval', 'p.Temporal'):
# 		r = 'p.TMP'
# 	elif r in ('p.Locus', 'p.Source', 'p.Path', 'p.Goal', 'p.Direction', 'p.Extent'):
# 		r = 'p.LOC'
# 	else:
# 		r = 'p.OTH'
# 	print(lc, '\t' + r + ' ~> *')" | sort | uniq -c >> SUPERSENSES.txt
# echo "" >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "p.* by spatiotemporality" >> SUPERSENSES.txt
echo "(TMP = Time|Frequency|Duration|Interval|Temporal, LOC=Locus|Source|Path|Goal|Direction|Extent [not necessarily concrete])" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
cut -f10 $DATA | egrep -o 'Supersense(\[scene\])?=p\.[^|]+' | sed -E 's/.*=(p\..+)/\1/g' | sed -E 's/p\.(Time|Frequency|Duration|Interval|Temporal)/p.TMP ~> */g' | sed -E 's/p\.(Locus|Source|Path|Goal|Direction|Extent)/p.LOC ~> */g' | sed -E 's/p\.[A-Z][a-z].*/p.OTH ~> */g' | sort | uniq -c >> SUPERSENSES.txt
