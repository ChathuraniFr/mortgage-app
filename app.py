import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


TRANSLATIONS = {
    "English": {
        "app_title": "Mortgage Calculator",
        "language": "Language",
        "calculation_type": "Calculation type",
        "monthly_payment_mode": "Monthly payment",
        "payoff_time_mode": "Payoff time",
        "loan_amount": "Loan amount (€)",
        "interest_rate": "Interest rate (%)",
        "years": "Years",
        "monthly_payment": "Monthly payment (€)",
        "calculate": "Calculate",
        "show_selector": "Show",
        "summary": "Summary",
        "remaining_balance_graph": "Remaining balance graph",
        "total_mortgage_cost": "Total mortgage cost",
        "mortgage_cost_by_year": "Mortgage cost by year",
        "simple_explanation_table": "Simple explanation table",
        "full_yearly_data_table": "Full yearly data table",
        "enter_values_info": "Enter your values below and click Calculate.",
        "monthly_payment_metric": "Monthly Payment",
        "total_paid_metric": "Total Paid",
        "total_interest_metric": "Total Interest",
        "time_needed_metric": "Time Needed",
        "exact_monthly_payment_caption": "Exact monthly payment before rounding: €{value:,.6f}",
        "payoff_caption": "At €{payment:,.2f} per month, the mortgage is repaid in {years} years and {months} months.",
        "time_needed_format_full": "{years} years, {months} months",
        "time_needed_format_years": "{years} years",
        "time_needed_format_months": "{months} months",
        "time_needed_format_zero": "0 months",
        "principal": "Principal",
        "interest": "Interest",
        "total": "Total",
        "year": "Year",
        "remaining_balance_eur": "Remaining Balance (€)",
        "interest_paid_eur": "Interest Paid (€)",
        "principal_repaid_eur": "Principal Repaid (€)",
        "total_paid_eur": "Total Paid (€)",
        "interest_share_pct": "Interest Share (%)",
        "principal_share_pct": "Principal Share (%)",
        "start": "Start",
        "middle": "Middle",
        "end": "End",
        "what_this_means": "What this means",
        "mostly_interest": "Mostly interest",
        "mostly_principal": "Mostly principal",
        "balanced": "Balanced",
        "loan_amount_error": "Loan amount must be greater than 0.",
        "interest_rate_error": "Interest rate cannot be negative.",
        "years_error": "Years must be greater than 0.",
        "monthly_payment_error": "Monthly payment must be greater than 0.",
        "invalid_numeric_error": "Please enter valid numeric values in all required fields.",
        "payment_too_low_error": "The monthly payment is too low. It does not cover the monthly interest, so the loan would never be repaid.",
        "minimum_payment_needed": "The minimum monthly payment must be greater than €{value:,.2f}.",
        "minimum_payment_hint": "To reduce the loan balance, you must pay more than the monthly interest amount of €{value:,.2f}.",
        "minimum_payment_live_hint": "Minimum useful monthly payment: more than €{value:,.2f}",
        "placeholder_loan": "e.g. 400000",
        "placeholder_rate": "e.g. 4",
        "placeholder_years": "e.g. 30",
        "placeholder_payment": "e.g. 1909.67",
        "hover_remaining_balance": "Year: %{x}<br>Remaining Balance: €%{y:,.2f}<extra></extra>",
        "hover_principal_bar": "Year: %{x}<br>Principal: €%{y:,.2f}<extra></extra>",
        "hover_interest_bar": "Year: %{x}<br>Interest: €%{y:,.2f}<extra></extra>",
        "pie_texttemplate": "%{label}<br>€%{value:,.0f}<br>(%{percent})",
        "pie_hovertemplate": "%{label}<br>€%{value:,.2f}<br>%{percent}<extra></extra>",
        "simple_cols": {
            "stage": "Stage",
            "year": "Year",
            "remaining_balance": "Remaining Balance (€)",
            "interest_paid": "Interest Paid (€)",
            "principal_repaid": "Principal Repaid (€)",
            "total_paid": "Total Paid (€)",
            "interest_share": "Interest Share (%)",
            "principal_share": "Principal Share (%)",
            "meaning": "What this means",
        },
        "required_field_error": "Please fill in the field: {field}",
        "invalid_number_error": "Please enter a valid number in the field: {field}",
        "invalid_integer_error": "Please enter a whole number in the field: {field}",
        "input_section": "Inputs",
        "results_section": "Results",
    },
    "Deutsch": {
        "app_title": "Kreditrechner",
        "language": "Sprache",
        "calculation_type": "Berechnungsart",
        "monthly_payment_mode": "Monatliche Rate",
        "payoff_time_mode": "Laufzeit",
        "loan_amount": "Darlehensbetrag (€)",
        "interest_rate": "Zinssatz (%)",
        "years": "Jahre",
        "monthly_payment": "Monatliche Rate (€)",
        "calculate": "Berechnen",
        "show_selector": "Anzeigen",
        "summary": "Übersicht",
        "remaining_balance_graph": "Restschuldgrafik",
        "total_mortgage_cost": "Gesamtkosten der Hypothek",
        "mortgage_cost_by_year": "Hypothekenkosten pro Jahr",
        "simple_explanation_table": "Einfache Erklärungstabelle",
        "full_yearly_data_table": "Vollständige Jahrestabelle",
        "enter_values_info": "Gib unten deine Werte ein und klicke auf „Berechnen“.",
        "monthly_payment_metric": "Monatliche Rate",
        "total_paid_metric": "Gesamt gezahlt",
        "total_interest_metric": "Gesamtzinsen",
        "time_needed_metric": "Benötigte Zeit",
        "exact_monthly_payment_caption": "Exakte monatliche Rate vor Rundung: €{value:,.6f}",
        "payoff_caption": "Bei €{payment:,.2f} pro Monat ist die Hypothek nach {years} Jahren und {months} Monaten zurückgezahlt.",
        "time_needed_format_full": "{years} Jahre, {months} Monate",
        "time_needed_format_years": "{years} Jahre",
        "time_needed_format_months": "{months} Monate",
        "time_needed_format_zero": "0 Monate",
        "principal": "Tilgung",
        "interest": "Zinsen",
        "total": "Gesamt",
        "year": "Jahr",
        "remaining_balance_eur": "Restschuld (€)",
        "interest_paid_eur": "Gezahlte Zinsen (€)",
        "principal_repaid_eur": "Getilgt (€)",
        "total_paid_eur": "Gesamt gezahlt (€)",
        "interest_share_pct": "Zinsanteil (%)",
        "principal_share_pct": "Tilgungsanteil (%)",
        "start": "Anfang",
        "middle": "Mitte",
        "end": "Ende",
        "what_this_means": "Bedeutung",
        "mostly_interest": "Überwiegend Zinsen",
        "mostly_principal": "Überwiegend Tilgung",
        "balanced": "Ausgeglichen",
        "loan_amount_error": "Der Darlehensbetrag muss größer als 0 sein.",
        "interest_rate_error": "Der Zinssatz darf nicht negativ sein.",
        "years_error": "Die Jahre müssen größer als 0 sein.",
        "monthly_payment_error": "Die monatliche Rate muss größer als 0 sein.",
        "invalid_numeric_error": "Bitte gib in allen erforderlichen Feldern gültige Zahlen ein.",
        "payment_too_low_error": "Die monatliche Rate ist zu niedrig. Sie deckt nicht einmal die monatlichen Zinsen, daher würde das Darlehen nie vollständig zurückgezahlt.",
        "minimum_payment_needed": "Die minimale monatliche Rate muss größer als €{value:,.2f} sein.",
        "minimum_payment_hint": "Damit sich die Restschuld verringert, muss die monatliche Rate höher sein als die monatlichen Zinsen von €{value:,.2f}.",
        "minimum_payment_live_hint": "Sinnvolle minimale Monatsrate: mehr als €{value:,.2f}",
        "placeholder_loan": "z. B. 400000",
        "placeholder_rate": "z. B. 4",
        "placeholder_years": "z. B. 30",
        "placeholder_payment": "z. B. 1909,67",
        "hover_remaining_balance": "Jahr: %{x}<br>Restschuld: €%{y:,.2f}<extra></extra>",
        "hover_principal_bar": "Jahr: %{x}<br>Tilgung: €%{y:,.2f}<extra></extra>",
        "hover_interest_bar": "Jahr: %{x}<br>Zinsen: €%{y:,.2f}<extra></extra>",
        "pie_texttemplate": "%{label}<br>€%{value:,.0f}<br>(%{percent})",
        "pie_hovertemplate": "%{label}<br>€%{value:,.2f}<br>%{percent}<extra></extra>",
        "simple_cols": {
            "stage": "Phase",
            "year": "Jahr",
            "remaining_balance": "Restschuld (€)",
            "interest_paid": "Gezahlte Zinsen (€)",
            "principal_repaid": "Getilgt (€)",
            "total_paid": "Gesamt gezahlt (€)",
            "interest_share": "Zinsanteil (%)",
            "principal_share": "Tilgungsanteil (%)",
            "meaning": "Bedeutung",
        },
        "required_field_error": "Bitte fülle das Feld aus: {field}",
        "invalid_number_error": "Bitte gib eine gültige Zahl ein im Feld: {field}",
        "invalid_integer_error": "Bitte gib eine ganze Zahl ein im Feld: {field}",
        "input_section": "Eingaben",
        "results_section": "Ergebnisse",
    },
}


def parse_number(value: str) -> float:
    value = value.strip().replace(" ", "").replace(",", ".")
    return float(value)


def validate_required_text(value: str, field_label: str, t: dict) -> str | None:
    if value is None or value.strip() == "":
        return t["required_field_error"].format(field=field_label)
    return None


def validate_float_field(value: str, field_label: str, t: dict) -> tuple[float | None, str | None]:
    missing_error = validate_required_text(value, field_label, t)
    if missing_error:
        return None, missing_error

    try:
        return parse_number(value), None
    except ValueError:
        return None, t["invalid_number_error"].format(field=field_label)


def validate_int_field(value: str, field_label: str, t: dict) -> tuple[int | None, str | None]:
    missing_error = validate_required_text(value, field_label, t)
    if missing_error:
        return None, missing_error

    try:
        parsed = parse_number(value)
        if not float(parsed).is_integer():
            return None, t["invalid_integer_error"].format(field=field_label)
        return int(parsed), None
    except ValueError:
        return None, t["invalid_integer_error"].format(field=field_label)


def format_time_duration(years: int, months: int, t: dict) -> str:
    if years > 0 and months > 0:
        return t["time_needed_format_full"].format(years=years, months=months)
    if years > 0:
        return t["time_needed_format_years"].format(years=years)
    if months > 0:
        return t["time_needed_format_months"].format(months=months)
    return t["time_needed_format_zero"]


def get_minimum_monthly_payment(loan_amount: float, annual_interest_rate: float) -> float:
    monthly_interest_rate = annual_interest_rate / 100 / 12
    return loan_amount * monthly_interest_rate


def calculate_mortgage_by_term(
    loan_amount: float,
    annual_interest_rate: float,
    years: int,
    t: dict,
) -> dict:
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

    return build_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        exact_monthly_payment=exact_monthly_payment,
        calculation_type=t["monthly_payment_mode"],
        t=t,
    )


def calculate_mortgage_by_payment(
    loan_amount: float,
    annual_interest_rate: float,
    monthly_payment: float,
    t: dict,
) -> dict:
    minimum_payment = get_minimum_monthly_payment(loan_amount, annual_interest_rate)

    if annual_interest_rate > 0 and monthly_payment <= minimum_payment:
        minimum_payment_display = math.ceil(minimum_payment * 100) / 100
        raise ValueError(
            f"{t['payment_too_low_error']} "
            f"{t['minimum_payment_needed'].format(value=minimum_payment_display)} "
            f"{t['minimum_payment_hint'].format(value=minimum_payment_display)}"
        )

    return build_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        exact_monthly_payment=monthly_payment,
        calculation_type=t["payoff_time_mode"],
        t=t,
    )


def build_amortization_schedule(
    loan_amount: float,
    annual_interest_rate: float,
    monthly_payment: float,
    exact_monthly_payment: float,
    calculation_type: str,
    t: dict,
) -> dict:
    monthly_interest_rate = annual_interest_rate / 100 / 12

    balance = loan_amount
    total_paid = 0.0
    total_interest = 0.0

    yearly_balances = []
    yearly_interest_paid = []
    yearly_principal_paid = []
    yearly_total_paid = []

    current_year_interest = 0.0
    current_year_principal = 0.0
    current_year_total_paid = 0.0
    payment_number = 0

    while balance > 1e-8:
        payment_number += 1

        interest = balance * monthly_interest_rate
        principal = monthly_payment - interest

        if principal > balance:
            principal = balance
            monthly_payment_actual = interest + principal
        else:
            monthly_payment_actual = monthly_payment

        balance -= principal
        total_paid += monthly_payment_actual
        total_interest += interest

        current_year_interest += interest
        current_year_principal += principal
        current_year_total_paid += monthly_payment_actual

        if abs(balance) < 1e-8:
            balance = 0.0

        if payment_number % 12 == 0 or balance == 0.0:
            yearly_balances.append(round(balance, 2))
            yearly_interest_paid.append(round(current_year_interest, 2))
            yearly_principal_paid.append(round(current_year_principal, 2))
            yearly_total_paid.append(round(current_year_total_paid, 2))

            current_year_interest = 0.0
            current_year_principal = 0.0
            current_year_total_paid = 0.0

    years_needed = payment_number // 12
    remaining_months = payment_number % 12
    years_list = list(range(1, len(yearly_balances) + 1))

    yearly_df = pd.DataFrame({
        t["year"]: years_list,
        t["remaining_balance_eur"]: yearly_balances,
        t["interest_paid_eur"]: yearly_interest_paid,
        t["principal_repaid_eur"]: yearly_principal_paid,
        t["total_paid_eur"]: yearly_total_paid,
    })

    yearly_df[t["interest_share_pct"]] = (
        yearly_df[t["interest_paid_eur"]] / yearly_df[t["total_paid_eur"]] * 100
    ).round(1)

    yearly_df[t["principal_share_pct"]] = (
        yearly_df[t["principal_repaid_eur"]] / yearly_df[t["total_paid_eur"]] * 100
    ).round(1)

    return {
        "calculation_type": calculation_type,
        "loan_amount": round(loan_amount, 2),
        "annual_interest_rate": annual_interest_rate,
        "monthly_payment": round(monthly_payment, 2),
        "exact_monthly_payment": exact_monthly_payment,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "months_needed": payment_number,
        "years_needed": years_needed,
        "remaining_months": remaining_months,
        "yearly_df": yearly_df,
    }


def plot_balance_interactive(yearly_df: pd.DataFrame, t: dict):
    fig = px.line(
        yearly_df,
        x=t["year"],
        y=t["remaining_balance_eur"],
        markers=True,
        title=t["remaining_balance_graph"],
    )
    fig.update_traces(hovertemplate=t["hover_remaining_balance"])
    fig.update_layout(
        xaxis_title=t["year"],
        yaxis_title=t["remaining_balance_eur"],
        hovermode="closest",
    )
    return fig


def plot_total_principal_vs_interest(
    loan_amount: float,
    total_interest: float,
    total_paid: float,
    t: dict,
):
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[t["principal"], t["interest"]],
                values=[loan_amount, total_interest],
                hole=0.6,
                texttemplate=t["pie_texttemplate"],
                hovertemplate=t["pie_hovertemplate"],
            )
        ]
    )
    fig.update_layout(
        title=t["total_mortgage_cost"],
        annotations=[
            dict(
                text=f"{t['total']}<br>€{total_paid:,.0f}",
                x=0.5,
                y=0.5,
                showarrow=False,
                font_size=14,
            )
        ],
    )
    return fig


def plot_yearly_mortgage_cost(yearly_df: pd.DataFrame, t: dict):
    fig = go.Figure()

    fig.add_bar(
        x=yearly_df[t["year"]],
        y=yearly_df[t["principal_repaid_eur"]],
        name=t["principal"],
        hovertemplate=t["hover_principal_bar"],
    )

    fig.add_bar(
        x=yearly_df[t["year"]],
        y=yearly_df[t["interest_paid_eur"]],
        name=t["interest"],
        hovertemplate=t["hover_interest_bar"],
    )

    fig.update_layout(
        title=t["mortgage_cost_by_year"],
        xaxis_title=t["year"],
        yaxis_title=t["total_paid_eur"],
        barmode="stack",
        hovermode="x unified",
    )
    return fig


def build_simple_explanation_table(yearly_df: pd.DataFrame, t: dict) -> pd.DataFrame:
    selected_years = sorted(set([1, max(1, len(yearly_df) // 2), len(yearly_df)]))
    df = yearly_df[yearly_df[t["year"]].isin(selected_years)].copy()

    labels = {}
    if len(selected_years) >= 1:
        labels[selected_years[0]] = t["start"]
    if len(selected_years) >= 2:
        labels[selected_years[1]] = t["middle"]
    if len(selected_years) >= 3:
        labels[selected_years[-1]] = t["end"]

    df[t["simple_cols"]["stage"]] = df[t["year"]].map(labels)

    def explain(row):
        if row[t["interest_share_pct"]] >= 60:
            return t["mostly_interest"]
        if row[t["principal_share_pct"]] >= 60:
            return t["mostly_principal"]
        return t["balanced"]

    df[t["simple_cols"]["meaning"]] = df.apply(explain, axis=1)

    df[t["remaining_balance_eur"]] = df[t["remaining_balance_eur"]].map(lambda x: f"€{x:,.2f}")
    df[t["interest_paid_eur"]] = df[t["interest_paid_eur"]].map(lambda x: f"€{x:,.2f}")
    df[t["principal_repaid_eur"]] = df[t["principal_repaid_eur"]].map(lambda x: f"€{x:,.2f}")
    df[t["total_paid_eur"]] = df[t["total_paid_eur"]].map(lambda x: f"€{x:,.2f}")
    df[t["interest_share_pct"]] = df[t["interest_share_pct"]].map(lambda x: f"{x:.1f}%")
    df[t["principal_share_pct"]] = df[t["principal_share_pct"]].map(lambda x: f"{x:.1f}%")

    return df[
        [
            t["simple_cols"]["stage"],
            t["year"],
            t["remaining_balance_eur"],
            t["interest_paid_eur"],
            t["principal_repaid_eur"],
            t["total_paid_eur"],
            t["interest_share_pct"],
            t["principal_share_pct"],
            t["simple_cols"]["meaning"],
        ]
    ]


def format_full_table(df: pd.DataFrame, t: dict) -> pd.DataFrame:
    df = df.copy()
    euro_columns = [
        t["remaining_balance_eur"],
        t["interest_paid_eur"],
        t["principal_repaid_eur"],
        t["total_paid_eur"],
    ]
    pct_columns = [t["interest_share_pct"], t["principal_share_pct"]]

    for col in euro_columns:
        df[col] = df[col].map(lambda x: f"€{x:,.2f}")

    for col in pct_columns:
        df[col] = df[col].map(lambda x: f"{x:.1f}%")

    return df


def initialize_state():
    defaults = {
        "language": "English",
        "result": None,
        "result_mode": None,
        "selected_mode": None,
        "loan_amount_input": "",
        "annual_interest_rate_input": "",
        "years_input": "",
        "monthly_payment_input": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_result_state():
    st.session_state.result = None
    st.session_state.result_mode = None


def render_summary(result: dict, show_exact_payment: bool, t: dict):
    st.subheader(t["summary"])

    formatted_time = format_time_duration(
        result["years_needed"],
        result["remaining_months"],
        t,
    )

    col1, col2 = st.columns(2)
    col1.metric(t["monthly_payment_metric"], f"€{result['monthly_payment']:,.2f}")
    col2.metric(t["time_needed_metric"], formatted_time)

    col3, col4 = st.columns(2)
    col3.metric(t["total_paid_metric"], f"€{result['total_paid']:,.0f}")
    col4.metric(t["total_interest_metric"], f"€{result['total_interest']:,.0f}")

    if show_exact_payment:
        st.caption(
            t["exact_monthly_payment_caption"].format(
                value=result["exact_monthly_payment"]
            )
        )
    else:
        st.caption(
            t["payoff_caption"].format(
                payment=result["monthly_payment"],
                years=result["years_needed"],
                months=result["remaining_months"],
            )
        )


st.set_page_config(layout="centered", page_title="Mortgage Calculator")
initialize_state()

language = st.selectbox(
    "Language / Sprache",
    options=["English", "Deutsch"],
    key="language",
)

t = TRANSLATIONS[language]

mode_options = {
    t["monthly_payment_mode"]: "monthly",
    t["payoff_time_mode"]: "payoff",
}

st.title(t["app_title"])

selected_mode_label = st.radio(
    t["calculation_type"],
    options=list(mode_options.keys()),
    horizontal=True,
)

selected_mode = mode_options[selected_mode_label]

if st.session_state.selected_mode is None:
    st.session_state.selected_mode = selected_mode
elif st.session_state.selected_mode != selected_mode:
    st.session_state.selected_mode = selected_mode
    clear_result_state()

st.subheader(t["input_section"])

with st.form("main_form"):
    loan_amount_input = st.text_input(
        t["loan_amount"],
        value=st.session_state.loan_amount_input,
        placeholder=t["placeholder_loan"],
        key="loan_amount_widget",
    )

    annual_interest_rate_input = st.text_input(
        t["interest_rate"],
        value=st.session_state.annual_interest_rate_input,
        placeholder=t["placeholder_rate"],
        key="interest_rate_widget",
    )

    if selected_mode == "monthly":
        third_input = st.text_input(
            t["years"],
            value=st.session_state.years_input,
            placeholder=t["placeholder_years"],
            key="years_widget",
        )
    else:
        third_input = st.text_input(
            t["monthly_payment"],
            value=st.session_state.monthly_payment_input,
            placeholder=t["placeholder_payment"],
            key="payment_widget",
        )

        parsed_loan = None
        parsed_rate = None

        try:
            if loan_amount_input.strip():
                parsed_loan = parse_number(loan_amount_input)
        except ValueError:
            parsed_loan = None

        try:
            if annual_interest_rate_input.strip():
                parsed_rate = parse_number(annual_interest_rate_input)
        except ValueError:
            parsed_rate = None

        if parsed_loan is not None and parsed_rate is not None and parsed_loan > 0 and parsed_rate >= 0:
            live_minimum_payment = math.ceil(get_minimum_monthly_payment(parsed_loan, parsed_rate) * 100) / 100
            st.caption(t["minimum_payment_live_hint"].format(value=live_minimum_payment))

    submitted = st.form_submit_button(t["calculate"], use_container_width=True)

if submitted:
    clear_result_state()

    st.session_state.loan_amount_input = loan_amount_input
    st.session_state.annual_interest_rate_input = annual_interest_rate_input

    if selected_mode == "monthly":
        st.session_state.years_input = third_input
    else:
        st.session_state.monthly_payment_input = third_input

    field_errors = []

    loan_amount, error = validate_float_field(loan_amount_input, t["loan_amount"], t)
    if error:
        field_errors.append(error)

    annual_interest_rate, error = validate_float_field(annual_interest_rate_input, t["interest_rate"], t)
    if error:
        field_errors.append(error)

    if selected_mode == "monthly":
        third_value, error = validate_int_field(third_input, t["years"], t)
        if error:
            field_errors.append(error)
    else:
        third_value, error = validate_float_field(third_input, t["monthly_payment"], t)
        if error:
            field_errors.append(error)

    if loan_amount is not None and loan_amount <= 0:
        field_errors.append(t["loan_amount_error"])

    if annual_interest_rate is not None and annual_interest_rate < 0:
        field_errors.append(t["interest_rate_error"])

    if selected_mode == "monthly":
        if third_value is not None and third_value <= 0:
            field_errors.append(t["years_error"])
    else:
        if third_value is not None and third_value <= 0:
            field_errors.append(t["monthly_payment_error"])

    if field_errors:
        for err in field_errors:
            st.error(err)
    else:
        try:
            if selected_mode == "monthly":
                years = third_value

                st.session_state.result = calculate_mortgage_by_term(
                    loan_amount=loan_amount,
                    annual_interest_rate=annual_interest_rate,
                    years=years,
                    t=t,
                )
                st.session_state.result_mode = "monthly"

            else:
                monthly_payment = third_value

                st.session_state.result = calculate_mortgage_by_payment(
                    loan_amount=loan_amount,
                    annual_interest_rate=annual_interest_rate,
                    monthly_payment=monthly_payment,
                    t=t,
                )
                st.session_state.result_mode = "payoff"

        except ValueError as e:
            clear_result_state()

            message = str(e).strip()
            if message:
                st.error(message)
            else:
                st.error(t["invalid_numeric_error"])

result = st.session_state.result

st.subheader(t["results_section"])

if result is not None:
    tab_summary, tab_balance, tab_total_cost, tab_yearly_cost, tab_simple, tab_full = st.tabs(
        [
            t["summary"],
            t["remaining_balance_graph"],
            t["total_mortgage_cost"],
            t["mortgage_cost_by_year"],
            t["simple_explanation_table"],
            t["full_yearly_data_table"],
        ]
    )

    with tab_summary:
        render_summary(
            result=result,
            show_exact_payment=(result["calculation_type"] == t["monthly_payment_mode"]),
            t=t,
        )

    with tab_balance:
        st.subheader(t["remaining_balance_graph"])
        st.plotly_chart(
            plot_balance_interactive(result["yearly_df"], t),
            use_container_width=True,
        )

    with tab_total_cost:
        st.subheader(t["total_mortgage_cost"])
        st.plotly_chart(
            plot_total_principal_vs_interest(
                result["loan_amount"],
                result["total_interest"],
                result["total_paid"],
                t,
            ),
            use_container_width=True,
        )

    with tab_yearly_cost:
        st.subheader(t["mortgage_cost_by_year"])
        st.plotly_chart(
            plot_yearly_mortgage_cost(result["yearly_df"], t),
            use_container_width=True,
        )

    with tab_simple:
        st.subheader(t["simple_explanation_table"])
        st.dataframe(
            build_simple_explanation_table(result["yearly_df"], t),
            use_container_width=True,
            hide_index=True,
        )

    with tab_full:
        st.subheader(t["full_yearly_data_table"])
        st.dataframe(
            format_full_table(result["yearly_df"], t),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info(t["enter_values_info"])