# GSS + O*NET Merge Notes

Write-up for the GSS + O*NET merge (issue #12): what got joined and what didn't.

## What got joined

| | |
|---|---|
| **Base** | GSS 2024 (`data/GSS2024.sav`), all 3,986 respondents, 31 selected columns |
| **Joined** | O*NET Work Values (6) and Job Zone, averaged per Census 2010 code (`gss_occ10_work_values.csv`) |
| **Key** | GSS `occ10` → crosswalk `census_code`, both as 4-digit text |
| **Join type** | Left join from GSS, many-to-one (checked with `validate="many_to_one"`) |
| **Output** | `gss2024_onet_merged.csv`: 3,986 rows × 48 columns |
| **Scripts** | `notebooks/build_gss_onet_crosswalk.py` (crosswalk), then `notebooks/merge_gss_onet.py` (merge) |

**GSS columns kept:**

| Group | Columns |
|---|---|
| IDs and survey design | `id`, `year`, `ballot`, `wtssps`, `wtssnrps`, `vpsu`, `vstrat` |
| Outcome | `satjob` |
| Occupation and job | `occ10`, `indus10`, `wrkstat`, `wrkslf`, `prestg10`, `sei10` |
| Income and hours | `realrinc`, `rincom16`, `hrs1`, `hrs2`, `weekswrk` |
| Demographics | `age`, `sex`, `race`, `hispanic`, `born`, `educ`, `degree`, `marital`, `childs`, `region`, `union1` |
| Person-side values | `impjob` |

GSS missing codes (iap, don't know, no answer) come through as blank. No gaps were filled: a respondent whose occupation has no O*NET data has blank Work Values, never 0.

## Match rate

| Group | Rows | Has Work Values (unweighted) | Has Work Values (weighted) |
|---|---|---|---|
| All respondents with `occ10` | 3,720 | 96.3% | 96.5% |
| Usable rows (`occ10`, `satjob`, `wtssps`) | 2,144 | 96.2% | 96.2% |

Job Zone is filled for 98.3% of usable rows (weighted). **Dropped records: none.** The merge is a left join and the row count is checked. 266 respondents have no `occ10` and are kept with `match = "no occ10"`.

**Match type, usable rows:**

| `match` | Rows | Weighted % |
|---|---|---|
| `1:1` | 1,000 | 48.3 |
| `1:many` | 625 | 27.9 |
| `partial` | 438 | 20.0 |
| `no data` | 75 | 3.4 |
| `not in Census list` | 6 | 0.4 |

## Unmatched records cluster by occupation
81 usable rows have no Work Values, spread over 20 codes. **The top 4 codes hold 45 of them (56%)**, so the missing rows are not random. They are mostly "all other" catch-alls, drivers, and education support:

| Census code | Occupation | Usable rows | Reason |
|---|---|---|---|
| 2540 | Teacher assistants | 19 | `no data`: all 3 O*NET 2019 codes lack Work Values |
| 5940 | Office/admin support, all other | 11 | `no data` |
| 9140 | Taxi drivers and chauffeurs | 9 | `no data` |
| 9830 | Military, rank not specified | 6 | Not in the Census list; O*NET doesn't cover the military |
| 16 other codes | e.g. 3245, 8220, 0060, 1240, 5420, 9150 | 36 | `no data`, 1–4 rows each |

Dropping these rows in analysis would under-represent lower-prep service and transport jobs, which biases the O*NET features. Run `notebooks/merge_gss_onet.py` for the full list.

## Flags for EDA
- **`match`**: the crosswalk match type, plus `not in Census list` and `no occ10` for respondents the crosswalk doesn't cover.
- **`has_work_values`**: True when the six values are filled.
- **`partial_substantive`**: True for `partial` codes missing a real occupation, not just an "All Other" catch-all (SOC codes ending in 9). There are 23 codes and 171 usable rows. Their values come from a neighboring occupation, e.g. software developers (1020) get Computer Programmers' ratings only. This is a bias risk more than a missing-data one; rerun key results without these rows.

## Limitations
1. **No person-side work values in GSS 2024.** The standard GSS job-values questions (`jobinc`, `jobsec`, `jobpromo`, `jobmeans`, the ISSP work-orientation items) aren't in the 2024 file. `impjob` (importance of a fulfilling job) is the only one: 1,062 respondents, 385 with `satjob` and `occ10`. The O*NET Work Values describe what the **occupation** offers, so everyone in the same occupation gets identical values. These are occupation characteristics, not person-job fit. Person-level fit can be measured in the NSCG track (#7), which asks respondents how important each job factor is (`FAC*`). Raise at the next check-in.
2. **Occupation values are simple averages.** When a Census code maps to several O*NET occupations, each counts equally, regardless of how many people work in it.
3. **Job Zone has no Zone 1.** The O*NET release in `data/Job Zones.xlsx` has only Zones 2–5, so entry-level jobs sit in Zone 2. Codes that map to several occupations get averaged zones (70 of 538 codes aren't whole numbers).
4. **Income is missing for ~22% of usable rows** (`realrinc`, `rincom16`), the largest gap among the baseline factors. This is for the cleaning step.
5. **Weights are missing for 677 of 3,986 respondents** (`wtssps`). Check why before modeling.

## Sanity check
Across the 538 Census codes, Achievement (r = 0.83) and Recognition (r = 0.84) rise with Job Zone, as expected. So do Working Conditions (0.80) and Independence (0.71). Support doesn't (−0.11).

## Decisions made
- **Gap filling:** none. Unmatched rows stay blank and flagged. Filling or dropping them is a cleaning decision.
- **Military (9830):** kept and flagged as `not in Census list`. Exclude in the analysis step if needed.
- **GSS year:** 2024 only, per Jim's note to use 2024 for OCC10.
- **Job Zone:** included, as a control and for the sanity check.

## Repo cleanup ✅
Deleted the duplicate `data/2024/GSS2024.sav` (identical to `data/GSS2024.sav`), untracked `.DS_Store` and `.ipynb_checkpoints/`, and added them to `.gitignore`.
