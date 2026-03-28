import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def calculate_mortgage(loan_amount: float, annual_interest_rate: float, years: int) -> dict:
    monthly_interest_rate = annual_interest_rate / 100 / 12
    number_of_payments = years * 12

    if monthly_interest_rate == 0:
        exact_monthly_payment = loan_amount / number_of_payments
    else:
        exact_monthly_payment = loan_amount * (
            monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments
        ) / (
            (1 + monthly_interest_rate) ** number_of_payments - 1
        )

    monthly_payment = math.ceil(exact_monthly_payment * 100) / 100

    balance = loan_amount
    yearly_balances = []
    yearly_interest_paid = []
    yearly_principal_paid = []

    current_year_interest = 0.0
    current_year_principal = 0.0
    total_paid = 0.0

    for month in range(1, number_of_payments + 1):
        interest = balance * monthly_interest_rate
        principal = monthly_payment - interest

        if principal > balance:
            principal = balance
            monthly_payment_actual = interest + principal
        else:
            monthly_payment_actual = monthly_payment

        balance -= principal
        total_paid += monthly_payment_actual

        current_year_interest += interest
        current_year_principal += principal

        if abs(balance) < 1e-8:
            balance = 0.0

        if month % 12 == 0:
            yearly_balances.append(round(balance, 2))
            yearly_interest_paid.append(round(current_year_interest, 2))
            yearly_principal_paid.append(round(current_year_principal, 2))
            current_year_interest = 0.0
            current_year_principal = 0.0

    total_interest = total_paid - loan_amount

    years_list = list(range(1, years + 1))

    yearly_df = pd.DataFrame({
        "Year": years_list,
        "Remaining Balance (€)": yearly_balances,
        "Interest Paid (€)": yearly_interest_paid,
        "Principal Repaid (€)": yearly_principal_paid,
    })

    return {
        "monthly_payment": round(monthly_payment, 2),
        "exact_monthly_payment": exact_monthly_payment,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "yearly_balances": yearly_balances,
        "yearly_interest_paid": yearly_interest_paid,
        "yearly_principal_paid": yearly_principal_paid,
        "yearly_df": yearly_df,
    }


def plot_balance_interactive(yearly_df: pd.DataFrame):
    fig = px.line(
        yearly_df,
        x="Year",
        y="Remaining Balance (€)",
        markers=True,
        title="Remaining Mortgage Balance by Year",
    )

    fig.update_traces(
        hovertemplate=(
            "Year: %{x}<br>"
            "Remaining Balance: €%{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Remaining Balance (€)",
        hovermode="x unified",
    )

    return fig


def plot_interest_principal_interactive(yearly_df: pd.DataFrame):
    fig = go.Figure()

    fig.add_bar(
        x=yearly_df["Year"],
        y=yearly_df["Interest Paid (€)"],
        name="Interest Paid (€)",
        hovertemplate=(
            "Year: %{x}<br>"
            "Interest Paid: €%{y:,.2f}"
            "<extra></extra>"
        ),
    )

    fig.add_bar(
        x=yearly_df["Year"],
        y=yearly_df["Principal Repaid (€)"],
        name="Principal Repaid (€)",
        hovertemplate=(
            "Year: %{x}<br>"
            "Principal Repaid: €%{y:,.2f}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title="Yearly Interest and Principal",
        xaxis_title="Year",
        yaxis_title="Amount (€)",
        barmode="group",
    )

    return fig


st.title("Mortgage Calculator")

loan_amount = st.number_input("Loan amount (€)", min_value=0.0, value=400000.0, step=1000.0)
annual_interest_rate = st.number_input("Annual interest rate (%)", min_value=0.0, value=4.0, step=0.1)
years = st.number_input("Years", min_value=1, value=30, step=1)

result = calculate_mortgage(
    loan_amount=loan_amount,
    annual_interest_rate=annual_interest_rate,
    years=years,
)

st.subheader("Summary")
st.write(f"Monthly payment: €{result['monthly_payment']:,.2f}")
st.write(f"Exact monthly payment: €{result['exact_monthly_payment']:,.6f}")
st.write(f"Total paid: €{result['total_paid']:,.2f}")
st.write(f"Total interest: €{result['total_interest']:,.2f}")

st.subheader("Yearly Data")
st.dataframe(result["yearly_df"], use_container_width=True)

st.subheader("Remaining Balance by Year")
balance_fig = plot_balance_interactive(result["yearly_df"])
st.plotly_chart(balance_fig, use_container_width=True)

st.subheader("Interest vs Principal by Year")
interest_principal_fig = plot_interest_principal_interactive(result["yearly_df"])
st.plotly_chart(interest_principal_fig, use_container_width=True)