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

## Status
Phase 2 of 7 complete.
