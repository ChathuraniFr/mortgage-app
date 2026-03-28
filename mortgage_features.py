import math
import pandas as pd


def get_minimum_monthly_payment(loan_amount: float, annual_interest_rate: float) -> float:
    monthly_interest_rate = annual_interest_rate / 100 / 12
    return loan_amount * monthly_interest_rate


def validate_monthly_payment(
    loan_amount: float,
    annual_interest_rate: float,
    monthly_payment: float,
    t: dict,
) -> None:
    monthly_interest_rate = annual_interest_rate / 100 / 12

    if monthly_interest_rate > 0 and monthly_payment <= loan_amount * monthly_interest_rate:
        minimum_payment = math.ceil((loan_amount * monthly_interest_rate) * 100) / 100
        raise ValueError(
            f"{t['payment_too_low_error']} "
            f"{t['minimum_payment_needed'].format(value=minimum_payment)} "
            f"{t['minimum_payment_hint'].format(value=minimum_payment)}"
        )


def calculate_exact_monthly_payment(
    loan_amount: float,
    annual_interest_rate: float,
    years: int,
    residual_balance_target: float = 0.0,
) -> float:
    monthly_interest_rate = annual_interest_rate / 100 / 12
    number_of_payments = years * 12

    if monthly_interest_rate == 0:
        return (loan_amount - residual_balance_target) / number_of_payments

    discounted_residual = residual_balance_target / ((1 + monthly_interest_rate) ** number_of_payments)

    return (
        (loan_amount - discounted_residual)
        * monthly_interest_rate
        / (1 - (1 + monthly_interest_rate) ** (-number_of_payments))
    )


def build_amortization_schedule(
    loan_amount: float,
    annual_interest_rate: float,
    monthly_payment: float,
    exact_monthly_payment: float,
    calculation_type: str,
    t: dict,
    annual_lump_sum: float = 0.0,
    residual_balance_target: float = 0.0,
) -> dict:
    monthly_interest_rate = annual_interest_rate / 100 / 12

    if loan_amount <= 0:
        raise ValueError(t["loan_amount_error"])

    if annual_interest_rate < 0:
        raise ValueError(t["interest_rate_error"])

    if monthly_payment <= 0:
        raise ValueError(t["monthly_payment_error"])

    if residual_balance_target < 0:
        raise ValueError(t["residual_balance_error"])

    if residual_balance_target >= loan_amount:
        raise ValueError(t["residual_balance_too_high_error"])

    validate_monthly_payment(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        t=t,
    )

    balance = loan_amount
    total_paid = 0.0
    total_interest = 0.0
    payment_number = 0

    yearly_balances = []
    yearly_interest_paid = []
    yearly_principal_paid = []
    yearly_total_paid = []

    current_year_interest = 0.0
    current_year_principal = 0.0
    current_year_total_paid = 0.0

    while balance - residual_balance_target > 1e-8:
        payment_number += 1

        interest = balance * monthly_interest_rate
        principal = monthly_payment - interest
        remaining_principal_needed = balance - residual_balance_target

        if principal > remaining_principal_needed:
            principal = remaining_principal_needed
            monthly_payment_actual = interest + principal
        else:
            monthly_payment_actual = monthly_payment

        balance -= principal
        total_paid += monthly_payment_actual
        total_interest += interest

        current_year_interest += interest
        current_year_principal += principal
        current_year_total_paid += monthly_payment_actual

        if abs(balance - residual_balance_target) < 1e-8:
            balance = residual_balance_target

        if payment_number % 12 == 0 and balance > residual_balance_target and annual_lump_sum > 0:
            max_lump_sum = balance - residual_balance_target
            lump_sum_actual = min(annual_lump_sum, max_lump_sum)

            balance -= lump_sum_actual
            total_paid += lump_sum_actual
            current_year_principal += lump_sum_actual
            current_year_total_paid += lump_sum_actual

            if abs(balance - residual_balance_target) < 1e-8:
                balance = residual_balance_target

        if payment_number % 12 == 0 or balance == residual_balance_target:
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

    principal_repaid_total = round(loan_amount - residual_balance_target, 2)

    return {
        "calculation_type": calculation_type,
        "loan_amount": round(loan_amount, 2),
        "annual_interest_rate": annual_interest_rate,
        "monthly_payment": round(monthly_payment, 2),
        "base_monthly_payment": round(monthly_payment, 2),
        "annual_lump_sum": round(annual_lump_sum, 2),
        "exact_monthly_payment": exact_monthly_payment,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "months_needed": payment_number,
        "years_needed": years_needed,
        "remaining_months": remaining_months,
        "residual_balance_target": round(residual_balance_target, 2),
        "principal_repaid_total": principal_repaid_total,
        "yearly_df": yearly_df,
    }


def calculate_balance_after_term(
    loan_amount: float,
    annual_interest_rate: float,
    monthly_payment: float,
    years: int,
    t: dict,
    annual_lump_sum: float = 0.0,
) -> dict:
    monthly_interest_rate = annual_interest_rate / 100 / 12

    if loan_amount <= 0:
        raise ValueError(t["loan_amount_error"])

    if annual_interest_rate < 0:
        raise ValueError(t["interest_rate_error"])

    if monthly_payment <= 0:
        raise ValueError(t["monthly_payment_error"])

    if years <= 0:
        raise ValueError(t["years_error"])

    validate_monthly_payment(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        t=t,
    )

    total_months = years * 12
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

    actual_months_run = 0

    for month in range(1, total_months + 1):
        if balance <= 1e-8:
            balance = 0.0
            break

        actual_months_run += 1

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

        if month % 12 == 0 and balance > 0.0 and annual_lump_sum > 0:
            lump_sum_actual = min(annual_lump_sum, balance)
            balance -= lump_sum_actual
            total_paid += lump_sum_actual
            current_year_principal += lump_sum_actual
            current_year_total_paid += lump_sum_actual

            if abs(balance) < 1e-8:
                balance = 0.0

        if month % 12 == 0 or month == total_months or balance == 0.0:
            yearly_balances.append(round(balance, 2))
            yearly_interest_paid.append(round(current_year_interest, 2))
            yearly_principal_paid.append(round(current_year_principal, 2))
            yearly_total_paid.append(round(current_year_total_paid, 2))

            current_year_interest = 0.0
            current_year_principal = 0.0
            current_year_total_paid = 0.0

        if balance == 0.0:
            break

    years_list = list(range(1, len(yearly_balances) + 1))
    principal_repaid_total = round(loan_amount - balance, 2)

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
        "calculation_type": t["remaining_balance_mode"],
        "loan_amount": round(loan_amount, 2),
        "annual_interest_rate": annual_interest_rate,
        "monthly_payment": round(monthly_payment, 2),
        "base_monthly_payment": round(monthly_payment, 2),
        "annual_lump_sum": round(annual_lump_sum, 2),
        "exact_monthly_payment": monthly_payment,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "months_needed": actual_months_run,
        "years_needed": actual_months_run // 12,
        "remaining_months": actual_months_run % 12,
        "residual_balance_target": round(balance, 2),
        "principal_repaid_total": principal_repaid_total,
        "input_years": years,
        "yearly_df": yearly_df,
    }


def calculate_mortgage_by_term(
    loan_amount: float,
    annual_interest_rate: float,
    years: int,
    t: dict,
    residual_balance_target: float = 0.0,
) -> dict:
    exact_monthly_payment = calculate_exact_monthly_payment(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        years=years,
        residual_balance_target=residual_balance_target,
    )

    # Intentionally round up to the next cent so the fixed monthly payment
    # always covers the exact amortizing payment and the loan is not underpaid.
    monthly_payment = math.ceil(exact_monthly_payment * 100) / 100

    return build_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        exact_monthly_payment=exact_monthly_payment,
        calculation_type=t["monthly_payment_mode"],
        t=t,
        annual_lump_sum=0.0,
        residual_balance_target=residual_balance_target,
    )


def calculate_mortgage_by_payment(
    loan_amount: float,
    annual_interest_rate: float,
    monthly_payment: float,
    t: dict,
    residual_balance_target: float = 0.0,
) -> dict:
    return build_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        exact_monthly_payment=monthly_payment,
        calculation_type=t["payoff_time_mode"],
        t=t,
        annual_lump_sum=0.0,
        residual_balance_target=residual_balance_target,
    )


def calculate_mortgage_by_term_with_lump_sum(
    loan_amount: float,
    annual_interest_rate: float,
    years: int,
    annual_lump_sum: float,
    t: dict,
    residual_balance_target: float = 0.0,
) -> dict:
    exact_monthly_payment = calculate_exact_monthly_payment(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        years=years,
        residual_balance_target=residual_balance_target,
    )

    # Intentionally round up to the next cent so the fixed monthly payment
    # always covers the exact amortizing payment and the loan is not underpaid.
    monthly_payment = math.ceil(exact_monthly_payment * 100) / 100

    return build_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        exact_monthly_payment=exact_monthly_payment,
        calculation_type=t["monthly_payment_mode"],
        t=t,
        annual_lump_sum=annual_lump_sum,
        residual_balance_target=residual_balance_target,
    )


def calculate_mortgage_by_payment_with_lump_sum(
    loan_amount: float,
    annual_interest_rate: float,
    monthly_payment: float,
    annual_lump_sum: float,
    t: dict,
    residual_balance_target: float = 0.0,
) -> dict:
    return build_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        exact_monthly_payment=monthly_payment,
        calculation_type=t["payoff_time_mode"],
        t=t,
        annual_lump_sum=annual_lump_sum,
        residual_balance_target=residual_balance_target,
    )


def calculate_lump_sum_impact(base_result: dict, lump_sum_result: dict) -> dict:
    months_saved = base_result["months_needed"] - lump_sum_result["months_needed"]
    interest_saved = round(base_result["total_interest"] - lump_sum_result["total_interest"], 2)

    return {
        "months_saved": months_saved,
        "years_saved": months_saved // 12,
        "remaining_months_saved": months_saved % 12,
        "interest_saved": interest_saved,
    }