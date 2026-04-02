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
from mortgage_validation import (
    parse_number,
    validate_float_field,
    validate_int_field,
    validate_optional_float_field,
)
from mortgage_visuals import (
    build_simple_explanation_table,
    format_full_table,
    plot_balance_interactive,
    plot_total_principal_vs_interest,
    plot_yearly_mortgage_cost,
)


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