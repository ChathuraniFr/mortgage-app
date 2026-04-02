import pandas as pd
import streamlit as st

from property_compare import compare_properties, format_comparison_table
from property_import import build_manual_listing, import_properties_from_uploaded_file
from property_models import PropertyListing
from property_storage import (
    clear_properties,
    get_saved_properties,
    remove_property,
    save_property,
)


def _format_bool(value: bool | None) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return ""


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
            year_built = st.number_input(
                t["property_year_built"],
                min_value=0,
                value=0,
                step=1,
            )
            property_type = st.text_input(t["property_type_label"])
            house_subtype = st.text_input("House subtype")

        with col2:
            condition = st.text_input(t["property_condition"])
            heating_type = st.text_input(t["property_heating_type"])
            energy_source = st.text_input(t["property_energy_source"])
            energy_class = st.text_input(t["property_energy_class"])
            has_cellar = st.checkbox("Cellar / Keller")
            has_garage = st.checkbox("Garage")
            has_parking_space = st.checkbox("Parking space / Stellplatz")
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
            house_subtype=house_subtype if house_subtype.strip() else None,
            postal_code=postal_code if postal_code.strip() else None,
            address=address if address.strip() else None,
            plot_area_sqm=plot_area_sqm if plot_area_sqm > 0 else None,
            condition=condition if condition.strip() else None,
            heating_type=heating_type if heating_type.strip() else None,
            energy_source=energy_source if energy_source.strip() else None,
            energy_class=energy_class if energy_class.strip() else None,
            has_cellar=has_cellar,
            has_garage=has_garage,
            has_parking_space=has_parking_space,
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
            year_built = st.number_input(
                t["property_year_built"],
                min_value=0,
                value=int(preview.year_built or 0),
                step=1,
            )
            property_type = st.text_input(t["property_type_label"], value=preview.property_type or "")
            house_subtype = st.text_input("House subtype", value=preview.house_subtype or "")

        with col2:
            condition = st.text_input(t["property_condition"], value=preview.condition or "")
            heating_type = st.text_input(t["property_heating_type"], value=preview.heating_type or "")
            energy_source = st.text_input(t["property_energy_source"], value=preview.energy_source or "")
            energy_class = st.text_input(t["property_energy_class"], value=preview.energy_class or "")
            has_cellar = st.checkbox("Cellar / Keller", value=bool(preview.has_cellar) if preview.has_cellar is not None else False)
            has_garage = st.checkbox("Garage", value=bool(preview.has_garage) if preview.has_garage is not None else False)
            has_parking_space = st.checkbox("Parking space / Stellplatz", value=bool(preview.has_parking_space) if preview.has_parking_space is not None else False)
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
            house_subtype=house_subtype.strip() if house_subtype.strip() else None,
            condition=condition.strip() if condition.strip() else None,
            heating_type=heating_type.strip() if heating_type.strip() else None,
            energy_source=energy_source.strip() if energy_source.strip() else None,
            energy_class=energy_class.strip() if energy_class.strip() else None,
            has_cellar=has_cellar,
            has_garage=has_garage,
            has_parking_space=has_parking_space,
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
                "House subtype": item.house_subtype,
                t["property_condition"]: item.condition,
                t["property_heating_type"]: item.heating_type,
                t["property_energy_source"]: item.energy_source,
                t["property_energy_class"]: item.energy_class,
                "Cellar": _format_bool(item.has_cellar),
                "Garage": _format_bool(item.has_garage),
                "Parking space": _format_bool(item.has_parking_space),
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