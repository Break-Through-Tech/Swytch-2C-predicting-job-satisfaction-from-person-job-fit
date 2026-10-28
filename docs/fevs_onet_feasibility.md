
# Issue #22: FEVS + O*NET Merge Feasibility

## Objective

Determine whether the 2024 Federal Employee Viewpoint Survey (FEVS)
Public Release Data File can be merged with O*NET at the occupation
level to support person-level job satisfaction analysis.

Per Issue #22, stop after the feasibility assessment if the
occupation-level merge is not possible.

## Data Sources

- 2024 OPM FEVS Public Release Data File
  (`FEVS_2024_PRDF_rv20250625.csv`)
- 2024 OPM FEVS PRDF Codebook
  (`2024_OPM_FEVS_PRDF_Codebook.xlsx`)
- O*NET occupational data, including the work values and occupation
  profiles available in the project repository

## Dataset Inspection

The FEVS respondent-level dataset contains:

| Metric | Finding |
| --- | --- |
| Respondents | 87,321 |
| Variables | 96 |
| Duplicate RandomID values | 0 |
| Distinct agency codes | 4 |
| Distinct level1 codes | 20 |
| Undocumented agency codes | 0 |
| Undocumented level1 codes | 0 |
| Non-missing Q70 responses | 83,618 |
| Missing Q70 responses | 3,703 |

## Occupation Identifier Investigation

The dataset columns and official codebook were inspected for an
occupation identifier or compatible coding scheme.

No respondent-level Census occupation code, Standard Occupational
Classification (SOC) code, O*NET-SOC code, or federal occupational
series was identified.

The available organizational fields are:

- `agency`: Identifies a federal agency.
- `level1`: Identifies an agency subdivision.
- `RandomID`: Randomly assigned respondent identifier.
- `POSTWT`: Survey weighting variable.

The official codebook confirms that `agency` and `level1` represent
organizations rather than occupations.

An agency or subdivision can employ individuals in multiple
occupations. Therefore, these fields cannot determine which O*NET
occupational profile applies to an individual respondent.

## Job Satisfaction Outcome

FEVS includes `Q70`, which measures overall job satisfaction on a
five-point scale:

| Value | Response | Respondents |
| --- | --- | ---: |
| 1 | Very Dissatisfied | 3,505 |
| 2 | Dissatisfied | 7,601 |
| 3 | Neither Satisfied nor Dissatisfied | 12,810 |
| 4 | Satisfied | 36,506 |
| 5 | Very Satisfied | 23,196 |
| Missing | No response | 3,703 |

Although FEVS provides usable job satisfaction data, the outcome
cannot be reliably linked to respondent-level O*NET occupation
profiles using the identifiers in this public-release file.

## Merge Feasibility Decision: NO-GO

**The 2024 FEVS Public Release Data File cannot support a defensible
respondent-level occupation merge with O*NET.**

Reason:

1. O*NET occupational profiles require an identifiable occupation.
2. The inspected FEVS file does not contain occupation codes.
3. Agency and subdivision identifiers do not uniquely identify an
   individual's occupation.
4. Assigning an occupation from an agency alone would introduce
   unsupported assumptions about respondents' jobs.

This conclusion applies to the inspected 2024 FEVS public-release
file and the occupation-level merge specified in Issue #22.

## Acceptance Criteria Status

| Issue #22 requirement | Status |
| --- | --- |
| Identify occupation variable, granularity, and coding scheme | Complete: no occupation identifier found |
| Document merge feasibility and reason | Complete: NO-GO |
| Build crosswalk to O*NET-SOC | Not applicable due to NO-GO |
| Merge and validate row count and coverage | Not applicable due to NO-GO |
| Clean merged dataset | Not applicable due to NO-GO |
| Perform merged-data EDA | Not applicable due to NO-GO |

Following the issue instructions, work stops after the feasibility
decision. No occupation crosswalk, merged dataset, or merged-data EDA
was created.

## Reproducibility

Run the inspection script from the project root:

```powershell
.\.venv\Scripts\python.exe scripts\inspect_fevs_onet_feasibility.py
```

The script requires `pandas`, `openpyxl`, the 2024 FEVS CSV, and the
official codebook in `data/fevs/2024/`.

## Conclusion

The requested FEVS + O*NET occupation-level merge is not feasible
with the inspected public-release data. The investigation is
documented as a NO-GO in accordance with Issue #22.
