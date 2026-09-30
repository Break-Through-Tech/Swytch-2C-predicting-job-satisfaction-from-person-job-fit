# Data Cleaning & Preprocessing Documentation

This document records the data cleaning steps, missing value strategies, and feature filtering decisions applied to the merged GSS 2024 and O*NET dataset.


## 1. Initial Dataset Overview
* Starting rows: 3,986 respondents
* Total columns: 48 features spanning demographics, employment, economics, and O*NET work values.

## 2. Handling Missing Values & Target Variable
* **Target Variable (`satjob`):** Rows where job satisfaction was missing (1,204 missing) were dropped, as missing target values cannot be reliably imputed for supervised learning models.
* **Sparse / Low-Data Features:** Columns with extremely high missing rates (such as `hrs2` and `impjob`) were excluded from modeling feature sets due to insufficient data density.
* **General Imputation:** 
  * Numeric features with minor gaps were imputed using the median value to protect against skewness.
  * Categorical features were filled with a placeholder label.

## 3. Feature Grouping Strategy
The features were split into three logical modeling groups:
* **Baseline Features:** GSS demographic, economic, and employment variables (e.g., `age`, `educ`, `realrinc`, `wrkstat`).
* **Person-Job Fit Features:** O*NET psychological work values and requirements (e.g., `Achievement`, `Independence`, `Relationships`, `job_zone`).
* **Administrative & Metadata:** Identifiers, survey weights, and crosswalk flags (`id`, `ballot`, `wtssps`, etc.) were dropped from modeling inputs.

## Initial Missing Values Audit (Full 48-Column Dataset)

| Column Name | Missing Count (out of ~3,986) | Notes / Category |
| :--- | :--- | :--- |
| `hrs2` | 3,914 | Extreme sparsity (dropped) |
| `onet_no_data` | 3,115 | Merge diagnostic flag (dropped) |
| `impjob` | 2,924 | High sparsity (dropped) |
| `hrs1` | 1,785 | Employment hours |
| `realrinc` / `rincom16` | 1,641 | Income variables |
| `union1` | 1,359 | Union membership status |
| `satjob` | 1,204 | Target variable (dropped during training only) |
| `wtssps` / `wtssnrps` | 677 | Survey weights (dropped) |
| `Achievement`, `Independence`, `Recognition`, `Relationships`, `Support`, `Working Conditions` | 404 each | O*NET Work Values (unmatched codes) |
| `job_zone` | 334 | O*NET Job Zone requirement |
| `indus10` | 293 | Industry code |
| `census_title`, `soc2010`, `n_onet`, `n_with_data`, `n_with_job_zone` | 281 each | Merge metadata flags (dropped) |
| `occ10` | 266 | Occupation code |
| `prestg10` / `sei10` | 264 each | Occupational prestige/socioeconomic scores |
| `wrkslf` | 156 | Self-employed status |
| `weekswrk` | 142 | Weeks worked last year |
| `age` | 127 | Respondent age |
| `race` | 80 | Race category |
| `childs` | 42 | Number of children |
| `hispanic` | 39 | Hispanic origin |
| `educ` | 34 | Years of education |
| `sex` | 30 | Respondent sex |
| `born` | 27 | U.S. citizenship/birth status |
| `marital` | 15 | Marital status |
| `wrkstat` | 12 | Working status |
| `degree` | 7 | Highest degree earned |

## Columns Dropped & Why

19 columns were dropped before modeling to clean things up. Here's a quick breakdown of what was removed and why:

### IDs & Survey Weights
* **`id`, `year`**: `id` is just a row identifier with zero predictive signal. `year` is 2024 for every single row, so it has no variance.
* **`ballot`**: tells us which GSS survey form version the respondent answered.
* **`wtssps`, `wtssnrps`**: Official survey weights used for population demographics, not features for a machine learning model.
* **`vpsu`, `vstrat`**: Sampling error and variance strata variables from the GSS survey design.

### Merge & Crosswalk Metadata
* **`census_code`, `census_title`, `soc2010`**: Behind-the-scenes occupational codes used to link GSS jobs to O*NET. (We kept the actual O*NET work values and general prestige scores like `prestg10`, so we aren't losing the actual job characteristics).
* **`n_onet`, `n_with_data`, `n_with_job_zone`, `match`, `onet_no_data`, `partial_substantive`, `has_work_values`**: These are all diagnostic flags left over from the script that merged the GSS and O*NET files. They just track whether the merge worked, rather than telling us anything about the actual respondent.

### Sparse Features
* **`hrs2`, `impjob`**: Way too many missing values (thousands missing), so keeping them would mess with our sample size.


## Missing Values Audit (Streamlined 29-Column Dataset)

| Column Name | Missing Count (out of ~3,986) | Category / Strategy |
| :--- | :--- | :--- |
| `hrs1` | 1,785 | Employment Hours |
| `realrinc` / `rincom16` | 1,641 | Income Variables |
| `union1` | 1,359 | Union Membership |
| `satjob` | 1,204 | Target Variable (handled during model training) |
| `Achievement`, `Independence`, `Recognition`, `Relationships`, `Support`, `Working Conditions` | 404 each | O*NET Work Values (unmatched codes) |
| `job_zone` | 334 | O*NET Job Zone |
| `indus10` | 293 | Industry Code |
| `occ10` | 266 | Occupation Code |
| `prestg10` / `sei10` | 264 each | Occupational Prestige / Socioeconomic Scores |
| `wrkslf` | 156 | Self-Employed Status |
| `weekswrk` | 142 | Weeks Worked |
| `age` | 127 | Demographics (`age`) |
| `race` | 80 | Demographics (`race`) |
| `childs` | 42 | Demographics (`childs`) |
| `hispanic` | 39 | Demographics (`hispanic`) |
| `educ` | 34 | Demographics (`educ`) |
| `sex` | 30 | Demographics (`sex`) |
| `born` | 27 | Demographics (`born`) |
| `marital` | 15 | Demographics (`marital`) |
| `wrkstat` | 12 | Employment Status (`wrkstat`) |
| `degree` | 7 | Highest Degree (`degree`) |


## Imputation Log

The following median values were dynamically computed from the dataset and applied to fill missing feature values (excluding the target variable `satjob`):

| Column Name | Method | Imputed Value |
| :--- | :--- | :--- |
| `occ10` | Median | 4110.0 |
| `indus10` | Median | 7390.0 |
| `wrkstat` | Median | 2.0 |
| `wrkslf` | Median | 2.0 |
| `prestg10` | Median | 44.0 |
| `sei10` | Median | 41.1 |
| `realrinc` | Median | 16335.0 |
| `rincom16` | Median | 18.0 |
| `hrs1` | Median | 40.0 |
| `weekswrk` | Median | 40.0 |
| `age` | Median | 48.0 |
| `sex` | Median | 2.0 |
| `race` | Median | 1.0 |
| `hispanic` | Median | 1.0 |
| `born` | Median | 1.0 |
| `educ` | Median | 14.0 |
| `degree` | Median | 1.0 |
| `marital` | Median | 3.0 |
| `childs` | Median | 2.0 |
| `union1` | Median | 4.0 |
| `Achievement` | Median | 4.0 |
| `Independence` | Median | 4.335 |
| `Recognition` | Median | 3.335 |
| `Relationships` | Median | 4.67 |
| `Support` | Median | 4.33 |
| `Working Conditions` | Median | 3.83 |
| `job_zone` | Median | 3.0 |

* **Summary Stats:**
           realrinc         hrs1          age     weekswrk     prestg10
count   3986.000000  3986.000000  3986.000000  3986.000000  3986.000000
mean   21496.479865    39.605620    49.001254    30.456096    44.313096
std    19233.479153    10.089537    17.380320    22.700907    13.122598
min      181.500000     0.000000    18.000000     0.000000    16.000000
25%    16335.000000    40.000000    35.000000     0.000000    35.000000
50%    16335.000000    40.000000    48.000000    40.000000    44.000000
75%    19965.000000    40.000000    63.000000    52.000000    53.000000
max    97883.490870    89.000000    89.000000    52.000000    80.000000

Outlier Counts (using 1.5 * IQR rule):
realrinc: 1445 outliers (bounds: 10890.0 to 25410.0)
hrs1: 1295 outliers (bounds: 40.0 to 40.0)
age: 0 outliers (bounds: -7.0 to 105.0)
weekswrk: 0 outliers (bounds: -78.0 to 130.0)
prestg10: 0 outliers (bounds: 8.0 to 80.0)

* **Breakdown by Feature:**

    * Working Hours (hrs1) — 1,295 flags:
        Because most people report working a standard 40-hour week, the 25th, 50th, and 75th percentiles all landed right on 40.0. That squashed the IQR range down to zero, meaning anyone who worked even slightly more or less than 40 hours got incorrectly flagged as an outlier.

    * Income (realrinc) — 1,445 flags:
        Income data naturally clusters heavily around the median, which squeezed the IQR span and mislabeled normal, higher-earning respondents as statistical anomalies.

    * Other Metrics (age, weekswrk, prestg10) — 0 flags:
        These stayed entirely within normal, expected real-world limits with zero strange values flagged.

* **No Clipping or Removal:** 
  * The IQR rule breaks down when survey responses cluster tightly around norms (like a 40-hour work week). Because tree-based models handle skewed data naturally, we're keeping the raw values to avoid throwing out valid responses.



  ## Summary of Data Cleaning Phase

* **Feature Reduction:** Trimmed the raw 48-column dataset down to 29 core features by removing irrelevant administrative columns, structural identifiers, and sparse flags.
* **Missing Value Imputation:** Handled missing values using median imputation for numeric features and placeholder filling for categoricals, explicitly excluding the target variable (`satjob`) to prevent data leakage.
* **Outlier Diagnostics & Strategy:** Audited continuous features using descriptive statistics and IQR checks. Preserved raw values without clipping or dropping, as survey responses naturally cluster around social norms (like 40-hour work weeks) rather than following a smooth distribution.

## Final Dataset Output
* **File Name:** `gss2024_onet_cleaned.csv`
* **Dimensions:** 3,986 rows × 29 core features
* **Status:** Fully cleaned, missing values imputed, ready for feature engineering and exploratory data analysis.