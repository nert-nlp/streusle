Multiword Expressions
=====================

Multiword Expressions (MWEs) are either strong (notated with `_` in the human-readable 
markup) or weak (collocational but semantically transparent; notated with `~`). 
[Guidelines](https://github.com/nschneid/nanni/wiki/MWE-Annotation-Guidelines)

Token-level MWE-positional flags are as follows (with frequency counts):

    46234 O  Not part of or inside any MWE
      770 o  Not part of any MWE, but inside the gap of an MWE
     3607 B  First token of an MWE, not inside a gap
       29 b  First token of an MWE, inside the gap of another MWE
     4089 Ī  Token continuing a strong MWE, not inside a gap
       34 ī  Token continuing a strong MWE, inside the gap of another MWE
      813 Ĩ  Token continuing a weak MWE, not inside a gap
        3 ĩ  Token continuing a weak MWE, inside the gap of another MWE
    =====
    55579 tokens

Class Labels
============

Many of the lexical expressions (single-word or strong multiword) in the corpus 
have been manually annotated with semantic classes. There are 111 unique class labels.
They are listed below with their token frequencies.

Noun Supersenses
----------------

All of the 26 noun supersenses defined in WordNet are attested, including what we call 
`OTHER` (traditionally, `noun.Tops`), which here is applied to the vague word "stuff".
[Guidelines](http://www.cs.cmu.edu/~ark/ArabicSST/corpus/guidelines.html), 
[examples](http://www.cs.cmu.edu/~ark/ArabicSST/corpus/examples.html) of the approach 
to noun supersense annotation.

      88 ANIMAL
     999 ARTIFACT
     209 ATTRIBUTE
     715 ACT
     749 COGNITION
     424 COMMUNICATION
      88 BODY
     427 EVENT
      38 FEELING
     773 FOOD
    1489 GROUP
     638 LOCATION
      25 MOTIVE
      54 NATURAL OBJECT
       2 OTHER
    1224 PERSON
      23 PHENOMENON
       5 PLANT
     351 POSSESSION
      27 PROCESS
     110 QUANTITY
      35 RELATION
       6 SHAPE
      52 STATE
      34 SUBSTANCE
     527 TIME
    ====
    9112 noun supersense mentions
 
Verb Supersenses
----------------

Of the 15 verb supersenses defined in WordNet, 14 are attested in this corpus. 
There are no occurrences of `weather` verbs. 
[Annotation guidelines](http://www.cs.cmu.edu/~ark/LexSem/vsst-guidelines.html)

      81 body
     283 change
    1080 cognition
     975 communication
      11 competition
      93 consumption
      47 contact
      65 creation
     245 emotion
     613 motion
     144 perception
     310 possession
     945 social
    2797 stative
    ====
    7689 verb supersense mentions

Preposition Supersenses
-----------------------

There are 75 preposition supersenses in total, but 7 of them serve only as abstractions 
to structure the hierarchy, and 5 (`3DMedium`, `Co-Patient`, `Creator`, `Temporal`, and `Transit`) 
were not attested in this corpus. That leaves the 63 listed below. 
See [PrepWiki](http://tiny.cc/prepwiki) for their interpretation and hierarchical organization.

(A regular expression matching these as distinct from other class labels is: `^[0-9A-Z].*[a-z].*`)

      21 1DTrajectory
      18 2DArea
      27 Accompanier
      20 Activity
       1 Age
      38 Agent
      72 Approximator
     143 Attribute
      83 Beneficiary
       6 Causer
      63 Circumstance
       1 ClockTimeCxn
      41 Co-Agent
       1 Co-Participant
      17 Co-Theme
     135 Comparison/Contrast
       1 Contour
       5 Course
      66 DeicticTime
     153 Destination
     133 Direction
      40 Donor/Speaker
     102 Duration
      30 Elements
      21 EndState
      29 EndTime
      25 Experiencer
      97 Explanation
      39 Extent
       9 Frequency
      89 Function
       7 Goal
      57 InitialLocation
      21 Instance
       7 Instrument
     596 Location
      37 Locus
      50 Manner
       2 Material
      19 Means
      29 Patient
      78 Possessor
      73 ProfessionalAspect
     298 Purpose
      94 Quantity
      97 Recipient
      38 Reciprocation
     131 RelativeTime
      62 Scalar/Rank
      21 Source
      40 Species
      10 StartState
      27 StartTime
      77 State
     105 Stimulus
     134 Superset
     200 Theme
     162 Time
     133 Topic
      52 Value
       2 ValueComparison
      10 Via
      55 Whole
    ====
    4250 preposition supersense mentions

Non-supersense Labels
---------------------

These were applied to tokens flagged by our heuristics for annotation with a noun, verb, 
or preposition supersense, but which actually had a different grammatical function.

       9 ??  Unintelligible or violently ungrammatical.
     745 `   Used for miscellaneous words that do not deserve supersenses, including "as" in as-as constructions, emoticons, and some other cases that were annotated before the label refinements below (`d, `o, etc.) were introduced.
    1322 `a  Auxiliaries not POS-tagged as MD. Includes multiword "quasi-modals" like "have to" indicating necessity or obligation.
      95 `d  Discourse expression. Excludes subordinators marking a semantic role (such as time or explanation). For historical reasons some discourse expressions are labeled `.
     484 `i  The word "to" used as infinitive marker, but not marking a Purpose or Function adjunct. Includes complements ("want to").
      91 `j  Adjectival expression.
       4 `o  Indefinite pronoun (tagged as a noun in PTB). (For historical reasons most pronouns are labeled ` -- `o was only recently introduced.)
      74 `r  Adverbial expression that does not count as a preposition or PP. E.g., "too" and "then" when spelled correctly (as opposed to "to", "than").
