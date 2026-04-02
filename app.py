import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from mortgage_features import (
    calculate_balance_after_term,
    calculate_lump_sum_impact,
    calculate_mortgage_by_payment,
    calculate_mortgage_by_payment_with_lump_sum,
    calculate_mortgage_by_term,
    calculate_mortgage_by_term_with_lump_sum,
    get_minimum_monthly_payment,
)
from property_compare import compare_properties, format_comparison_table
from property_import import build_manual_listing, import_properties_from_uploaded_file
from property_models import PropertyListing
from property_storage import (
    clear_properties,
    get_saved_properties,
    initialize_property_storage,
    remove_property,
    save_many_properties,
    save_property,
)


TRANSLATIONS = {
    "English": {
        "app_title": "Mortgage Calculator",
        "language": "Language",
        "calculation_type": "Calculation type",
        "monthly_payment_mode": "Monthly payment",
        "payoff_time_mode": "Payoff time",
        "remaining_balance_mode": "Remaining balance after term",
        "loan_amount": "Loan amount (€)",
        "interest_rate": "Interest rate (%)",
        "years": "Years",
        "monthly_payment": "Monthly payment (€)",
        "annual_lump_sum": "Annual lump sum payment (€)",
        "residual_balance": "Target residual balance (€)",
        "calculate": "Calculate",
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
        "residual_balance_metric": "Residual Balance",
        "exact_monthly_payment_caption": "Exact monthly payment before rounding: €{value:,.6f}",
        "payoff_caption": "At €{payment:,.2f} per month, the mortgage reaches the target balance after {years} years and {months} months.",
        "balance_after_term_caption": "After {years} years of paying €{payment:,.2f} per month, the remaining balance is €{balance:,.2f}.",
        "residual_balance_caption": "Target residual balance: €{value:,.2f}",
        "time_needed_format_full": "{years} years, {months} months",
        "time_needed_format_years": "{years} years",
        "time_needed_format_months": "{months} months",
        "time_needed_format_zero": "0 months",
        "principal": "Principal repaid",
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
        "annual_lump_sum_error": "Annual lump sum payment cannot be negative.",
        "residual_balance_error": "Residual balance cannot be negative.",
        "residual_balance_too_high_error": "Residual balance must be lower than the loan amount.",
        "invalid_numeric_error": "Please enter valid numeric values in all required fields.",
        "payment_too_low_error": "The monthly payment is too low. It does not cover the monthly interest, so the loan would never be repaid.",
        "minimum_payment_needed": "The minimum monthly payment must be greater than €{value:,.2f}.",
        "minimum_payment_hint": "To reduce the loan balance, you must pay more than the monthly interest amount of €{value:,.2f}.",
        "minimum_payment_live_hint": "Minimum useful monthly payment: more than €{value:,.2f}",
        "placeholder_loan": "e.g. 400000",
        "placeholder_rate": "e.g. 4",
        "placeholder_years": "e.g. 30",
        "placeholder_payment": "e.g. 1909.67",
        "placeholder_lump_sum": "e.g. 5000",
        "placeholder_residual_balance": "e.g. 100000",
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
        "lump_sum_details_caption": "Base monthly payment: €{base:,.2f} | Annual lump sum: €{lump_sum:,.2f}",
        "lump_sum_savings_caption": "The annual lump sum saves €{interest_saved:,.2f} in interest and {years} years and {months} months in time.",
        "property_assistant_title": "Property Assistant",
        "property_assistant_info": "Save properties manually or import them, then compare them with mortgage scenarios.",
        "property_manual_entry_tab": "Manual entry",
        "property_import_tab": "Import",
        "property_saved_tab": "Saved properties",
        "property_compare_tab": "Compare properties",
        "property_title": "Title",
        "property_city": "City",
        "property_postal_code": "Postal code",
        "property_address": "Address",
        "property_price": "Purchase price (€)",
        "property_living_area": "Living area (sqm)",
        "property_plot_area": "Plot area (sqm)",
        "property_rooms": "Rooms",
        "property_year_built": "Year built",
        "property_type_label": "Property type",
        "property_condition": "Condition",
        "property_heating_type": "Heating type",
        "property_energy_source": "Main energy source",
        "property_energy_class": "Energy efficiency class",
        "property_additional_costs": "Additional costs (€)",
        "property_url": "Listing URL",
        "property_description": "Description",
        "property_save_button": "Save property",
        "property_saved_success": "Property saved.",
        "property_minimum_fields_error": "Please enter at least title, city, and a valid purchase price.",
        "property_import_file": "Upload CSV, XLSX, HTML, or PDF",
        "property_import_button": "Import properties",
        "property_import_success": "Imported {count} properties.",
        "property_import_error": "Import failed: {error}",
        "property_import_no_file": "Please upload a CSV, XLSX, HTML, or PDF file first.",
        "property_saved_empty": "No properties saved yet.",
        "property_remove_select": "Select property to remove",
        "property_remove_button": "Remove selected property",
        "property_remove_success": "Property removed.",
        "property_clear_button": "Clear all properties",
        "property_clear_success": "All properties removed.",
        "comparison_interest_rate": "Comparison interest rate (%)",
        "comparison_years": "Comparison years",
        "comparison_down_payment": "Down payment (€)",
        "comparison_closing_cost_rate": "Estimated closing cost rate (%)",
        "comparison_residual_balance": "Target residual balance (€)",
        "comparison_run_button": "Run comparison",
        "comparison_results_info": "Set the financing assumptions and run the comparison.",
        "property_source": "Source",
        "property_external_id": "ID",
        "property_comparison_sort_hint": "Results are sorted by estimated monthly payment and purchase price.",
        "main_tab_mortgage": "Mortgage Calculator",
        "main_tab_property": "Property Assistant",
        "import_preview_title": "Import preview",
        "import_preview_info": "Review and edit the extracted values before saving.",
        "import_preview_save_button": "Save previewed property",
        "import_preview_no_data": "No import preview available yet.",
        "import_preview_saved_success": "Previewed property saved.",
    },
    "Deutsch": {
        "app_title": "Kreditrechner",
        "language": "Sprache",
        "calculation_type": "Berechnungsart",
        "monthly_payment_mode": "Monatliche Rate",
        "payoff_time_mode": "Laufzeit",
        "remaining_balance_mode": "Restschuld nach Laufzeit",
        "loan_amount": "Darlehensbetrag (€)",
        "interest_rate": "Zinssatz (%)",
        "years": "Jahre",
        "monthly_payment": "Monatliche Rate (€)",
        "annual_lump_sum": "Jährliche Sondertilgung (€)",
        "residual_balance": "Ziel-Restschuld (€)",
        "calculate": "Berechnen",
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
        "residual_balance_metric": "Restschuld",
        "exact_monthly_payment_caption": "Exakte monatliche Rate vor Rundung: €{value:,.6f}",
        "payoff_caption": "Bei €{payment:,.2f} pro Monat erreicht die Hypothek die Ziel-Restschuld nach {years} Jahren und {months} Monaten.",
        "balance_after_term_caption": "Nach {years} Jahren mit einer monatlichen Rate von €{payment:,.2f} beträgt die Restschuld €{balance:,.2f}.",
        "residual_balance_caption": "Ziel-Restschuld: €{value:,.2f}",
        "time_needed_format_full": "{years} Jahre, {months} Monate",
        "time_needed_format_years": "{years} Jahre",
        "time_needed_format_months": "{months} Monate",
        "time_needed_format_zero": "0 Monate",
        "principal": "Getilgtes Kapital",
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
        "annual_lump_sum_error": "Die jährliche Sondertilgung darf nicht negativ sein.",
        "residual_balance_error": "Die Restschuld darf nicht negativ sein.",
        "residual_balance_too_high_error": "Die Restschuld muss kleiner sein als der Darlehensbetrag.",
        "invalid_numeric_error": "Bitte gib in allen erforderlichen Feldern gültige Zahlen ein.",
        "payment_too_low_error": "Die monatliche Rate ist zu niedrig. Sie deckt nicht einmal die monatlichen Zinsen, daher würde das Darlehen nie vollständig zurückgezahlt.",
        "minimum_payment_needed": "Die minimale monatliche Rate muss größer als €{value:,.2f} sein.",
        "minimum_payment_hint": "Damit sich die Restschuld verringert, muss die monatliche Rate höher sein als die monatlichen Zinsen von €{value:,.2f}.",
        "minimum_payment_live_hint": "Sinnvolle minimale Monatsrate: mehr als €{value:,.2f}",
        "placeholder_loan": "z. B. 400000",
        "placeholder_rate": "z. B. 4",
        "placeholder_years": "z. B. 30",
        "placeholder_payment": "z. B. 1909,67",
        "placeholder_lump_sum": "z. B. 5000",
        "placeholder_residual_balance": "z. B. 100000",
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
        "lump_sum_details_caption": "Normale Monatsrate: €{base:,.2f} | Jährliche Sondertilgung: €{lump_sum:,.2f}",
        "lump_sum_savings_caption": "Die jährliche Sondertilgung spart €{interest_saved:,.2f} Zinsen und {years} Jahre und {months} Monate Zeit.",
        "property_assistant_title": "Immobilien-Assistent",
        "property_assistant_info": "Speichere Immobilien manuell oder importiere sie und vergleiche sie anschließend mit Finanzierungsszenarien.",
        "property_manual_entry_tab": "Manuell",
        "property_import_tab": "Import",
        "property_saved_tab": "Gespeicherte Immobilien",
        "property_compare_tab": "Immobilien vergleichen",
        "property_title": "Titel",
        "property_city": "Stadt",
        "property_postal_code": "PLZ",
        "property_address": "Adresse",
        "property_price": "Kaufpreis (€)",
        "property_living_area": "Wohnfläche (qm)",
        "property_plot_area": "Grundstücksfläche (qm)",
        "property_rooms": "Zimmer",
        "property_year_built": "Baujahr",
        "property_type_label": "Objektart",
        "property_condition": "Objektzustand",
        "property_heating_type": "Heizungsart",
        "property_energy_source": "Wesentliche Energieträger",
        "property_energy_class": "Energieeffizienzklasse",
        "property_additional_costs": "Zusätzliche Kosten (€)",
        "property_url": "Inserats-URL",
        "property_description": "Beschreibung",
        "property_save_button": "Immobilie speichern",
        "property_saved_success": "Immobilie gespeichert.",
        "property_minimum_fields_error": "Bitte gib mindestens Titel, Stadt und einen gültigen Kaufpreis ein.",
        "property_import_file": "CSV, XLSX, HTML oder PDF hochladen",
        "property_import_button": "Immobilien importieren",
        "property_import_success": "{count} Immobilien importiert.",
        "property_import_error": "Import fehlgeschlagen: {error}",
        "property_import_no_file": "Bitte lade zuerst eine CSV-, XLSX-, HTML- oder PDF-Datei hoch.",
        "property_saved_empty": "Noch keine Immobilien gespeichert.",
        "property_remove_select": "Immobilie zum Löschen auswählen",
        "property_remove_button": "Ausgewählte Immobilie löschen",
        "property_remove_success": "Immobilie gelöscht.",
        "property_clear_button": "Alle Immobilien löschen",
        "property_clear_success": "Alle Immobilien gelöscht.",
        "comparison_interest_rate": "Vergleichszinssatz (%)",
        "comparison_years": "Vergleichslaufzeit",
        "comparison_down_payment": "Eigenkapital (€)",
        "comparison_closing_cost_rate": "Geschätzte Kaufnebenkosten (%)",
        "comparison_residual_balance": "Ziel-Restschuld (€)",
        "comparison_run_button": "Vergleich starten",
        "comparison_results_info": "Lege die Finanzierungsannahmen fest und starte dann den Vergleich.",
        "property_source": "Quelle",
        "property_external_id": "ID",
        "property_comparison_sort_hint": "Die Ergebnisse sind nach geschätzter Monatsrate und Kaufpreis sortiert.",
        "main_tab_mortgage": "Kreditrechner",
        "main_tab_property": "Immobilien-Assistent",
        "import_preview_title": "Import-Vorschau",
        "import_preview_info": "Prüfe und bearbeite die erkannten Werte vor dem Speichern.",
        "import_preview_save_button": "Vorschau-Immobilie speichern",
        "import_preview_no_data": "Noch keine Import-Vorschau vorhanden.",
        "import_preview_saved_success": "Vorschau-Immobilie gespeichert.",
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


def validate_optional_float_field(value: str, field_label: str, t: dict) -> tuple[float | None, str | None]:
    if value is None or value.strip() == "":
        return 0.0, None

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
    principal_repaid_total: float,
    total_interest: float,
    total_paid: float,
    t: dict,
):
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[t["principal"], t["interest"]],
                values=[principal_repaid_total, total_interest],
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
        "annual_lump_sum_input": "",
        "residual_balance_input": "",
        "import_preview_listing": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_result_state():
    st.session_state.result = None
    st.session_state.result_mode = None


def render_summary(result: dict, t: dict):
    st.subheader(t["summary"])

    col1, col2 = st.columns(2)
    col1.metric(t["monthly_payment_metric"], f"€{result['monthly_payment']:,.2f}")
    col2.metric(t["total_interest_metric"], f"€{result['total_interest']:,.0f}")

    col3, col4 = st.columns(2)
    col3.metric(t["total_paid_metric"], f"€{result['total_paid']:,.0f}")
    col4.metric(t["residual_balance_metric"], f"€{result['residual_balance_target']:,.2f}")

    if result["calculation_type"] == t["monthly_payment_mode"]:
        st.caption(
            t["exact_monthly_payment_caption"].format(
                value=result["exact_monthly_payment"]
            )
        )
        st.caption(
            t["residual_balance_caption"].format(
                value=result.get("residual_balance_target", 0.0)
            )
        )

    elif result["calculation_type"] == t["payoff_time_mode"]:
        st.caption(
            t["payoff_caption"].format(
                payment=result["monthly_payment"],
                years=result["years_needed"],
                months=result["remaining_months"],
            )
        )
        st.caption(
            t["residual_balance_caption"].format(
                value=result.get("residual_balance_target", 0.0)
            )
        )

    elif result["calculation_type"] == t["remaining_balance_mode"]:
        st.caption(
            t["balance_after_term_caption"].format(
                years=result["input_years"],
                payment=result["monthly_payment"],
                balance=result["residual_balance_target"],
            )
        )

    if result.get("annual_lump_sum", 0) > 0:
        st.caption(
            t["lump_sum_details_caption"].format(
                base=result["base_monthly_payment"],
                lump_sum=result["annual_lump_sum"],
            )
        )

        comparison = result.get("comparison")
        if comparison:
            st.caption(
                t["lump_sum_savings_caption"].format(
                    interest_saved=comparison["interest_saved"],
                    years=comparison["years_saved"],
                    months=comparison["remaining_months_saved"],
                )
            )


def render_mortgage_calculator(t: dict):
    mode_options = {
        t["monthly_payment_mode"]: "monthly",
        t["payoff_time_mode"]: "payoff",
        t["remaining_balance_mode"]: "balance_after_term",
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
            first_dynamic_input = st.text_input(
                t["years"],
                value=st.session_state.years_input,
                placeholder=t["placeholder_years"],
                key="years_widget",
            )
            second_dynamic_input = st.text_input(
                t["residual_balance"],
                value=st.session_state.residual_balance_input,
                placeholder=t["placeholder_residual_balance"],
                key="residual_balance_widget",
            )

        elif selected_mode == "payoff":
            first_dynamic_input = st.text_input(
                t["monthly_payment"],
                value=st.session_state.monthly_payment_input,
                placeholder=t["placeholder_payment"],
                key="payment_widget",
            )
            second_dynamic_input = st.text_input(
                t["residual_balance"],
                value=st.session_state.residual_balance_input,
                placeholder=t["placeholder_residual_balance"],
                key="residual_balance_widget",
            )

        else:
            first_dynamic_input = st.text_input(
                t["years"],
                value=st.session_state.years_input,
                placeholder=t["placeholder_years"],
                key="years_widget",
            )
            second_dynamic_input = st.text_input(
                t["monthly_payment"],
                value=st.session_state.monthly_payment_input,
                placeholder=t["placeholder_payment"],
                key="payment_widget",
            )

        annual_lump_sum_input = st.text_input(
            t["annual_lump_sum"],
            value=st.session_state.annual_lump_sum_input,
            placeholder=t["placeholder_lump_sum"],
            key="lump_sum_widget",
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
            live_minimum_payment = round(get_minimum_monthly_payment(parsed_loan, parsed_rate), 2)
            st.caption(t["minimum_payment_live_hint"].format(value=live_minimum_payment))

        submitted = st.form_submit_button(t["calculate"], use_container_width=True)

    if submitted:
        clear_result_state()

        st.session_state.loan_amount_input = loan_amount_input
        st.session_state.annual_interest_rate_input = annual_interest_rate_input
        st.session_state.annual_lump_sum_input = annual_lump_sum_input

        field_errors = []

        loan_amount, error = validate_float_field(loan_amount_input, t["loan_amount"], t)
        if error:
            field_errors.append(error)

        annual_interest_rate, error = validate_float_field(annual_interest_rate_input, t["interest_rate"], t)
        if error:
            field_errors.append(error)

        annual_lump_sum, error = validate_optional_float_field(
            annual_lump_sum_input,
            t["annual_lump_sum"],
            t,
        )
        if error:
            field_errors.append(error)

        if selected_mode == "monthly":
            st.session_state.years_input = first_dynamic_input
            st.session_state.residual_balance_input = second_dynamic_input

            years, error = validate_int_field(first_dynamic_input, t["years"], t)
            if error:
                field_errors.append(error)

            residual_balance_target, error = validate_optional_float_field(
                second_dynamic_input,
                t["residual_balance"],
                t,
            )
            if error:
                field_errors.append(error)

            if years is not None and years <= 0:
                field_errors.append(t["years_error"])

            if residual_balance_target is not None and residual_balance_target < 0:
                field_errors.append(t["residual_balance_error"])

            if (
                loan_amount is not None
                and residual_balance_target is not None
                and residual_balance_target >= loan_amount
            ):
                field_errors.append(t["residual_balance_too_high_error"])

        elif selected_mode == "payoff":
            st.session_state.monthly_payment_input = first_dynamic_input
            st.session_state.residual_balance_input = second_dynamic_input

            monthly_payment, error = validate_float_field(first_dynamic_input, t["monthly_payment"], t)
            if error:
                field_errors.append(error)

            residual_balance_target, error = validate_optional_float_field(
                second_dynamic_input,
                t["residual_balance"],
                t,
            )
            if error:
                field_errors.append(error)

            if monthly_payment is not None and monthly_payment <= 0:
                field_errors.append(t["monthly_payment_error"])

            if residual_balance_target is not None and residual_balance_target < 0:
                field_errors.append(t["residual_balance_error"])

            if (
                loan_amount is not None
                and residual_balance_target is not None
                and residual_balance_target >= loan_amount
            ):
                field_errors.append(t["residual_balance_too_high_error"])

        else:
            st.session_state.years_input = first_dynamic_input
            st.session_state.monthly_payment_input = second_dynamic_input

            years, error = validate_int_field(first_dynamic_input, t["years"], t)
            if error:
                field_errors.append(error)

            monthly_payment, error = validate_float_field(second_dynamic_input, t["monthly_payment"], t)
            if error:
                field_errors.append(error)

            if years is not None and years <= 0:
                field_errors.append(t["years_error"])

            if monthly_payment is not None and monthly_payment <= 0:
                field_errors.append(t["monthly_payment_error"])

        if loan_amount is not None and loan_amount <= 0:
            field_errors.append(t["loan_amount_error"])

        if annual_interest_rate is not None and annual_interest_rate < 0:
            field_errors.append(t["interest_rate_error"])

        if annual_lump_sum is not None and annual_lump_sum < 0:
            field_errors.append(t["annual_lump_sum_error"])

        if field_errors:
            for err in field_errors:
                st.error(err)
        else:
            try:
                if selected_mode == "monthly":
                    if annual_lump_sum > 0:
                        base_result = calculate_mortgage_by_term(
                            loan_amount=loan_amount,
                            annual_interest_rate=annual_interest_rate,
                            years=years,
                            t=t,
                            residual_balance_target=residual_balance_target,
                        )
                        result = calculate_mortgage_by_term_with_lump_sum(
                            loan_amount=loan_amount,
                            annual_interest_rate=annual_interest_rate,
                            years=years,
                            annual_lump_sum=annual_lump_sum,
                            t=t,
                            residual_balance_target=residual_balance_target,
                        )
                        result["comparison"] = calculate_lump_sum_impact(base_result, result)
                        st.session_state.result = result
                    else:
                        st.session_state.result = calculate_mortgage_by_term(
                            loan_amount=loan_amount,
                            annual_interest_rate=annual_interest_rate,
                            years=years,
                            t=t,
                            residual_balance_target=residual_balance_target,
                        )

                elif selected_mode == "payoff":
                    if annual_lump_sum > 0:
                        base_result = calculate_mortgage_by_payment(
                            loan_amount=loan_amount,
                            annual_interest_rate=annual_interest_rate,
                            monthly_payment=monthly_payment,
                            t=t,
                            residual_balance_target=residual_balance_target,
                        )
                        result = calculate_mortgage_by_payment_with_lump_sum(
                            loan_amount=loan_amount,
                            annual_interest_rate=annual_interest_rate,
                            monthly_payment=monthly_payment,
                            annual_lump_sum=annual_lump_sum,
                            t=t,
                            residual_balance_target=residual_balance_target,
                        )
                        result["comparison"] = calculate_lump_sum_impact(base_result, result)
                        st.session_state.result = result
                    else:
                        st.session_state.result = calculate_mortgage_by_payment(
                            loan_amount=loan_amount,
                            annual_interest_rate=annual_interest_rate,
                            monthly_payment=monthly_payment,
                            t=t,
                            residual_balance_target=residual_balance_target,
                        )

                else:
                    st.session_state.result = calculate_balance_after_term(
                        loan_amount=loan_amount,
                        annual_interest_rate=annual_interest_rate,
                        monthly_payment=monthly_payment,
                        years=years,
                        t=t,
                        annual_lump_sum=annual_lump_sum,
                    )

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
                    result["principal_repaid_total"],
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


def render_property_manual_entry(t: dict):
    st.subheader(t["property_manual_entry_tab"])

    with st.form("property_manual_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input(t["property_title"])
            city = st.text_input(t["property_city"])
            postal_code = st.text_input(t["property_postal_code"])
            address = st.text_input(t["property_address"])
            price_eur = st.number_input(
                t["property_price"],
                min_value=0.0,
                value=0.0,
                step=1000.0,
            )
            living_area_sqm = st.number_input(
                t["property_living_area"],
                min_value=0.0,
                value=0.0,
                step=1.0,
            )
            plot_area_sqm = st.number_input(
                t["property_plot_area"],
                min_value=0.0,
                value=0.0,
                step=1.0,
            )
            rooms = st.number_input(
                t["property_rooms"],
                min_value=0.0,
                value=0.0,
                step=0.5,
            )

        with col2:
            year_built = st.number_input(
                t["property_year_built"],
                min_value=0,
                value=0,
                step=1,
            )
            property_type = st.text_input(t["property_type_label"])
            condition = st.text_input(t["property_condition"])
            heating_type = st.text_input(t["property_heating_type"])
            energy_source = st.text_input(t["property_energy_source"])
            energy_class = st.text_input(t["property_energy_class"])
            additional_costs_eur = st.number_input(
                t["property_additional_costs"],
                min_value=0.0,
                value=0.0,
                step=1000.0,
            )

        url = st.text_input(t["property_url"])
        description = st.text_area(t["property_description"])

        submitted = st.form_submit_button(t["property_save_button"], use_container_width=True)

    if submitted:
        if not title.strip() or not city.strip() or price_eur <= 0:
            st.error(t["property_minimum_fields_error"])
            return

        listing = build_manual_listing(
            title=title,
            city=city,
            price_eur=price_eur,
            living_area_sqm=living_area_sqm if living_area_sqm > 0 else None,
            rooms=rooms if rooms > 0 else None,
            year_built=year_built if year_built > 0 else None,
            property_type=property_type if property_type.strip() else None,
            postal_code=postal_code if postal_code.strip() else None,
            address=address if address.strip() else None,
            plot_area_sqm=plot_area_sqm if plot_area_sqm > 0 else None,
            condition=condition if condition.strip() else None,
            heating_type=heating_type if heating_type.strip() else None,
            energy_source=energy_source if energy_source.strip() else None,
            energy_class=energy_class if energy_class.strip() else None,
            additional_costs_eur=additional_costs_eur if additional_costs_eur > 0 else None,
            url=url,
            description=description if description.strip() else None,
        )
        save_property(listing)
        st.success(t["property_saved_success"])


def render_import_preview_form(t: dict):
    st.subheader(t["import_preview_title"])
    st.info(t["import_preview_info"])

    preview = st.session_state.get("import_preview_listing")
    if preview is None:
        st.info(t["import_preview_no_data"])
        return

    with st.form("import_preview_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input(t["property_title"], value=preview.title)
            city = st.text_input(t["property_city"], value=preview.city)
            postal_code = st.text_input(t["property_postal_code"], value=preview.postal_code or "")
            address = st.text_input(t["property_address"], value=preview.address or "")
            price_eur = st.number_input(
                t["property_price"],
                min_value=0.0,
                value=float(preview.price_eur or 0.0),
                step=1000.0,
            )
            living_area_sqm = st.number_input(
                t["property_living_area"],
                min_value=0.0,
                value=float(preview.living_area_sqm or 0.0),
                step=1.0,
            )
            plot_area_sqm = st.number_input(
                t["property_plot_area"],
                min_value=0.0,
                value=float(preview.plot_area_sqm or 0.0),
                step=1.0,
            )
            rooms = st.number_input(
                t["property_rooms"],
                min_value=0.0,
                value=float(preview.rooms or 0.0),
                step=0.5,
            )

        with col2:
            year_built = st.number_input(
                t["property_year_built"],
                min_value=0,
                value=int(preview.year_built or 0),
                step=1,
            )
            property_type = st.text_input(t["property_type_label"], value=preview.property_type or "")

            # ✅ NEW FIELDS
            house_subtype = st.text_input("House subtype", value=getattr(preview, "house_subtype", "") or "")

            condition = st.text_input(t["property_condition"], value=preview.condition or "")
            heating_type = st.text_input(t["property_heating_type"], value=preview.heating_type or "")
            energy_source = st.text_input(t["property_energy_source"], value=preview.energy_source or "")
            energy_class = st.text_input(t["property_energy_class"], value=preview.energy_class or "")

            has_cellar = st.checkbox(
                "Cellar / Keller",
                value=bool(getattr(preview, "has_cellar", False)),
            )
            has_garage = st.checkbox(
                "Garage",
                value=bool(getattr(preview, "has_garage", False)),
            )
            has_parking_space = st.checkbox(
                "Parking space / Stellplatz",
                value=bool(getattr(preview, "has_parking_space", False)),
            )

            additional_costs_eur = st.number_input(
                t["property_additional_costs"],
                min_value=0.0,
                value=float(preview.additional_costs_eur or 0.0),
                step=1000.0,
            )

        url = st.text_input(t["property_url"], value=preview.url or "")
        description = st.text_area(t["property_description"], value=preview.description or "")

        submitted = st.form_submit_button(t["import_preview_save_button"], use_container_width=True)

    if submitted:
        if not title.strip() or not city.strip() or price_eur <= 0:
            st.error(t["property_minimum_fields_error"])
            return

        listing = PropertyListing(
            source=preview.source,
            external_id=preview.external_id,
            title=title.strip(),
            city=city.strip(),
            postal_code=postal_code.strip() if postal_code.strip() else None,
            address=address.strip() if address.strip() else None,
            price_eur=float(price_eur),
            living_area_sqm=living_area_sqm if living_area_sqm > 0 else None,
            plot_area_sqm=plot_area_sqm if plot_area_sqm > 0 else None,
            rooms=rooms if rooms > 0 else None,
            year_built=year_built if year_built > 0 else None,
            property_type=property_type.strip() if property_type.strip() else None,

            # ✅ NEW FIELDS (FIX FOR YOUR ERROR)
            house_subtype=house_subtype.strip() if house_subtype.strip() else None,
            has_cellar=has_cellar,
            has_garage=has_garage,
            has_parking_space=has_parking_space,

            condition=condition.strip() if condition.strip() else None,
            heating_type=heating_type.strip() if heating_type.strip() else None,
            energy_source=energy_source.strip() if energy_source.strip() else None,
            energy_class=energy_class.strip() if energy_class.strip() else None,

            additional_costs_eur=additional_costs_eur if additional_costs_eur > 0 else None,
            url=url.strip(),
            description=description.strip() if description.strip() else None,
        )

        save_property(listing)
        st.session_state.import_preview_listing = None
        st.success(t["import_preview_saved_success"])


def render_property_import_section(t: dict):
    st.subheader(t["property_import_tab"])

    uploaded_file = st.file_uploader(
        t["property_import_file"],
        type=["csv", "xlsx", "html", "htm", "pdf"],
        key="property_import_uploader",
    )

    if st.button(t["property_import_button"], use_container_width=True):
        if uploaded_file is None:
            st.error(t["property_import_no_file"])
            return

        try:
            listings = import_properties_from_uploaded_file(uploaded_file)

            if not listings:
                st.error(t["property_import_error"].format(error="No listing data found."))
                return

            first_listing = listings[0]
            st.session_state.import_preview_listing = first_listing
        except Exception as exc:
            st.error(t["property_import_error"].format(error=exc))

    render_import_preview_form(t)


def render_saved_properties_section(t: dict):
    st.subheader(t["property_saved_tab"])

    listings = get_saved_properties()

    if not listings:
        st.info(t["property_saved_empty"])
        return

    rows = []
    for item in listings:
        rows.append(
            {
                t["property_external_id"]: item.external_id,
                t["property_title"]: item.title,
                t["property_city"]: item.city,
                t["property_price"]: item.price_eur,
                t["property_living_area"]: item.living_area_sqm,
                t["property_plot_area"]: item.plot_area_sqm,
                t["property_rooms"]: item.rooms,
                t["property_year_built"]: item.year_built,
                t["property_type_label"]: item.property_type,
                t["property_condition"]: item.condition,
                t["property_heating_type"]: item.heating_type,
                t["property_energy_source"]: item.energy_source,
                t["property_energy_class"]: item.energy_class,
                t["property_source"]: item.source,
                t["property_url"]: item.url,
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    remove_options = {f"{item.title} ({item.city})": item.external_id for item in listings}
    selected_label = st.selectbox(
        t["property_remove_select"],
        options=[""] + list(remove_options.keys()),
        key="property_remove_selectbox",
    )

    if selected_label:
        if st.button(t["property_remove_button"], use_container_width=True):
            remove_property(remove_options[selected_label])
            st.success(t["property_remove_success"])
            st.rerun()

    if st.button(t["property_clear_button"], use_container_width=True):
        clear_properties()
        st.success(t["property_clear_success"])
        st.rerun()


def render_property_comparison_section(t: dict):
    st.subheader(t["property_compare_tab"])

    listings = get_saved_properties()

    if not listings:
        st.info(t["property_saved_empty"])
        return

    st.caption(t["comparison_results_info"])

    with st.form("property_comparison_form"):
        col1, col2 = st.columns(2)

        with col1:
            annual_interest_rate = st.number_input(
                t["comparison_interest_rate"],
                min_value=0.0,
                value=4.0,
                step=0.1,
            )
            years = st.number_input(
                t["comparison_years"],
                min_value=1,
                value=30,
                step=1,
            )
            down_payment_eur = st.number_input(
                t["comparison_down_payment"],
                min_value=0.0,
                value=50000.0,
                step=1000.0,
            )

        with col2:
            closing_cost_rate_pct = st.number_input(
                t["comparison_closing_cost_rate"],
                min_value=0.0,
                value=10.0,
                step=0.5,
            )
            residual_balance_target = st.number_input(
                t["comparison_residual_balance"],
                min_value=0.0,
                value=0.0,
                step=1000.0,
            )

        submitted = st.form_submit_button(t["comparison_run_button"], use_container_width=True)

    if submitted:
        comparison_df = compare_properties(
            listings=listings,
            annual_interest_rate=annual_interest_rate,
            years=years,
            t=t,
            down_payment_eur=down_payment_eur,
            closing_cost_rate_pct=closing_cost_rate_pct,
            residual_balance_target=residual_balance_target,
        )

        st.caption(t["property_comparison_sort_hint"])
        st.dataframe(
            format_comparison_table(comparison_df),
            use_container_width=True,
            hide_index=True,
        )


def render_property_assistant(t: dict):
    st.title(t["property_assistant_title"])
    st.info(t["property_assistant_info"])

    tab_manual, tab_import, tab_saved, tab_compare = st.tabs(
        [
            t["property_manual_entry_tab"],
            t["property_import_tab"],
            t["property_saved_tab"],
            t["property_compare_tab"],
        ]
    )

    with tab_manual:
        render_property_manual_entry(t)

    with tab_import:
        render_property_import_section(t)

    with tab_saved:
        render_saved_properties_section(t)

    with tab_compare:
        render_property_comparison_section(t)


st.set_page_config(layout="centered", page_title="Mortgage Calculator")
initialize_state()
initialize_property_storage()

language = st.selectbox(
    "Language / Sprache",
    options=["English", "Deutsch"],
    key="language",
)

t = TRANSLATIONS[language]

main_tab_mortgage, main_tab_property = st.tabs(
    [
        t["main_tab_mortgage"],
        t["main_tab_property"],
    ]
)

with main_tab_mortgage:
    render_mortgage_calculator(t)

with main_tab_property:
    render_property_assistant(t)