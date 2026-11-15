# Logistic Regression — AJQ Progress Report

*Model development, evaluation, data quality, and error analysis*

*Research progress summary \| American Job Quality (AJQ) survey \| November 14, 2026*

## Executive summary

The logistic regression (LR) work progressed from a
demographic/employment baseline to a 36-question feature set
incorporating workplace quality, scheduling, career growth, and job
security. The strongest reported model on the original 67/33 split
achieved 76.74% test accuracy, compared with 62.74% for the baseline.
This is substantial progress, but below the project’s 82% target.

| **Primary model**           | **Test accuracy** | **ROC-AUC** | **F1** | **Incorrect / 6,066** |
|-----------------------------|-------------------|-------------|--------|-----------------------|
| Baseline (11 questions)     | 62.74%            | 0.6532      | 0.4562 | ~2,260                |
| Baseline + Job Quality (22) | 75.72%            | 0.8307      | 0.7069 | ~1,473                |
| All New Features (36)       | 76.74%            | 0.8447      | 0.7224 | 1,411                 |

*These are original LR notebook test results. Baseline and job-quality reference models used C=1; the expanded model used validation-selected C=0.01. The target is binary and the test decision threshold is 0.50.*

## 1 Dataset, target, and split

- **Source and size.** JFF_formatted_public_release_labels.csv contained
  18,429 survey records and 153 original columns. Filtering to valid Q4
  satisfaction ratings (0–10) left 18,381 respondents.
- **Target.** Q4 ratings 8–10 = 1 (“highly satisfied”); ratings 0–7 = 0
  (“not highly satisfied”). Class 0 should not be described as
  necessarily dissatisfied.
- **Distribution.** 10,736 respondents (58.4%) were class 0 and 7,645
  (41.6%) were class 1. A majority-class classifier would score about
  58.4% accuracy.
- **Evaluation.** Stratified 67% development / 33% test split,
  random_state=1234; 6,066 test respondents. Within the development set,
  9,236 fit and 3,079 validation respondents were used for feature-group
  selection.

## 2 Feature development

| **Feature group**   | **Original survey columns** | **Purpose**                                                                                                            |
|---------------------|-----------------------------|------------------------------------------------------------------------------------------------------------------------|
| Baseline            | 11                          | Hours, earnings, tenure, gender, employment type, organization size, days/week, marital status, education, age, region |
| + Job Quality      | 22 total                    | Q33A–Q33J workplace statements; Q55 insurance                                                                          |
| + Scheduling       | 29 total                    | Q23, Q24, Q25A–Q25D, Q27                                                                                               |
| + Growth           | 27 total                    | Q34, Q35A–Q35D                                                                                                         |
| + Security         | 24 total                    | Q36, Q41                                                                                                               |
| + All New Features | 36 total                    | Baseline + job quality + scheduling + growth + security                                                                |

## 3 Preprocessing and model selection

- **Target parsing.** Extracted the leading numeric value from labeled
  Q4 responses, filtered invalid ratings, and created a binary label.
- **Numeric features.** Q20 (hours), Q17 (days), and Q51 (age) were
  converted to numeric values, imputed using the training-set median,
  and standardized.
- **Categorical features.** Survey categories, including income and
  tenure brackets, were one-hot encoded. Unanswered categories were
  represented as “Missing”.
- **Regularization.** Compared multiple inverse regularization values C. 
  A five-fold stratified CV diagnostic on baseline + job quality reached 
  75.62% mean accuracy at C=0.001. This is separate from the expanded-model selection.
- **Selection.** The feature-group validation comparison selected all
  new features at C=0.01 by ROC-AUC (validation accuracy 76.78%; ROC-AUC
  0.8443; F1 0.7215).

## 4 Reported performance

| **Model**        | **Test accuracy** | **ROC-AUC** | **F1** | **Recall (class 1)** | **Log loss** |
|------------------|-------------------|-------------|--------|----------------------|--------------|
| Baseline         | 0.6274            | 0.6532      | 0.4562 | 0.3757               | 0.6432       |
| Job Quality      | 0.7572            | 0.8307      | 0.7069 | 0.7039               | 0.4974       |
| All New Features | 0.7674            | 0.8447      | 0.7224 | 0.7277               | 0.4793       |

Adding job-quality responses produced the largest gain (+12.98
percentage points over baseline). The scheduling, growth, and security
variables together added a further +1.02 points. Overall improvement
from baseline to all features was +14.00 percentage points.

## 5 Incorrect predictions and the satisfaction boundary

| **Actual class / predicted class** | **Predicted 0**      | **Predicted 1**      |
|------------------------------------|----------------------|----------------------|
| Actual 0 (Q4 = 0–7)                | 2,819 true negatives | 724 false positives  |
| Actual 1 (Q4 = 8–10)               | 687 false negatives  | 1,836 true positives |

The expanded model correctly classified 4,655 of 6,066 test respondents
and misclassified 1,411. Its 724 false positives predicted high
satisfaction for Q4=0–7; its 687 false negatives missed respondents with
Q4=8–10.

| **Actual Q4 rating** | **Test respondents** | **Incorrect** | **Error rate** |
|----------------------|----------------------|---------------|----------------|
| 6                    | 759                  | 126           | 16.6%          |
| 7                    | 1,392                | 494           | 35.5%          |
| 8                    | 1,376                | 534           | 38.8%          |
| 9                    | 727                  | 105           | 14.4%          |
| 10                   | 420                  | 48            | 11.4%          |

Ratings 7 and 8 account for 1,028 / 1,411 errors (72.9%). Among 
respondents with Q4=8, 534 of 1,376 (38.8%) were classified as class 0;
373 of those errors persisted across all three LR feature sets. Across 
all Q4 ratings, 727 errors were shared by the baseline, job-quality, 
and expanded models.

## 6 Data quality and analytical challenges

### Missingness and response categories

| **Feature** | **Missing responses** | **Missing rate** |
|-------------|-----------------------|------------------|
| Q34         | 3,561                 | 19.37%           |
| Q35B        | 3,103                 | 16.88%           |
| Q35D        | 2,535                 | 13.79%           |
| Q33H        | 2,521                 | 13.72%           |
| Q35C        | 2,348                 | 12.77%           |
| Q35A        | 2,070                 | 11.26%           |

Career-development and advancement questions had the highest
missing-response rates. The original cleaning maps “No response,” “Not
sure,” and “Not applicable” to missing values. That simplifies
preprocessing but may discard meaningful differences: “Not applicable”
can reflect a survey skip or genuinely inapplicable employment
conditions.

### Experiments that did not materially improve accuracy

- **Ordinal encoding.** Encoding agreement-scale responses in order
  (1–5) and imputing missing values with the mean or median produced no
  consistent accuracy gain over one-hot encoding.
- **Five-fold preprocessing comparison.** At C=0.001, original one-hot
  averaged 76.43% CV accuracy (AUC 0.8403); ordinal + mean averaged
  76.09% (AUC 0.8390). At C=0.01, ordinal + mean averaged 76.35% (AUC
  0.8398).
- **Not-applicable preservation.** Keeping “Not applicable” separate was
  conceptually sensible, but one-hot with that distinction averaged
  76.40% CV accuracy at C=0.001—essentially tied with the original
  approach.
- **Class weighting.** On validation, class_weight=balanced changed
  accuracy from 76.78% to 76.45%, but increased F1 from 0.7215 to 0.7380
  and balanced accuracy from 0.7613 to 0.7692. It changed the
  precision–recall tradeoff rather than solving the accuracy plateau.

### Subgroup diagnostic

Positive-class recall varied by region (Midwest 0.673; Northeast 0.694;
South 0.740; West 0.787). Female and male accuracy was 0.753 and 0.779,
respectively. These differences warrant checking prevalence, subgroup
sizes, and uncertainty; they do not by themselves establish
discrimination or causation.
