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

## Status
Phase 1 of 7 complete.
