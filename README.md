# Customer Churn Prediction and Retention Revenue Model

## Business problem
Acquiring a new customer costs more than keeping one. A retention team can only
contact a limited number of customers each week, so the goal is not just to
predict churn, but to decide which customers to contact and whether the
campaign returns more than it costs.

## Definitions
- **Churn:** a customer is counted as churned if they cancelled their service
  (Churn Value = 1). Inactivity-based churn cannot be measured because the
  dataset has no usage data.
- **Prediction window:** the dataset is a snapshot, so churn is treated as
  leaving within roughly the next 30 days. This is a documented assumption.
- **Base rate:** 26.54% of customers churned (1,869 of 7,043).
- **Success criterion:** campaign profit under a limited budget, not accuracy.

## Why accuracy is not used
A model that predicts nobody churns is 73.46% accurate but catches 0 of the
1,869 churners. Models are judged on recall, precision and profit instead.

## Data leakage: columns excluded from the model
| Column | Reason |
|---|---|
| Churn Reason | Only filled in after a customer has left |
| Churn Score | Output of another churn model |
| Churn Label / Churn Value | The target itself |
| CLTV | Kept for the profit calculation, not used to predict |

## Data cleaning
`Total Charges` was blank for 11 customers with tenure 0 (not billed yet).
These were set to 0 instead of being dropped, so new customers stay in the sample.

## Key findings from exploratory analysis
- **Contract type is the strongest signal** (Cramér's V = 0.41): churn is 42.7%
  for month-to-month, 11.3% for one-year and 2.8% for two-year contracts.
- **Early-tenure cliff:** 42% of all churners leave within the first 6 months
  (churn is 62% in month 1, falling to under 2% at month 72).
- **Danger zone:** month-to-month customers paying by electronic check are 26%
  of customers but 53% of all churners (53.7% churn rate).
- **Protection add-ons matter:** among internet customers, churn falls from
  56.7% with no protection add-ons to 5.3% with all four.
- **Fiber optic customers churn at 41.9%** versus 19.0% for DSL. Association,
  not proven cause.
- **Gender and phone service show no significant link to churn.**
- All tests were run with Bonferroni correction (19 tests, threshold 0.0026).


## Feature engineering
- **28 model features** built from the cleaned data (`data/processed/telco_features.csv`).
- **Engineered:** tenure buckets (to capture the early-churn cliff), protection
  add-on count, and absolute bill change (current bill vs lifetime average).
- **Tested and dropped:** average monthly revenue (r = 0.996 with monthly charges),
  monthly-to-total ratio (r = 0.999 with 1/tenure) and signed bill change (r = 0.002).
- **Excluded:** Gender (no significant link), Phone Service (redundant with
  Multiple Lines), and location fields.
- **Limitation:** the dataset has no usage history, so usage-trend features
  could not be built.
- **Fairness note:** Senior Citizen is kept because it shows a real signal, but
  a real deployment should review whether age can be used to target offers.
- Scaling and any resampling happen inside the model pipeline, never before
  the train/test split, to avoid leakage.


## Modelling
- **Split:** 80/20 stratified (churn rate 26.5% in both). Models compared with
  5-fold cross-validation on the training set only; test set used once.
- **Imbalance:** handled with class weights, not SMOTE.
- **Results (5-fold CV):**

| Model | ROC-AUC | PR-AUC | Recall | Precision |
|---|---|---|---|---|
| Logistic Regression | 0.861 | 0.683 | 0.812 | 0.538 |
| Random Forest | 0.858 | 0.675 | 0.736 | 0.576 |

  (Baseline "predict nobody": PR-AUC 0.265.)
- **Finding:** complex models did not beat a well-prepared logistic regression,
  so the simpler, explainable model was chosen.
- **Feature testing:** `Abs Charge Change` was dropped after an ablation test
  showed no gain. `Protection Count` was excluded from the logistic model
  because it is an exact sum of four other features.
- **Calibration:** class weights inflated probabilities (mean 0.41 vs actual
  0.27). Platt scaling fixed this (Brier 0.1615 to 0.1338).
- **Test set (calibrated):** ROC-AUC 0.853, PR-AUC 0.662. Contacting the top
  10% of customers by risk reaches a group where 78% actually churn.

## Economics layer
Expected value per customer = P(churn) × offer success rate × value saved − offer cost.

**Assumptions (not measured from data):** $5 call + 20% discount for 6 months;
25% offer success rate (46% of churners cite price/offer-related reasons);
value saved = 30% of CLTV (CLTV treated as revenue).

**Results on 1,409 held-out customers (100-customer budget):**
| Ranking | Net profit | ROI |
|---|---|---|
| By churn probability | $14,485 | 144.5% |
| **By expected value** | **$18,412** | **203.4%** |
| Random | -$58 | -0.7% |

- Only 41% of customers have positive expected value; contacting everyone loses money.
- Profit-optimal threshold is 0.23; the F1-optimal threshold (0.34) leaves ~$2,800
  on the table and the default 0.5 leaves ~$8,000.
- A per-customer EV > 0 rule beats any single global threshold ($41,498 vs $36,846).
- Break-even offer success rate: 8.2% for the EV-ranked top 100.
- Sensitivity analysis across success rates (10-40%) and margins (20-40%) included.

**Limitations:** the success rate is an assumption and should be measured with an
A/B test (contacted group vs holdout). The model predicts who will churn, not who
will respond to an offer (uplift modelling would address this). CLTV is a
pre-computed field with undocumented methodology.



  
## Status
Phase 5 of 7 complete.
