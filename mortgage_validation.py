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