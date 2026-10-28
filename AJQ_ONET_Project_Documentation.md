# AJQ + O*NET: EDA, Merge, and Logistic Regression Notes
## Files and responsibilities
| Notebook | Role | Main contents |
|---|---|---|
| `American-Job-quality(1).ipynb` | AJQ-only exploratory analysis (EDA) | Q4 distribution, occupational representation, demographics, employer type, autonomy, income/workplace comparisons, initial missingness checks |
| `AJQ_ONET_Merged(1).ipynb` | AJQ–O*NET merge and merged-data EDA | Work Values reshape, broad SOC-to-Q6 mapping, crosswalk export, left merge, match coverage, missingness, occupation counts and Work Values heatmap |
| `ajq_logistic_regression_model.ipynb` | AJQ-only classification | Baseline vs. baseline + job-quality logistic regression, shared split, coefficients, confusion matrices and threshold exploration |
| `ajq_onet_merged_logistic_regression_model(1).ipynb` | Merged-data classification | Repeats AJQ–O*NET merge, five logistic regression comparisons, occupation-control experiment, model evaluation and coefficients |

> **Note:** Both merged notebooks independently build the merge

## Dataset and outcome

| Item | Recorded result |
|---|---|
| Base survey | American Job Quality (AJQ), `JFF_formatted_public_release_labels.csv` |
| Raw input | **18,429 respondents × 153 original columns** |
| Target | `Q4` overall job satisfaction, parsed to `Q4_Numeric` (0–10) |
| Modeling population | **18,381 valid Q4 respondents**; **48** excluded from modeling because their Q4 value cannot be used |
| Binary outcome | `Highly_Satisfied = 1` for Q4 ≥ 8, otherwise 0 |
| Class balance | **7,645 highly satisfied (41.59%)**; **10,736 not highly satisfied (58.41%)** |
| Modeling split | Stratified **67% training / 33% test**; fixed random seeds and same respondents across models within each notebook |

The merged dataset and its row-count assertion use **18,381 valid-Q4 respondents**, not all 18,429 survey records.

## Occupation matching: go/no-go decision

| Question | Finding |
|---|---|
| AJQ occupation variable | `Q6` (26 observed response labels in the AJQ EDA notebook) |
| Coding | Survey-specific occupational labels, rather than a respondent-level Census code or detailed SOC code |
| Resolution | **Broad occupational groups**; most map approximately to two-digit SOC major groups |
| O*NET source | `Work Values.xlsx`, `EX` (Extent) ratings, pivoted to six Work Values per O*NET-SOC occupation |
| Detailed O*NET coverage | **874** occupation profiles constructed in the notebook |
| Decision | Go for a broad-group aggregate merge, not an exact occupation-level match |
| Main consequence | All AJQ respondents sharing a Q6 category receive the same six aggregated O*NET ratings |

The six Work Values are **Achievement, Independence, Recognition, Relationships, Support, and Working Conditions**. The exported model columns use `ONET_` prefixes (for example `ONET_Working_Conditions`). Ratings are **unweighted averages of detailed occupations** within a mapped group.

### Crosswalk and joining

| Property | Current implementation |
|---|---|
| Mapping direction | O*NET-SOC two-digit major group → AJQ `Q6` text label; healthcare-technician exception uses `29-2` as a provisional subgroup |
| Crosswalk output | `ajq_onet_crosswalk.csv`: one row per **observed non-null Q6 label**, labeled `aggregate` or `unmapped` |
| Additional aggregate output | `ajq_onet_crosswalk_aggregates.csv`: mapped AJQ category, six mean Work Values and `onet_occupation_count` |
| Direct matches | **None**: join is based on broad occupational aggregates |
| Unmatched occupations | `Military`, `Something else (please specify):`, `No response`; O*NET columns remain missing |
| Join | `df_clean.merge(..., how='left', left_on='Q6', right_on='AJQ_Category', validate='many_to_one')` |
| Match indicators | `onet_matched`, `match_level`, `merge_status` |
| Saved merged output | `ajq_onet_outputs/ajq_onet_merged.csv` |

**Crosswalk caveat:** `AJQ_Category` is a survey occupation label, **not a literal SOC or O*NET-SOC code**. The current exported crosswalk does not explicitly enumerate every constituent SOC code for each AJQ row. A formal auditable crosswalk should add a `SOC_groups`/`O*NET-SOC_codes` field and document the special `29-2` assignment. Unmatched code lists should be blank; the present crosswalk leaves their aggregated O*NET values blank. The `No response` label is included because the code reads observed Q6 labels, rather than only populated occupation codes.

### Match rate (valid-Q4 respondents, unweighted)

| Match status | Respondents | Share |
|---|---:|---:|
| Has all six aggregate Work Values | **18,267** | **99.38%** |
| Unmatched | **114** | **0.62%** |
| **Total** | **18,381** | **100%** |

Unmatched responses in the notebook: **65** “Something else (please specify):”, **32** “Military”, and **17** “No response”. Their work-value fields stay blank at the merge stage. These figures measure **availability of a broad group average**, not accuracy of identifying each person's specific job. No survey weights have been applied to the reported coverage.

## AJQ-only exploratory data analysis

Notebook: `American-Job-quality(1).ipynb`

- Explores the full raw AJQ survey and the 0–10 satisfaction outcome; shows an outcome frequency plot and category counts.
- Examines leading `Q6` occupation categories; notebook reports **26 unique Q6 labels**.
- Includes plots/crosstabs of satisfaction against employer/organization type (`Q7`), gender (`Q65`), race/ethnicity and autonomy (`Q33A`), plus additional workplace or income plots.
- Inspects missingness and selected workplace response distributions.

**Quality limitation:** Some missingness calculations take place after column selection/replacement and may miss labeled nonresponse codes. The older notebook also one-hot encodes a very large number of columns and standardizes before splitting in one experiment, so its early modeling cells should not be used as the definitive validation pipeline.

## Merged-data EDA

Notebook: `AJQ_ONET_Merged(1).ipynb`

EDA is performed on `df_eda = df_merged.copy()` before model feature selection. It:

1. Displays dataset shape, data types, duplicated-row check, and merge row-count assertion.
2. Converts common labels (`No response`, `Not sure`, `Not applicable`, blank strings) to missing values **for EDA only**.
3. Reports missing counts and percentages for **all merged columns**, with a top-15 missingness bar chart.
4. Reports binary `Highly_Satisfied` class counts and percentages.
5. Examines `Q6` occupation frequencies and O*NET match counts, including a top-12 occupations chart.
6. Plots a heatmap of the six aggregated O*NET Work Values across AJQ occupational groups.

**Outstanding EDA work:** The saved merged notebook contains three descriptive plots (missingness, occupation frequency, Work Values heatmap).

## Classification models

### AJQ-only (`ajq_logistic_regression_model.ipynb`)

The model predicts **high satisfaction (Q4 ≥ 8)** using the same valid-Q4 respondents for each feature set.

| Feature set | Included features |
|---|---|
| Baseline (**11 survey variables**) | `Q20`, `Q40`, `Q14`, `Q65`, `Q9`, `Q8`, `Q17`, `MARITAL_STATUS`, `EDUCATION`, `Q51`, `REGION` |
| Expanded (**22 survey variables**) | Baseline + `Q33A`–`Q33J`, `Q55` |

| AJQ-only model | Accuracy | ROC-AUC | F1 | Recall | Log loss |
|---|---:|---:|---:|---:|---:|
| Baseline | **62.74%** | 0.6532 | 0.4562 | 0.3757 | 0.6432 |
| Baseline + job quality | **75.72%** | 0.8307 | 0.7069 | 0.7039 | 0.4974 |

**Gain from job-quality responses:** **+12.98 percentage points in accuracy**, and **+0.1775 ROC-AUC**. The notebook shows the comparison chart, confusion matrices, top five absolute logistic-regression coefficients, and exploratory threshold curves. Among its largest encoded coefficients are categories of workplace belonging (`Q33G`) and pay fairness (`Q33I`), plus `Q51`.

### AJQ + O*NET (`ajq_onet_merged_logistic_regression_model(1).ipynb`)

All five models use a **shared stratified test split**. Missing values are handled using the training portion; categorical predictors are one-hot encoded and numerical inputs standardized. Models are fitted once and reused for metrics, coefficients and threshold plots.

| Model | Accuracy | ROC-AUC | F1 | Recall | Log loss |
|---|---:|---:|---:|---:|---:|
| AJQ baseline | **62.74%** | 0.6532 | 0.4562 | 0.3757 | 0.6432 |
| AJQ job quality | **75.72%** | 0.8307 | 0.7069 | 0.7039 | 0.4974 |
| Baseline + O*NET | **63.25%** | 0.6538 | 0.4648 | 0.3837 | 0.6428 |
| AJQ job quality + O*NET | **75.54%** | 0.8304 | 0.7047 | 0.7019 | 0.4977 |
| AJQ job quality + `Q6` occupation control | **75.87%** | 0.8306 | 0.7103 | 0.7115 | 0.4977 |

**Interpretation:** O*NET raises baseline accuracy by **0.51 percentage points** (62.74% → 63.25%), but adding it to the job-quality model slightly **lowers** test accuracy by **0.18 points** (75.72% → 75.54%). The `Q6` occupation-control model achieves the highest accuracy in these runs (**75.87%**).

**Saved modeling outputs** include `ajq_onet_model_comparison.csv` and `ajq_onet_combined_coefficients.csv` in `ajq_onet_outputs/`.

## Cleaning and interpretation decisions

- **Join first, clean for analysis second.** Preserve raw merged columns and unmatched O*NET profiles in the exported respondent-level dataset. EDA replaces common nonresponse labels in a separate copy.
- **No unmatched Work Values set to zero at merge.** Missing values are imputed **for modeling** from training data only; the merged CSV retains missingness.
- **No unsupported occupation proxies.** Military is not assigned protective-service scores; “Something else” is not guessed from a sample job title.
- **Matching is not exact.** The O*NET inputs are unweighted averages of detailed occupation profiles, not individual respondent preferences.
- **Missingness is survey-specific.** Nonresponse codes and survey routing should be checked question by question. 
- **Potential outliers remain to be documented** in the current merged EDA notebook.
- **Metrics suit binary classification.** Accuracy, ROC-AUC, F1, recall, log loss and confusion matrices are appropriate. RMSE/MAE are more appropriate if a separate model predicts the full 0–10 score; MAPE is problematic because zero is valid.
- **Exploratory results, not final validation.** All comparisons use held-out test splits, but feature or threshold choices informed by test results should be revisited with a separate validation set or cross-validation.
