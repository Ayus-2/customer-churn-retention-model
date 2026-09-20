"""Retention Campaign Planner: a Streamlit app that turns churn predictions into a call list."""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "call_list_data.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH, index_col="CustomerID")


def add_economics(df, call_cost, discount_pct, discount_months, success_rate, margin):
    """Add cost, value saved and expected profit (EV) for every customer."""
    out = df.copy()
    out["cost"] = call_cost + discount_pct * discount_months * out["Monthly Charges"]
    out["value_saved"] = margin * out["CLTV"]
    out["ev"] = out["churn_probability"] * success_rate * out["value_saved"] - out["cost"]
    return out


def pick_customers(df, budget):
    """Contact customers in order of expected profit until the budget runs out.
    Customers whose expected profit is not positive are never contacted."""
    ranked = df[df["ev"] > 0].sort_values("ev", ascending=False)
    ranked = ranked.assign(cumulative_cost=ranked["cost"].cumsum())
    return ranked[ranked["cumulative_cost"] <= budget]


def profit_by_threshold(df):
    """Expected profit if we contact everyone at or above each probability threshold."""
    thresholds = np.round(np.arange(0.0, 0.96, 0.01), 2)
    profit = [df.loc[df["churn_probability"] >= t, "ev"].sum() for t in thresholds]
    return pd.DataFrame({"threshold": thresholds, "expected_profit": profit})


def backtest(chosen, success_rate):
    """Profit using the customers' ACTUAL outcomes (possible because this is held-out data)."""
    spend = chosen["cost"].sum()
    gross = (chosen["churn_actual"] * success_rate * chosen["value_saved"]).sum()
    return spend, gross, gross - spend


def reasons_text(row):
    parts = [str(r) for r in (row["reason_1"], row["reason_2"], row["reason_3"])
             if isinstance(r, str) and r.strip()]
    return " • ".join(parts) if parts else "-"


def main():
    st.set_page_config(page_title="Retention Campaign Planner", layout="wide")
    st.title("Retention Campaign Planner")
    st.caption("Set a weekly budget and get a prioritised call list ranked by expected profit, "
               "not just churn risk. Data: 1,409 held-out telecom customers the model never saw in training.")

    df = load_data()

    st.sidebar.header("Weekly budget")
    budget = st.sidebar.number_input("Retention budget ($)", min_value=0, max_value=60000,
                                     value=9000, step=500)

    st.sidebar.header("Offer assumptions")
    st.sidebar.caption("These are assumptions, not measured facts. Change them to see how the plan responds.")
    success_rate = st.sidebar.slider("Offer success rate (%)", 5, 60, 25) / 100
    margin = st.sidebar.slider("Profit margin on lifetime value (%)", 10, 60, 30) / 100
    discount_pct = st.sidebar.slider("Discount offered (%)", 5, 40, 20) / 100
    discount_months = st.sidebar.slider("Discount length (months)", 1, 12, 6)
    call_cost = st.sidebar.slider("Cost per call ($)", 0, 20, 5)

    econ = add_economics(df, call_cost, discount_pct, discount_months, success_rate, margin)
    chosen = pick_customers(econ, budget)
    worthwhile = econ[econ["ev"] > 0]

    spend = chosen["cost"].sum()
    net = chosen["ev"].sum()
    gross = net + spend
    roi = net / spend if spend > 0 else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Customers to call", f"{len(chosen)}")
    c2.metric("Campaign spend", f"${spend:,.0f}")
    c3.metric("Expected value saved", f"${gross:,.0f}")
    c4.metric("Expected net profit", f"${net:,.0f}")
    c5.metric("Expected ROI", f"{roi:.0%}")

    st.info(f"With no budget limit, {len(worthwhile)} of {len(econ)} customers are worth contacting "
            f"(expected profit ${worthwhile['ev'].sum():,.0f}). Your budget covers {len(chosen)} of them.")

    if chosen.empty:
        st.warning("No customers have positive expected profit at this budget and these assumptions.")
        return

    left, right = st.columns(2)

    with left:
        st.subheader("Profit vs probability threshold")
        curve = profit_by_threshold(econ)
        best = curve.loc[curve["expected_profit"].idxmax()]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(curve["threshold"], curve["expected_profit"])
        ax.axvline(best["threshold"], color="green", linestyle="--",
                   label=f"Best threshold {best['threshold']:.2f}")
        ax.axhline(0, color="grey", linewidth=0.8)
        ax.set_xlabel("Contact customers with churn probability at or above")
        ax.set_ylabel("Expected profit ($)")
        ax.legend()
        st.pyplot(fig)
        st.caption(f"A single probability cut-off peaks at {best['threshold']:.2f} "
                   f"(expected profit ${best['expected_profit']:,.0f}). Ranking by each customer's own "
                   "expected profit does better, because it accounts for their value and offer cost.")

    with right:
        st.subheader("Profit vs campaign size")
        ranked_all = worthwhile.sort_values("ev", ascending=False)
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.plot(ranked_all["cost"].cumsum().values, ranked_all["ev"].cumsum().values)
        ax2.scatter([spend], [net], color="red", zorder=5, label="Your budget")
        ax2.set_xlabel("Cumulative campaign spend ($)")
        ax2.set_ylabel("Cumulative expected profit ($)")
        ax2.legend()
        st.pyplot(fig2)
        st.caption("Each extra dollar buys less profit than the last: the curve flattens as the list "
                   "moves to less valuable customers.")

    st.subheader("Prioritised call list")
    table = pd.DataFrame({
        "Rank": range(1, len(chosen) + 1),
        "Customer": chosen.index,
        "Churn probability (%)": (chosen["churn_probability"] * 100).round(1).values,
        "Expected profit ($)": chosen["ev"].round(0).values,
        "Monthly bill ($)": chosen["Monthly Charges"].round(0).values,
        "Value at stake ($)": chosen["value_saved"].round(0).values,
        "Why flagged": chosen.apply(reasons_text, axis=1).values,
    })
    st.dataframe(table, hide_index=True)
    st.download_button("Download call list (CSV)", table.to_csv(index=False),
                       file_name="call_list.csv", mime="text/csv")

    with st.expander("Backtest: how did this list really perform? (uses actual outcomes)"):
        b_spend, b_gross, b_net = backtest(chosen, success_rate)
        random_net = len(chosen) * ((econ["churn_actual"] * success_rate * econ["value_saved"]).mean()
                                    - econ["cost"].mean())
        st.write(f"**{chosen['churn_actual'].mean():.0%}** of the customers on this list actually churned, "
                 f"against **{econ['churn_actual'].mean():.0%}** across all customers.")
        st.write(f"Net profit using actual outcomes: **${b_net:,.0f}** on ${b_spend:,.0f} spent "
                 f"(ROI {b_net / b_spend:.0%}). A random list of the same size would earn about "
                 f"**${random_net:,.0f}**.")
        st.caption("This still assumes the offer success rate above. It checks who the model flagged, "
                   "not whether the offer really works, which needs an A/B test.")


if __name__ == "__main__":
    main()
