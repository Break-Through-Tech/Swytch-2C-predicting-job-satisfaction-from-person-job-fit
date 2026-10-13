# Feature Relevance Findings

## Scope and interpretation

This review covers the files currently in `data/GSS_data`, `data/O_NET_data`, and `data/Amer_Job_Qual_Surv_data`.

Relevance is assigned to the stated project question: **can job satisfaction be predicted, and does person-job fit improve prediction over background variables?**

- **Most relevant:** should be considered for the first modeling dataset or for constructing the fit features.
- **Relevant:** useful controls, alternative outcomes, subgroup analyses, or plausible secondary predictors.
- **Supporting / low priority:** useful for joins, interpretation, documentation, or stretch analyses, but not a first-pass model feature.
- **Not recommended initially:** unrelated survey modules, identifiers, duplicate representations, or fields likely to create leakage.

The labels are substantive recommendations, not a guarantee that a variable will be statistically predictive. Check missingness, skip patterns, and value labels before modeling.

## 1. GSS 2022

Source files: `GSS2022.sav`, `data_info.txt`, and the local GSS codebook PDF. The file has 1,297 columns and 4,149 records.

### Most relevant

| Columns | What they represent | Use |
|---|---|---|
| `satjob` | Work satisfaction | **Primary candidate outcome.** Recode its valid responses into a binary or ordinal target and remove non-substantive codes. |
| `satjob1` | Job satisfaction in general | Alternative outcome or sensitivity check. Do not use together with `satjob` as predictors. |
| `occ10` | Respondent's 2010 Census occupation code | **Critical linkage key** for connecting people to occupation-level O*NET information. Confirm the code system and crosswalk before joining. |
| `prestg10` | Respondent's 2010 occupational prestige score | Strong occupation-related baseline/control; can also be used to test whether fit adds information beyond status. |
| `sei10` | Respondent's 2010 socioeconomic index | Occupation/status baseline; use carefully because it is derived from occupation. |
| `hrs1` | Number of hours worked last week | Direct job-intensity control. |
| `jobsecok` | Whether job security is good | Strong job-quality predictor, but potentially too close to the satisfaction concept for a strict baseline. Run a version with and without it. |
| `proudemp` | Whether the respondent is proud to work for the employer | Relevant job-attitude predictor; likely close to the target, so treat as a possible leakage/sensitivity variable. |
| `wkvsfam` / `famvswk` | How often work and family life interfere with each other | Relevant work-life-fit/job-quality predictors; document direction and missingness. |
| `workwhts` | Hard-working versus lazy self-description | A possible individual work-value/personality proxy. Use only if its intended construct matches the fit definition. |

### Relevant baseline variables

These are appropriate for the background-only comparison model requested in the project overview:

| Columns / families | Why they matter |
|---|---|
| `realinc`, `realrinc`, `income`, `income16`, `rincome` | Individual/family income measures. Choose one conceptually appropriate measure; do not include all duplicates. |
| `educ`, `degree`, `nateduc`, `nateducy` | Education and credentials. Prefer the respondent-level measure with the clearest codebook definition. |
| `age` | Age control; consider nonlinear age effects. |
| `sex`, `sexnow1`, `sexbirth1` | Gender/sex controls, subject to the codebook and the analysis question. |
| `race`, `ethnic`, relevant race/ethnicity recodes | Demographic controls and fairness/subgroup analysis. Avoid dumping every race indicator into the model without checking coding. |
| `marital` | Household/family context control. |
| `region`, `region_7222` | Geographic control; select the version matching the 2022 sample documentation. |
| `class`, `union`, `union1`, `trdunion` | Economic position and collective-bargaining controls, when valid for the respondent's employment status. |
| `yearsjob` | Job tenure, if available for the analytic sample; likely useful for satisfaction and stability. |
| `joblose`, `jobfind`, `jobfind1` | Perceived job loss and re-employment prospects; relevant job-security predictors, but analyze separately from a strict background baseline. |

The partner, parent, and spouse versions such as `coocc10`, `paocc10`, `spocc10`, `cosei10`, `pasei10`, and `spsei10` are **secondary**. They may support household or intergenerational analyses but are not needed for the first respondent-level model.

### Relevant but conditional GSS work variables

The schema contains additional work-related fields including `coevwork`, `evwork`, `mustwork`, `overwork`, `workblks`, `workdiff`, `workfast`, `workfor1`, `workhard`, `workhsps`, `worksick`, and `workwhts`. These should not be treated as one automatic feature set: their labels cover different concepts, populations, and survey modules. Keep a variable only after checking its exact codebook wording and valid-case count.

Likewise, variables with names such as `jobfind`, `joblose`, `jobsecok`, `proudemp`, and `wkvsfam` are highly relevant substantively, but may measure job conditions that are downstream of satisfaction. Report a primary model using pre-existing/background information and a sensitivity model that adds these job-quality measures.

### Lower priority or exclude initially

- `id`, `year`, `fileversion`, `batch`, `ballot`, `sample`, and survey administration fields: identifiers/design metadata, not predictors.
- `wtssps_as`, `wtssnrps_as`: survey weights; use in a weighted analysis or robustness check rather than as ordinary predictors.
- Large religion, politics, health, family, sexuality, and attitudinal modules: only include if a specific hypothesis or fairness analysis requires them.
- Multiple versions of a measure (`realinc`/`realrinc`, several occupation/status recodes, and many spouse/parent fields): select one documented version to avoid redundancy and accidental leakage.

### GSS modeling cautions

1. `satjob` is the target and must never be included among predictors. `satjob1` is an alternative target, not an additional input.
2. Use `occ10` to join to O*NET only after checking whether the GSS occupation code is a Census 2010 code and finding the appropriate Census-to-O*NET crosswalk. O*NET's `O*NET-SOC Code` is not the same key.
3. Convert GSS special codes such as “not applicable,” “don't know,” and “no answer” to missing values using the codebook. Numeric values alone are not safe.
4. The supplied loader currently uses raw numeric values (`convert_categoricals=False`); keep a separate codebook/label map so the model does not mistake category codes for continuous quantities.






## 2. O*NET 31.0 Excel database

O*NET is occupation-level data. It does not contain each GSS respondent's personal values or satisfaction. Its role is to provide occupation profiles that can be joined to GSS respondents and compared with person-level characteristics. Most files use `O*NET-SOC Code` and `Title` as the occupation key/label.

### Most relevant files and features

| File | Key features / columns | Recommended use |
|---|---|---|
| `Work Styles.xlsx` | `Element ID`, `Element Name`, `Scale ID`, `Scale Name`, `Data Value`, confidence/date/source fields | **Best starting point for occupation-level work-value proxies.** Use work-style elements such as autonomy, achievement orientation, dependability, stress tolerance, adaptability, and social orientation when their labels fit the theoretical fit score. Pivot selected elements by occupation. |
| `Work Context.xlsx` | `Element Name`, `Scale Name`, `Category`, `Data Value`, `N`, standard error, confidence bounds, suppression/relevance flags | **Best starting point for job-condition fit.** Captures conditions such as public speaking, contact with others, physical environment, pace, schedule, and decision latitude. Preserve `N`, confidence, and suppression flags. |
| `Work Activities.xlsx` | `Element Name`, `Scale Name`, `Data Value`, survey quality fields | Occupation-level activities such as getting information, making decisions, interacting with people, and organizing work. Useful when GSS values describe preferred activities. |
| `Interests Illustrative Occupations.xlsx` | `Element Name`, `Interest Type`, `O*NET-SOC Code`, `Title` | Direct occupation-interest mapping; useful for Holland/RIASEC-style fit or occupation-interest summaries. |
| `Occupation Data.xlsx` | `O*NET-SOC Code`, `Title`, `Description` | Occupation lookup table and human-readable labels. Essential for joins and interpretation, not usually a predictive feature by itself. |
| `Job Zones.xlsx` | `Job Zone`, date/source | Broad preparation/complexity control; useful as a compact baseline or for subgroup comparisons. |
| `Skills.xlsx` equivalent: `Essential Skills.xlsx` | `Element Name`, scale/category, `Data Value`, quality fields | Occupation skill requirements; useful if the GSS provides education, ability, or work-activity preferences that can be compared to them. |
| `Knowledge.xlsx` | Knowledge-domain `Element Name`, scales, `Data Value`, quality fields | Occupation knowledge requirements; secondary fit features. |
| `Abilities.xlsx` | Ability `Element Name`, scales, `Data Value`, quality fields | Occupation ability requirements; useful for ability/requirement fit, but not a direct work-values measure. |

### Relevant supporting O*NET files

- `Education.xlsx`: required education level and related distributions; useful for education mismatch or a preparation baseline.
- `Training and Experience.xlsx`: experience/training requirements; useful for preparation mismatch.
- `Job Titles.xlsx` and `Sample of Reported Titles.xlsx`: title-to-occupation lookup and normalization, especially if the survey contains a free-text occupation title.
- `Related Occupations.xlsx`: occupation similarity and alternative mappings; useful for sensitivity analyses when the exact occupation match is uncertain.
- `Work Context Categories.xlsx`, `Task Categories.xlsx`, `Education Categories.xlsx`, `Training and Experience Categories.xlsx`: category label/reference tables, not respondent-level predictors.
- `Work Styles to Work Activities.xlsx`, `Work Styles to Work Context.xlsx`, `Abilities to Work Activities.xlsx`, `Abilities to Work Context.xlsx`, `Essential Skills to Work Activities.xlsx`, `Essential Skills to Work Context.xlsx`, and `Transferable Skills to Work Activities.xlsx` / `...Work Context.xlsx`: crosswalks between O*NET concepts. Use for feature selection or interpretation, not as additional observations.
- `Task Ratings.xlsx`, `Task Statements.xlsx`, `Tasks to DWAs.xlsx`, `GWAs to IWAs.xlsx`, and `GWAs to IWAs to DWAs.xlsx`: detailed task-level data. Potentially valuable for a refined task-fit score, but too granular for the first model.
- `Software Skills.xlsx`: useful only for a technology-specific or automation stretch question.
- `Career Interest Types.xlsx`, `Specific Interest Areas.xlsx`, and their keyword/crosswalk files: useful for interest-based fit if the GSS person-level items support it; otherwise supporting data.

### O*NET reference files, not model features

`Content Model Reference.xlsx`, `Level Scale Anchors.xlsx`, `Occupation Level Metadata.xlsx`, `Scales Reference.xlsx`, and `Survey Booklet Locations.xlsx` explain definitions, scales, survey sources, and measurement levels. Read them before combining `Data Value` columns. `Emerging Tasks.xlsx` is a specialized optional table, not a core feature source.

### O*NET recommendation

Start with a compact occupation profile built from `Work Styles`, `Work Context`, selected `Work Activities`, and `Job Zones`. Do not blindly pivot every element: this creates thousands of correlated features and weakens interpretability. Choose elements based on an explicit person-job-fit theory, then compare several fit scores. O*NET values are occupation averages, so they represent the job environment/requirements, not what an individual personally values.

## 3. American Job Quality Study 2025 (AJQS)

The folder contains three matching files: `..._codebook.xlsx`, `..._labels.xlsx`, and `..._values.xlsx`. The codebook contains variable names/types/question text; the values file contains coded responses; the labels file contains readable labels/recodes. Use the values file for analysis and the labels/codebook for interpretation. The codebook has 146 fields.

### Most relevant AJQS fields

| Columns | Meaning | Use |
|---|---|---|
| `Q4` | Overall satisfaction with the respondent's job | **Primary AJQS outcome.** This is an excellent validation/replication target, but do not combine it as a predictor when predicting itself. |
| `Q6`, `Q6_TEXT`, `Q6_RC` | Main-job occupation/category, including text and recode | Main occupation feature/link candidate. `Q6_RC` is the cleaned categorical form; it is not necessarily an O*NET-SOC code. |
| `Q9`, `Q15`, `WORKER_CLASS`, `WORKER_CLASS2` | Work status and worker class | Employment-type controls and subgroup variables. |
| `Q14` | Tenure in the main job | Strong baseline/job-stability predictor. |
| `Q17`-`Q22` | Days, work-from-home days, desired remote days, usual/max/min weekly hours | Work arrangement and workload features. |
| `Q23`-`Q25D` | Schedule unpredictability, advance notice, and control over hours/days/time off | **High-value job-quality and autonomy features.** |
| `Q27` | Work demands interfering with family/personal life | Work-life-fit predictor closely related to satisfaction. |
| `Q28` | Evaluation of hours/money tradeoff in the main job | Compensation/job-quality predictor. |
| `Q29` | Work-related negative experience in the last 12 months | Job-quality/stress predictor; inspect labels for its response coding. |
| `Q30` | Union contract coverage | Employment-condition control. |
| `Q31A`-`Q31C`, `Q32A`-`Q32C` | Important and desired improvements involving compensation, working conditions, and new technology | **Closest AJQS fields to work values/preferences.** These are especially useful for a values-versus-job-conditions analysis. |
| `Q33A`-`Q33J` | Freedom, variety, learning, pace, time, support, belonging, advancement, fairness, physical safety | **Core job-quality/person-job-fit features.** These directly measure autonomy, learning, social belonging, reward fairness, and safety. |
| `Q35A`, `Q35C`, `Q35D` | Employer-provided or self-funded training/education | Learning and development opportunity features. |
| `Q36`, `Q38A`, `Q38B` | Work interactions and relationships with supervisors/coworkers | Social environment and support features. |
| `Q39` | Technology-based performance monitoring | Control/privacy/job-quality feature. |
| `Q40` | Usual monthly main-job earnings | Compensation baseline; consider log transformation and missingness. |
| `Q47` | Satisfaction with secondary job | Secondary outcome only; use when analyzing multiple-job workers. |

### Relevant AJQS controls and secondary fields

- `Q1` life satisfaction and `Q3` self-rated health are useful controls or convergent outcomes, but they are not job satisfaction and should not replace `Q4`.
- `Q5`, `Q5_RC`, `Q11`, `Q13`, `Q16`, `Q44`, and `Q45` describe number/type of jobs, customers/organizations, and secondary-job hours/earnings. Use for multiple-job and labor-arrangement analyses.
- `Q15_TEXT`, `Q16_TEXT`, `Q55_TEXT`, and other text fields are useful for qualitative coding or occupation normalization, but require a documented text-processing plan before modeling.
- `Q46`, `Q46_RC` main reason for holding a second job; relevant only for the subset with a second job.
- `Q48`, `Q50`, and `WORKER_CLASS2` describe secondary-job role and independent-contractor status; useful for subgroup analysis.
- `Q55`, `Q55_TEXT` health-insurance source; relevant to benefits/job quality, but likely a secondary feature.
- `REGDIVISION` is a geographic control.
- `ENTITY_ID` is an identifier and must not be a predictor.

### AJQS labels and coded values

Do not infer meanings from the numeric values in `..._values.xlsx`. Join or inspect the corresponding columns in `..._labels.xlsx`; for example, `Q4=10` is a labeled response such as “completely satisfied,” not a continuous measurement without further decisions. Preserve ordinal structure where appropriate and document binary recodes.

## Recommended first analytic dataset

For the project's main comparison, construct two feature sets using GSS respondents with a valid job-satisfaction response and valid occupation code:

1. **Baseline:** `hrs1`, one income measure, education, age, sex/gender, race/ethnicity, marital status, region, union/class, and optionally `prestg10`/`sei10`.
2. **Fit-enhanced:** baseline plus a deliberately selected set of O*NET occupation profiles from `Work Styles`, `Work Context`, and selected `Work Activities`, joined through a documented Census-2010-to-O*NET-SOC crosswalk.

Use GSS `satjob` as the primary outcome. Use `jobsecok`, `proudemp`, and `wkvsfam` only in a clearly labeled expanded/sensitivity model because they may be downstream job-quality measures. Use AJQS primarily as a complementary 2025 job-quality analysis or replication dataset: it has rich job-condition questions, but its occupation categories and coding do not automatically provide a direct join to GSS/O*NET.

## Immediate next steps

1. Read the GSS codebook entries for every selected field and calculate valid counts after converting special codes to missing.
2. Inspect the exact Census occupation-code coverage in `occ10` and obtain the appropriate Census-to-O*NET crosswalk.
3. Select a small, theory-driven O*NET element list before pivoting the long tables.
4. Recode `satjob` and AJQS `Q4` separately, preserving ordinal versions for sensitivity analyses.
5. Compare baseline versus fit-enhanced AUC, calibration, and confidence intervals using the same split/CV procedure.
