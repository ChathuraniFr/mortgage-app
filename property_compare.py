import pandas as pd

from mortgage_features import calculate_mortgage_by_term
from property_models import PropertyListing


def estimate_total_purchase_cost(
    purchase_price: float,
    additional_costs_eur: float | None = None,
    closing_cost_rate_pct: float = 10.0,
) -> float:
    extra_costs = additional_costs_eur if additional_costs_eur is not None else 0.0
    closing_costs = purchase_price * (closing_cost_rate_pct / 100.0)
    return purchase_price + closing_costs + extra_costs


def calculate_price_per_sqm(
    price_eur: float,
    living_area_sqm: float | None,
) -> float | None:
    if living_area_sqm is None or living_area_sqm <= 0:
        return None
    return price_eur / living_area_sqm


def build_property_financing_summary(
    listing: PropertyListing,
    annual_interest_rate: float,
    years: int,
    t: dict,
    down_payment_eur: float = 0.0,
    closing_cost_rate_pct: float = 10.0,
    residual_balance_target: float = 0.0,
) -> dict:
    total_purchase_cost = estimate_total_purchase_cost(
        purchase_price=listing.price_eur,
        additional_costs_eur=listing.additional_costs_eur,
        closing_cost_rate_pct=closing_cost_rate_pct,
    )

    financed_amount = max(total_purchase_cost - down_payment_eur, 0.0)

    mortgage_result = calculate_mortgage_by_term(
        loan_amount=financed_amount,
        annual_interest_rate=annual_interest_rate,
        years=years,
        t=t,
        residual_balance_target=residual_balance_target,
    )

    return {
        "title": listing.title,
        "city": listing.city,
        "source": listing.source,
        "property_type": listing.property_type,
        "house_subtype": listing.house_subtype,
        "condition": listing.condition,
        "heating_type": listing.heating_type,
        "energy_source": listing.energy_source,
        "energy_class": listing.energy_class,
        "has_cellar": listing.has_cellar,
        "has_garage": listing.has_garage,
        "has_parking_space": listing.has_parking_space,
        "price_eur": listing.price_eur,
        "living_area_sqm": listing.living_area_sqm,
        "plot_area_sqm": listing.plot_area_sqm,
        "rooms": listing.rooms,
        "year_built": listing.year_built,
        "price_per_sqm": calculate_price_per_sqm(
            listing.price_eur,
            listing.living_area_sqm,
        ),
        "additional_costs_eur": listing.additional_costs_eur,
        "total_purchase_cost_eur": total_purchase_cost,
        "down_payment_eur": down_payment_eur,
        "financed_amount_eur": financed_amount,
        "monthly_payment_eur": mortgage_result["monthly_payment"],
        "exact_monthly_payment_eur": mortgage_result["exact_monthly_payment"],
        "total_interest_eur": mortgage_result["total_interest"],
        "total_paid_eur": mortgage_result["total_paid"],
        "residual_balance_target_eur": mortgage_result["residual_balance_target"],
        "url": listing.url,
    }


def compare_properties(
    listings: list[PropertyListing],
    annual_interest_rate: float,
    years: int,
    t: dict,
    down_payment_eur: float = 0.0,
    closing_cost_rate_pct: float = 10.0,
    residual_balance_target: float = 0.0,
) -> pd.DataFrame:
    rows = [
        build_property_financing_summary(
            listing=listing,
            annual_interest_rate=annual_interest_rate,
            years=years,
            t=t,
            down_payment_eur=down_payment_eur,
            closing_cost_rate_pct=closing_cost_rate_pct,
            residual_balance_target=residual_balance_target,
        )
        for listing in listings
    ]

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.sort_values(
            by=["monthly_payment_eur", "price_eur"],
            ascending=[True, True],
        ).reset_index(drop=True)

    return df


def format_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    formatted = df.copy()

    euro_cols = [
        "price_eur",
        "price_per_sqm",
        "additional_costs_eur",
        "total_purchase_cost_eur",
        "down_payment_eur",
        "financed_amount_eur",
        "monthly_payment_eur",
        "exact_monthly_payment_eur",
        "total_interest_eur",
        "total_paid_eur",
        "residual_balance_target_eur",
    ]

    for col in euro_cols:
        if col in formatted.columns:
            formatted[col] = formatted[col].apply(
                lambda x: f"€{x:,.2f}" if pd.notna(x) else ""
            )

    for col in ["has_cellar", "has_garage", "has_parking_space"]:
        if col in formatted.columns:
            formatted[col] = formatted[col].apply(
                lambda x: "Yes" if x is True else ("No" if x is False else "")
            )

    return formatted