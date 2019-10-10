SuperSense Update Decisions
===========================

### ssupdate.md documents changes and decisions made while updating lexcats and supersenses for words and MWEs tagged with !!@, a stopgap lexcat for tokens that need to be revisited

### Last Updated: 10/07/2019, Ryan A. Mannion

---

- 	**stuff** and **thing** are marked as n.OTHER, as well as **shit** in the same sense

	> Anyway we drive around in my van and solve mysterys and shit|n.OTHER

- 	Deciding between n.ARTIFACT and n.SUBSTANCE
	- 	n.ARTIFACT is used when the object has defined
		
		e.g. desk, door, seat, book, car, building, potpourri

	- 	n.SUBSTANCE is used with most mass nouns and objects without hard borders
		
		e.g. drug, paint, shellac, grease, oil, fabric, shampoo

- 	***start*** *to* ***finish*** and ***beginning*** *to* ***end*** are no longer interpreted as MWEs, and both words in both constructions are annotated as n.TIME
	
	> start|n.TIME to finish|n.TIME
	
	> beginning|n.TIME to end|n.TIME

- 	the character "**#**" is interpreted as being the lexical category SYM as opposed to representing the word "number"