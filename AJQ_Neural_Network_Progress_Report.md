# Neural Network — AJQ Progress Report

*Feature expansion, optimizer tuning, benchmark comparison, and limitations*

*Research progress summary \| American Job Quality (AJQ) survey \| November 14, 2026*

## Executive summary

The neural network progressed from an initial AJQ baseline/job-quality
comparison to an expanded experiment using the same six AJQ feature
groups as logistic regression. The original 64→32→16 network was
retained as the starting architecture; SGD and Adam were compared,
followed by a small architecture/dropout sweep. The best exploratory
validation accuracy was 77.06% (all features, Adam), but the selected
network reached 75.95% on the shared test respondents.

| **Key outcome**                | **Result** | **Interpretation**                  |
|--------------------------------|------------|-------------------------------------|
| Best expanded NN validation    | 77.06%     | All new features + Adam, 64–32–16   |
| Selected NN test accuracy      | 75.95%     | Shared 6,066-person test set        |
| Validation-selected LR test    | 76.26%     | Same expanded-NN benchmark pipeline |
| All-features LR reference test | 77.00%     | Same benchmark pipeline; C=0.01     |

*Validation scores were used to choose neural network settings; test results were reported after refitting. Neural-network numbers may vary with software backend, random seed, and numerical implementation.*

## 1 Dataset and prediction task

- **Dataset.** American Job Quality survey (AJQ), 18,429 raw records;
  18,381 respondents retained with valid Q4 ratings.
- **Target.** Class 1 = Q4 rating 8–10 (highly satisfied); class 0 = Q4
  rating 0–7 (not highly satisfied). The positive class represents
  approximately 41.6% of valid respondents.
- **Evaluation.** Stratified 67% development / 33% test split with
  random_state=1234. The expanded-NN experiment used 80% of development
  for fitting and 20% for validation; the shared test set contained
  6,066 respondents.
- **Goal.** Compare neural networks with a simpler LR baseline and work
  toward 82% accuracy without selecting models on the test labels.

## 2 Initial neural network configuration

- **Architecture.** Keras Sequential network with three ReLU hidden
  layers of 64, 32, and 16 neurons and a single sigmoid output for
  binary probabilities.
- **Optimization.** Original lab-style SGD with learning rate 0.1,
  binary cross-entropy, batch training, up to 100 epochs, and early
  stopping based on validation loss.
- **Preprocessing.** Q20, Q17, and Q51 were numeric with training-only
  median imputation and scaling; categorical survey responses were
  one-hot encoded and missing values treated as a “Missing” category.
- **Modeling note.** The architecture was a practical starting point
  from prior coursework, not a proven optimal network for AJQ.

## 3 Original AJQ and O\*NET experiments

Before expanding the AJQ survey features, the initial notebook compared
the baseline, job-quality variables, occupation controls, and O\*NET
occupation-level work values. Results below are test metrics from the
original NeuralNetwork.ipynb; they should not be mixed with later
validation scores.

| **Original feature set** | **NN accuracy** | **NN ROC-AUC** | **NN F1** |
|--------------------------|-----------------|----------------|-----------|
| AJQ Baseline             | 62.38%          | 0.6452         | 0.4626    |
| AJQ Job Quality          | 75.19%          | 0.8281         | 0.7075    |
| Baseline + O\*NET        | 62.38%          | 0.6424         | 0.4853    |
| AJQ + O\*NET Combined    | 74.91%          | 0.8277         | 0.7053    |
| Occupation Control (Q6)  | 75.40%          | 0.8287         | 0.7106    |

The strongest original NN accuracy came from adding the occupation
control (Q6), but the gain over AJQ job quality was small (75.40% versus
75.19%). Adding O\*NET work-value averages did not improve accuracy over
AJQ job quality alone. In the same original notebook, the
occupation-control LR reached 75.70% accuracy, ROC-AUC 0.8294, and F1
0.7089.

### O\*NET integration limitations

- The saved AJQ–O\*NET merge retained all 18,381 AJQ respondents;
  occupation-profile coverage was reported as 99.38%.
- O\*NET work-value averages were mapped through occupational categories
  rather than measured as individual workers’ preferences. They are not
  a direct person–job-fit score.
- Occupation mapping and aggregation can smooth over within-occupation
  differences, limiting the extra predictive value of the merged
  variables.

| **AJQ feature group**       | **SGD validation accuracy** | **Adam validation accuracy** |
|-----------------------------|-----------------------------|------------------------------|
| Baseline (11 features)      | 60.37%                      | 60.94%                       |
| Baseline + Job Quality (22) | 75.56%                      | 76.17%                       |
| + Scheduling (29)          | 76.65%                      | 76.65%                       |
| + Growth (27)              | 75.56%                      | 75.68%                       |
| + Security (24)            | 76.29%                      | 76.37%                       |
| + All New Features (36)    | 76.78%                      | 77.06%                       |

*Exploratory validation run recorded in NeuralNetwork_expanded_feature_comparison.ipynb and nn_feature_experiment_observed_results.csv. The run used Keras 3 with the PyTorch backend; TensorFlow may produce slightly different values.*

Job-quality variables again produced the major accuracy gain. Adding
scheduling, growth, and security together raised Adam validation
accuracy from 76.17% to 77.06% (+0.89 percentage points). Adam slightly
outperformed SGD in the full-feature comparison.

## 4 Hyperparameter and architecture investigation

- **Optimizer comparison.** SGD at 0.1 versus Adam at 0.001; Adam was
  selected on the expanded validation results.
- **Architecture sweep.** Compared the original 64–32–16 network, a
  smaller 32–16 network, a larger 128–64–32 network, and 64–32–16 with
  0.2 dropout.
- **Selection outcome.** The original 64–32–16 architecture with Adam
  and no dropout remained the best reported validation-accuracy
  configuration.
- **Training safeguards.** Early stopping monitored validation loss
  (patience 8, best weights restored); the selected epoch count was used
  when refitting on the full development set. Probability threshold
  remained 0.50.

## 5 Shared test-set comparison with logistic regression

| **Model in expanded experiment** | **Test accuracy** | **Selection / feature notes**  |
|----------------------------------|-------------------|--------------------------------|
| Neural network                   | 75.95%            | All features; Adam; 64–32–16   |
| Validation-selected LR           | 76.26%            | Job quality + security; C=0.01 |
| LR all-features reference        | 77.00%            | All 36 AJQ features; C=0.01    |

The selected NN performed 0.31 percentage points below the
validation-selected LR and 1.05 points below the all-features LR
reference on this shared test set. Differences are modest and should be
checked across multiple random seeds or cross-validation folds before
making a definitive algorithm choice.

### Why the LR accuracy appears as 76.74% elsewhere

The original logistic regression notebook reported 76.74% test accuracy
for its all-feature model. The expanded NN comparison notebook reported
77.00% for an all-feature LR reference because it uses a different
preprocessing implementation (including how encoded dummy variables are
scaled). The two figures are not contradictory; they are results from
different modeling pipelines. The fairest algorithm comparison is the NN
and LR benchmark run under the same preprocessing and respondent split.

## 6 Errors, challenges, and noteworthy findings

- **Boundary ambiguity.** As in LR, respondents with Q4 ratings near 7
  and 8 can have similar workplace characteristics even though the
  binary labels differ. The expanded NN notebook includes
  error-rate-by-rating plots and a direct comparison of where NN and LR
  predictions disagree.
- **No clear NN advantage.** A more flexible nonlinear model did not
  deliver a consistent accuracy improvement over LR. This may reflect
  limited additional nonlinear signal, the available feature
  representation, or tuning/data limitations—not proof that nonlinear
  relationships are absent.
- **Overfitting and training variance.** Neural networks are sensitive
  to optimizer, architecture, initialization, early stopping, and
  backend. Training/validation loss curves were included to diagnose
  overfitting; a single run is insufficient for strong conclusions.
- **Missingness and survey semantics.** Several growth-related survey
  questions have high missing-response rates. Mapping “Not applicable,”
  “Not sure,” and “No response” together may obscure skip logic;
  mean-imputation/ordinal experiments in LR did not show clear
  improvement.
- **Class definition.** Class 0 includes respondents with Q4=7, not just
  workers with low satisfaction. Accuracy is sensitive to this threshold
  and should not be artificially raised by redefining the task.
- **Test reuse.** The same 6,066-person test split has been examined
  across project iterations, so final generalization claims need
  independent confirmation.

## 7 Recommended model decision and next steps

Current recommendation: use logistic regression as the primary
interpretable benchmark and keep the neural network as a complementary
nonlinear comparison. Both models achieve broadly similar performance,
but LR is simpler to explain through feature coefficients and currently
matches or slightly exceeds NN accuracy on the shared test data.

- Repeat the NN versus LR comparison with identical feature
  preprocessing across several seeds or stratified folds, reporting mean
  and standard deviation of accuracy, ROC-AUC, F1, and log loss.
- Examine paired predictions: respondents LR gets wrong but NN gets
  right, and vice versa. This may identify nonlinear patterns even when
  aggregate accuracy is similar.
- Use training-only validation to test targeted feature interactions and
  person–job preference gaps (for example, actual versus preferred
  remote days).
- Check class-1 recall and probability calibration, not just accuracy;
  inspect training/validation curves for underfitting or overfitting.
- Reserve a fresh untouched holdout or use nested/repeated
  cross-validation for a more defensible final model comparison and
  assessment against the 82% target.

## 8 Progress milestones

| **Stage**                         | **Outcome**                                                 |
|-----------------------------------|-------------------------------------------------------------|
| Initial AJQ baseline              | 62.38% NN test accuracy                                     |
| Add job quality                   | 75.19% NN test accuracy                                     |
| O\*NET and occupation experiments | No substantial gain from O\*NET averages; Q6 control 75.40% |
| Expanded AJQ groups + Adam        | 77.06% best exploratory validation accuracy                 |
| Shared final test benchmark       | 75.95% NN versus 76.26% selected LR                         |
