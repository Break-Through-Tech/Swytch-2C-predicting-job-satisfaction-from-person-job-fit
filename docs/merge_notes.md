# GSS + O*NET Merge Notes

Working notes for the GSS + O*NET merge (issue #12). These will become the write-up of what got joined and what didn't.

## Follow-ups from the crosswalk PR (#17)

### 1. Blank codes (~4% of respondents)
81 of the 2,144 usable GSS rows get no Work Values. Most of them fall in a few occupations, so the missing rows are not random:

| Census code | Occupation | Usable rows | Reason |
|---|---|---|---|
| 2540 | Teacher assistants | 19 | `no data`: all 3 O*NET 2019 codes lack Work Values |
| 5940 | Office/admin support, all other | 11 | `no data` |
| 9140 | Taxi drivers and chauffeurs | 9 | `no data` |
| 9830 | Military, rank not specified | 6 | Not in the Census list; O*NET doesn't cover the military |
| other `no data` codes | | 36 | Smaller groups (3245, 8220, 0060, 1240, 5420, 9150, ...) |

To decide: fill the gaps (older O*NET release, or the minor SOC group average) or drop them and note it as a limitation. Also decide whether to exclude military codes (9800–9830) from the analysis sample.

### 2. Partial matches with borrowed scores
Some codes are labeled `partial` but aren't just missing an "All Other" catch-all. Their values come from a neighboring occupation:

| Census code | Occupation | O*NET codes with data |
|---|---|---|
| 1020 | Software developers | 1 of 2 (Computer Programmers only) |
| 9120 | Bus drivers | 1 of 3 |
| 2340 | Other teachers and instructors | 3 of 5 |
| 4840 | Sales reps, services | 1 of 2 |

Add a flag column for these codes so EDA can check results without them. This is a bias risk more than a missing-data one.

### 3. Join key format
Read the crosswalk with `dtype={'census_code': str}` and build the GSS key as `occ10.astype(int).astype(str).str.zfill(4)`. If the key formats are mixed, the merge matches only 81% of rows and doesn't raise an error.

### 4. Repo cleanup ✅
Deleted the duplicate `data/2024/GSS2024.sav` (identical to `data/GSS2024.sav`), untracked `.DS_Store` and `.ipynb_checkpoints/`, and added them to `.gitignore`.
