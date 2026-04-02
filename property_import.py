import io
import json
import re
import uuid
from pathlib import Path

import pandas as pd
import pdfplumber
from bs4 import BeautifulSoup
from pypdf import PdfReader

from property_models import PropertyListing
from sources.immoscout_saved import ImmoScoutSavedParser
from sources.kleinanzeigen_saved import KleinanzeigenSavedParser


PARSERS = [
    ImmoScoutSavedParser(),
    KleinanzeigenSavedParser(),
]


FIELD_SOURCE_PRIORITIES = {
    "price_eur": ["pdf", "html"],
    "living_area_sqm": ["html", "pdf"],
    "plot_area_sqm": ["html", "pdf"],
    "rooms": ["html", "pdf"],
    "year_built": ["html", "pdf"],
    "property_type": ["html", "pdf"],
    "house_subtype": ["html", "pdf"],
    "condition": ["html", "pdf"],
    "heating_type": ["html", "pdf"],
    "energy_source": ["html", "pdf"],
    "energy_class": ["html", "pdf"],
    "has_cellar": ["html", "pdf"],
    "has_garage": ["html", "pdf"],
    "has_parking_space": ["html", "pdf"],
    "postal_code": ["html", "pdf"],
    "city": ["html", "pdf"],
    "address": ["html", "pdf"],
    "title": ["html", "pdf"],
    "url": ["html", "pdf"],
}


MIN_REASONABLE_PURCHASE_PRICE_EUR = 20000.0
MIN_REASONABLE_AREA_SQM = 10.0
MAX_REASONABLE_AREA_SQM = 10000.0
MIN_REASONABLE_ROOMS = 0.5
MAX_REASONABLE_ROOMS = 50.0


HOUSE_SUBTYPE_PATTERNS = [
    (r"\breihenmittelhaus\b", "Reihenmittelhaus"),
    (r"\breiheneckhaus\b", "Reiheneckhaus"),
    (r"\breihenhaus\b", "Reihenhaus"),
    (r"\bdoppelhaush[äa]lfte\b", "Doppelhaushälfte"),
    (r"\beinfamilienhaus\b", "Einfamilienhaus"),
    (r"\bzweifamilienhaus\b", "Zweifamilienhaus"),
    (r"\bmehrfamilienhaus\b", "Mehrfamilienhaus"),
    (r"\bstadthaus\b", "Stadthaus"),
    (r"\bbungalow\b", "Bungalow"),
    (r"\bvilla\b", "Villa"),
    (r"\bfreistehend(?:es|e|er)? haus\b", "Freistehendes Haus"),
    (r"\bfreistehend\b", "Freistehend"),
]


def parse_number(value) -> float | None:
    if value is None:
        return None

    text = str(value).strip()
    if text == "":
        return None

    text = text.replace("€", "")
    text = text.replace("EUR", "")
    text = text.replace("eur", "")
    text = text.replace("\u00a0", " ")
    text = text.strip()

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "")
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")

    text = text.replace(" ", "")

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    return float(match.group(0))


def parse_int(value) -> int | None:
    parsed = parse_number(value)
    if parsed is None:
        return None
    return int(parsed)


def normalize_text(value) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text if text else None


def normalize_bool(value) -> bool | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()
    if text == "":
        return None

    truthy = {
        "true",
        "1",
        "yes",
        "y",
        "ja",
        "j",
        "vorhanden",
        "mit",
        "included",
    }
    falsy = {
        "false",
        "0",
        "no",
        "n",
        "nein",
        "nicht vorhanden",
        "ohne",
        "none",
    }

    if text in truthy:
        return True
    if text in falsy:
        return False

    return None


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def search_patterns(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def is_forbidden_price_context(text: str, start: int, end: int) -> bool:
    window_before = text[max(0, start - 80):start].lower()
    window_after = text[end:min(len(text), end + 80)].lower()
    combined = f"{window_before} {window_after}"

    forbidden_patterns = [
        r"€/m²",
        r"€/qm",
        r"€/sqm",
        r"euro/m²",
        r"pro m²",
        r"pro qm",
        r"je m²",
        r"je qm",
        r"hausgeld",
        r"nebenkosten",
        r"miete",
        r"kaltmiete",
        r"warmmiete",
        r"provision",
        r"courtage",
        r"erbpacht",
    ]

    return any(re.search(pattern, combined, flags=re.IGNORECASE) for pattern in forbidden_patterns)


def make_field(value, confidence: float, origin: str) -> dict | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    return {
        "value": text,
        "confidence": float(confidence),
        "origin": origin,
    }


def sanitize_purchase_price(value: float | None) -> float:
    if value is None:
        return 0.0
    if value < MIN_REASONABLE_PURCHASE_PRICE_EUR:
        return 0.0
    return float(value)


def sanitize_area(value: float | None) -> float | None:
    if value is None:
        return None
    if value < MIN_REASONABLE_AREA_SQM or value > MAX_REASONABLE_AREA_SQM:
        return None
    return float(value)


def sanitize_rooms(value: float | None) -> float | None:
    if value is None:
        return None
    if value < MIN_REASONABLE_ROOMS or value > MAX_REASONABLE_ROOMS:
        return None
    return float(value)


def choose_parser(text: str, html: str | None, file_name: str) -> object | None:
    for parser in PARSERS:
        if parser.can_handle(text=text, html=html, file_name=file_name):
            return parser
    return None


def extract_price_eur_from_text(text: str) -> dict | None:
    labeled_patterns = [
        r"(?:Kaufpreis|Purchase price|Price)\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:€|EUR)",
        r"(?:Kaufpreis|Purchase price|Price)\s*[:\-]?\s*(?:€|EUR)\s*([\d\.\,\s]+)",
    ]

    for pattern in labeled_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = parse_number(match.group(1))
            if value is None:
                continue
            if value < MIN_REASONABLE_PURCHASE_PRICE_EUR:
                continue
            if is_forbidden_price_context(text, match.start(), match.end()):
                continue
            return make_field(match.group(1), 0.88, "generic_labeled_price")

    generic_pattern = r"([\d\.\,\s]+)\s*(?:€|EUR)"
    for match in re.finditer(generic_pattern, text, flags=re.IGNORECASE):
        value = parse_number(match.group(1))
        if value is None:
            continue
        if value < MIN_REASONABLE_PURCHASE_PRICE_EUR:
            continue
        if is_forbidden_price_context(text, match.start(), match.end()):
            continue
        return make_field(match.group(1), 0.45, "generic_price")

    return None


def extract_living_area_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Wohnfläche|Living area|Wohnflaeche)\s*(?:ca\.)?\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:m²|qm|sqm)",
        r"([\d\.\,\s]+)\s*(?:m²|qm|sqm)\s*(?:Wohnfläche|Living area|Wohnflaeche)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            parsed = sanitize_area(parse_number(match.group(1)))
            if parsed is not None:
                return make_field(match.group(1), 0.82, "generic_living_area")
    return None


def extract_plot_area_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Grundstück|Grundst[üu]ck|Plot area|Lot size)\s*(?:ca\.)?\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:m²|qm|sqm)",
        r"([\d\.\,\s]+)\s*(?:m²|qm|sqm)\s*(?:Grundstück|Grundst[üu]ck|Plot area|Lot size)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            parsed = sanitize_area(parse_number(match.group(1)))
            if parsed is not None:
                return make_field(match.group(1), 0.80, "generic_plot_area")
    return None


def extract_rooms_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Zimmer|Zi\.|Rooms)\s*[:\-]?\s*([\d\.\,\s]+)",
        r"([\d\.\,\s]+)\s*(?:Zimmer|Zi\.|Rooms)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            parsed = sanitize_rooms(parse_number(match.group(1)))
            if parsed is not None:
                return make_field(match.group(1), 0.80, "generic_rooms")
    return None


def extract_year_built_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Baujahr|Year built)\s*[:\-]?\s*(\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            parsed = parse_int(match.group(1))
            if parsed is not None:
                return make_field(match.group(1), 0.82, "generic_year_built")
    return None


def extract_energy_class_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Energieeffizienzklasse|Energy class)\s*[:\-]?\s*([A-H][+]*)",
        r"\b([A-H][+]*)\b\s*(?:Energieeffizienzklasse|Energy class)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return make_field(match.group(1).upper(), 0.84, "generic_energy_class")
    return None


def extract_property_condition_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Objektzustand|Condition)\s*[:\-]?\s*([^\n\r]+)",
    ]
    value = search_patterns(text, patterns)
    return make_field(value, 0.80, "generic_condition")


def extract_heating_type_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Heizungsart|Heating type)\s*[:\-]?\s*([^\n\r]+)",
    ]
    value = search_patterns(text, patterns)
    return make_field(value, 0.80, "generic_heating_type")


def extract_energy_source_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Wesentliche Energieträger|Wesentlicher Energieträger|Energy source)\s*[:\-]?\s*([^\n\r]+)",
    ]
    value = search_patterns(text, patterns)
    return make_field(value, 0.80, "generic_energy_source")


def extract_house_subtype_from_text(text: str) -> dict | None:
    for pattern, normalized_value in HOUSE_SUBTYPE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return make_field(normalized_value, 0.88, "generic_house_subtype")
    return None


def extract_has_cellar_from_text(text: str) -> dict | None:
    if re.search(r"\bkeller\b", text, flags=re.IGNORECASE):
        if re.search(r"\bkein(?:en|er)?\s+keller\b", text, flags=re.IGNORECASE):
            return make_field("False", 0.85, "generic_has_cellar")
        return make_field("True", 0.88, "generic_has_cellar")
    return None


def extract_has_garage_from_text(text: str) -> dict | None:
    if re.search(r"\bgarage\b", text, flags=re.IGNORECASE):
        if re.search(r"\bkeine?\s+garage\b", text, flags=re.IGNORECASE):
            return make_field("False", 0.85, "generic_has_garage")
        return make_field("True", 0.88, "generic_has_garage")
    return None


def extract_has_parking_space_from_text(text: str) -> dict | None:
    if re.search(r"\b(stellplatz|außenstellplatz|aussenstellplatz|carport|parkplatz)\b", text, flags=re.IGNORECASE):
        return make_field("True", 0.88, "generic_has_parking_space")
    return None


def extract_postal_code_and_city(text: str) -> tuple[str | None, str | None]:
    match = re.search(r"\b(\d{5})\s+([A-Za-zÄÖÜäöüß\-\s]+)", text)
    if match:
        postal_code = match.group(1).strip()
        city = match.group(2).strip()
        city = re.split(r"[\n,|]", city)[0].strip()
        return postal_code, city
    return None, None


def extract_url_from_text(text: str) -> str:
    match = re.search(r"(https?://[^\s]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def extract_property_type_from_text(text: str) -> dict | None:
    patterns = [
        r"(?:Typ|Objektart|Property type)\s*[:\-]?\s*([^\n\r]+)",
    ]
    value = search_patterns(text, patterns)
    return make_field(value, 0.80, "generic_property_type")


def extract_title_from_text(text: str, fallback_title: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        first_line = lines[0]
        if len(first_line) >= 8:
            return first_line
    return fallback_title


def parse_filename_hints(file_name: str) -> dict:
    stem = Path(file_name).stem
    normalized = stem.replace("-", "_").replace(" ", "_")

    result = {
        "title": stem,
        "city": None,
        "postal_code": None,
        "price_eur": None,
        "living_area_sqm": None,
        "plot_area_sqm": None,
        "rooms": None,
        "year_built": None,
    }

    parts = [part for part in normalized.split("_") if part]

    if parts:
        first_part = parts[0]
        if not re.fullmatch(r"\d+", first_part):
            result["city"] = first_part

    for part in parts:
        lower = part.lower()

        if result["price_eur"] is None:
            price_match = re.fullmatch(r"(\d{4,7})", lower)
            if price_match:
                number = int(price_match.group(1))
                if MIN_REASONABLE_PURCHASE_PRICE_EUR <= number <= 50000000:
                    result["price_eur"] = float(number)
                    continue

        if result["rooms"] is None:
            rooms_match = re.fullmatch(r"(\d+(?:[.,]\d+)?)z", lower)
            if rooms_match:
                result["rooms"] = float(rooms_match.group(1).replace(",", "."))
                continue

        if result["living_area_sqm"] is None:
            area_match = re.fullmatch(r"(\d+(?:[.,]\d+)?)m2", lower)
            if area_match:
                result["living_area_sqm"] = float(area_match.group(1).replace(",", "."))
                continue

        if result["postal_code"] is None:
            postal_match = re.fullmatch(r"\d{5}", lower)
            if postal_match:
                result["postal_code"] = lower
                continue

        if result["year_built"] is None:
            year_match = re.fullmatch(r"(19\d{2}|20\d{2})", lower)
            if year_match:
                result["year_built"] = int(year_match.group(1))
                continue

    return result


def merge_candidate(existing: dict | None, candidate: dict | None, field_name: str) -> dict | None:
    if candidate is None:
        return existing
    if existing is None:
        return candidate

    existing_conf = float(existing.get("confidence", 0.0))
    candidate_conf = float(candidate.get("confidence", 0.0))

    if candidate_conf > existing_conf:
        return candidate

    if candidate_conf < existing_conf:
        return existing

    candidate_origin = str(candidate.get("origin", ""))
    existing_origin = str(existing.get("origin", ""))

    priority_sources = FIELD_SOURCE_PRIORITIES.get(field_name, ["html", "pdf"])

    def score(origin: str) -> int:
        origin_lower = origin.lower()
        for idx, source_name in enumerate(priority_sources):
            if source_name in origin_lower:
                return len(priority_sources) - idx
        return 0

    if score(candidate_origin) > score(existing_origin):
        return candidate

    return existing


def merge_field_maps(*maps: dict) -> dict:
    result: dict = {}

    for field_map in maps:
        for key, candidate in field_map.items():
            if key == "source":
                if key not in result and candidate is not None:
                    result[key] = candidate
                continue
            result[key] = merge_candidate(result.get(key), candidate, key)

    return result


def build_generic_field_map(text: str, file_name: str, source_name: str) -> dict:
    filename_hints = parse_filename_hints(file_name)
    postal_code, city = extract_postal_code_and_city(text)

    field_map = {
        "title": make_field(extract_title_from_text(text, Path(file_name).stem), 0.50, f"{source_name}_generic_title"),
        "price_eur": None,
        "living_area_sqm": extract_living_area_from_text(text),
        "plot_area_sqm": extract_plotArea_from_text(text) if False else extract_plot_area_from_text(text),
        "rooms": extract_rooms_from_text(text),
        "year_built": extract_year_built_from_text(text),
        "property_type": extract_property_type_from_text(text),
        "house_subtype": extract_house_subtype_from_text(text),
        "condition": extract_property_condition_from_text(text),
        "heating_type": extract_heating_type_from_text(text),
        "energy_source": extract_energy_source_from_text(text),
        "energy_class": extract_energy_class_from_text(text),
        "has_cellar": extract_has_cellar_from_text(text),
        "has_garage": extract_has_garage_from_text(text),
        "has_parking_space": extract_has_parking_space_from_text(text),
        "postal_code": make_field(postal_code, 0.72, f"{source_name}_generic_postal_city"),
        "city": make_field(city, 0.72, f"{source_name}_generic_postal_city"),
    }

    price_field = extract_price_eur_from_text(text)
    if price_field:
        price_field["origin"] = f"{source_name}_{price_field['origin']}"
    field_map["price_eur"] = price_field

    for field_name in [
        "living_area_sqm",
        "plot_area_sqm",
        "rooms",
        "year_built",
        "property_type",
        "house_subtype",
        "condition",
        "heating_type",
        "energy_source",
        "energy_class",
        "has_cellar",
        "has_garage",
        "has_parking_space",
        "postal_code",
        "city",
        "title",
    ]:
        field = field_map.get(field_name)
        if field is not None:
            field["origin"] = f"{source_name}_{field['origin']}"

    if filename_hints["price_eur"] is not None:
        field_map["price_eur"] = merge_candidate(
            field_map.get("price_eur"),
            make_field(str(filename_hints["price_eur"]), 0.35, f"{source_name}_filename_price"),
            "price_eur",
        )

    if filename_hints["living_area_sqm"] is not None:
        field_map["living_area_sqm"] = merge_candidate(
            field_map.get("living_area_sqm"),
            make_field(str(filename_hints["living_area_sqm"]), 0.35, f"{source_name}_filename_living_area"),
            "living_area_sqm",
        )

    if filename_hints["rooms"] is not None:
        field_map["rooms"] = merge_candidate(
            field_map.get("rooms"),
            make_field(str(filename_hints["rooms"]), 0.35, f"{source_name}_filename_rooms"),
            "rooms",
        )

    if filename_hints["year_built"] is not None:
        field_map["year_built"] = merge_candidate(
            field_map.get("year_built"),
            make_field(str(filename_hints["year_built"]), 0.35, f"{source_name}_filename_year_built"),
            "year_built",
        )

    if filename_hints["postal_code"] is not None:
        field_map["postal_code"] = merge_candidate(
            field_map.get("postal_code"),
            make_field(filename_hints["postal_code"], 0.35, f"{source_name}_filename_postal_code"),
            "postal_code",
        )

    if filename_hints["city"] is not None:
        field_map["city"] = merge_candidate(
            field_map.get("city"),
            make_field(filename_hints["city"], 0.30, f"{source_name}_filename_city"),
            "city",
        )

    return field_map


def build_listing_from_field_map(
    merged_fields: dict,
    source: str,
    fallback_title: str,
    text: str,
) -> PropertyListing:
    title_field = merged_fields.get("title")
    city_field = merged_fields.get("city")
    postal_code_field = merged_fields.get("postal_code")
    price_field = merged_fields.get("price_eur")
    living_area_field = merged_fields.get("living_area_sqm")
    plot_area_field = merged_fields.get("plot_area_sqm")
    rooms_field = merged_fields.get("rooms")
    year_built_field = merged_fields.get("year_built")
    property_type_field = merged_fields.get("property_type")
    house_subtype_field = merged_fields.get("house_subtype")
    condition_field = merged_fields.get("condition")
    heating_type_field = merged_fields.get("heating_type")
    energy_source_field = merged_fields.get("energy_source")
    energy_class_field = merged_fields.get("energy_class")
    has_cellar_field = merged_fields.get("has_cellar")
    has_garage_field = merged_fields.get("has_garage")
    has_parking_space_field = merged_fields.get("has_parking_space")
    address_field = merged_fields.get("address")
    url_field = merged_fields.get("url")

    title = title_field["value"] if title_field else fallback_title
    city = city_field["value"] if city_field else "Unknown"
    postal_code = postal_code_field["value"] if postal_code_field else None

    price_eur = sanitize_purchase_price(parse_number(price_field["value"]) if price_field else None)
    living_area_sqm = sanitize_area(parse_number(living_area_field["value"]) if living_area_field else None)
    plot_area_sqm = sanitize_area(parse_number(plot_area_field["value"]) if plot_area_field else None)
    rooms = sanitize_rooms(parse_number(rooms_field["value"]) if rooms_field else None)
    year_built = parse_int(year_built_field["value"]) if year_built_field else None

    property_type = property_type_field["value"] if property_type_field else None
    house_subtype = house_subtype_field["value"] if house_subtype_field else None
    condition = condition_field["value"] if condition_field else None
    heating_type = heating_type_field["value"] if heating_type_field else None
    energy_source = energy_source_field["value"] if energy_source_field else None
    energy_class = energy_class_field["value"] if energy_class_field else None
    has_cellar = normalize_bool(has_cellar_field["value"]) if has_cellar_field else None
    has_garage = normalize_bool(has_garage_field["value"]) if has_garage_field else None
    has_parking_space = normalize_bool(has_parking_space_field["value"]) if has_parking_space_field else None
    address = address_field["value"] if address_field else None

    url = url_field["value"] if url_field else extract_url_from_text(text)

    return PropertyListing(
        source=source,
        external_id=f"{source}_{uuid.uuid4().hex[:12]}",
        title=title.strip(),
        city=city.strip(),
        postal_code=normalize_text(postal_code),
        address=normalize_text(address),
        price_eur=price_eur,
        living_area_sqm=living_area_sqm,
        plot_area_sqm=plot_area_sqm,
        rooms=rooms,
        year_built=year_built,
        property_type=normalize_text(property_type),
        house_subtype=normalize_text(house_subtype),
        condition=normalize_text(condition),
        heating_type=normalize_text(heating_type),
        energy_source=normalize_text(energy_source),
        energy_class=normalize_text(energy_class),
        has_cellar=has_cellar,
        has_garage=has_garage,
        has_parking_space=has_parking_space,
        additional_costs_eur=None,
        url=url,
        description=text[:5000] if text else None,
    )


def extract_text_from_pdf(uploaded_file) -> str:
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    texts = []

    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    texts.append(page_text)
    except Exception:
        pass

    if texts:
        return clean_text("\n\n".join(texts))

    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text)
        return clean_text("\n\n".join(pages))
    except Exception:
        return ""


def extract_raw_html(uploaded_file) -> str:
    uploaded_file.seek(0)
    raw = uploaded_file.read()

    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("latin-1", errors="ignore")

    uploaded_file.seek(0)
    return html


def extract_text_from_html(uploaded_file) -> str:
    html = extract_raw_html(uploaded_file)
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    return clean_text(text)


def extract_json_ld_fields_from_html(html: str) -> dict:
    fields: dict = {}

    try:
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        for script in scripts:
            raw = script.string or script.get_text(strip=True)
            if not raw:
                continue

            try:
                data = json.loads(raw)
            except Exception:
                continue

            candidates = data if isinstance(data, list) else [data]
            for item in candidates:
                if not isinstance(item, dict):
                    continue

                if "name" in item and "title" not in fields:
                    fields["title"] = make_field(str(item["name"]), 0.90, "html_jsonld_title")

                if "url" in item and "url" not in fields:
                    fields["url"] = make_field(str(item["url"]), 0.90, "html_jsonld_url")

                if "address" in item and isinstance(item["address"], dict):
                    address_data = item["address"]
                    if address_data.get("postalCode") and "postal_code" not in fields:
                        fields["postal_code"] = make_field(str(address_data["postalCode"]), 0.92, "html_jsonld_address")
                    if address_data.get("addressLocality") and "city" not in fields:
                        fields["city"] = make_field(str(address_data["addressLocality"]), 0.92, "html_jsonld_address")
                    if address_data.get("streetAddress") and "address" not in fields:
                        fields["address"] = make_field(str(address_data["streetAddress"]), 0.90, "html_jsonld_address")
    except Exception:
        pass

    return fields


def build_manual_listing(
    title: str,
    city: str,
    price_eur: float,
    living_area_sqm: float | None = None,
    rooms: float | None = None,
    year_built: int | None = None,
    property_type: str | None = None,
    house_subtype: str | None = None,
    postal_code: str | None = None,
    address: str | None = None,
    plot_area_sqm: float | None = None,
    condition: str | None = None,
    heating_type: str | None = None,
    energy_source: str | None = None,
    energy_class: str | None = None,
    has_cellar: bool | None = None,
    has_garage: bool | None = None,
    has_parking_space: bool | None = None,
    additional_costs_eur: float | None = None,
    url: str = "",
    description: str | None = None,
) -> PropertyListing:
    return PropertyListing(
        source="manual",
        external_id=f"manual_{uuid.uuid4().hex[:10]}",
        title=title.strip(),
        city=city.strip(),
        postal_code=normalize_text(postal_code),
        address=normalize_text(address),
        price_eur=float(price_eur),
        living_area_sqm=living_area_sqm,
        plot_area_sqm=plot_area_sqm,
        rooms=rooms,
        year_built=year_built,
        property_type=normalize_text(property_type),
        house_subtype=normalize_text(house_subtype),
        condition=normalize_text(condition),
        heating_type=normalize_text(heating_type),
        energy_source=normalize_text(energy_source),
        energy_class=normalize_text(energy_class),
        has_cellar=has_cellar,
        has_garage=has_garage,
        has_parking_space=has_parking_space,
        additional_costs_eur=additional_costs_eur,
        url=url.strip(),
        description=normalize_text(description),
    )


def map_csv_row(row: dict) -> PropertyListing:
    title = row.get("title") or row.get("name") or row.get("objekt") or ""
    city = row.get("city") or row.get("stadt") or ""
    postal_code = row.get("postal_code") or row.get("zip") or row.get("plz")
    address = row.get("address") or row.get("street") or row.get("adresse")

    price_eur = (
        row.get("price_eur")
        or row.get("price")
        or row.get("kaufpreis")
        or row.get("purchase_price")
        or 0
    )

    living_area_sqm = (
        row.get("living_area_sqm")
        or row.get("living_area")
        or row.get("wohnflaeche")
        or row.get("wohnfläche")
    )

    plot_area_sqm = (
        row.get("plot_area_sqm")
        or row.get("plot_area")
        or row.get("grundstueck")
        or row.get("grundstück")
    )

    rooms = row.get("rooms") or row.get("zimmer")
    year_built = row.get("year_built") or row.get("baujahr")
    property_type = row.get("property_type") or row.get("objektart")
    house_subtype = row.get("house_subtype") or row.get("haussubtyp") or row.get("haus_typ")
    condition = row.get("condition") or row.get("objektzustand")
    heating_type = row.get("heating_type") or row.get("heizungsart")
    energy_source = row.get("energy_source") or row.get("wesentliche_energietraeger") or row.get("wesentliche energieträger")
    energy_class = row.get("energy_class") or row.get("energieklasse") or row.get("energieeffizienzklasse")
    has_cellar = row.get("has_cellar") or row.get("keller")
    has_garage = row.get("has_garage") or row.get("garage")
    has_parking_space = row.get("has_parking_space") or row.get("stellplatz")
    additional_costs_eur = (
        row.get("additional_costs_eur")
        or row.get("additional_costs")
        or row.get("nebenkosten")
    )
    url = row.get("url") or row.get("link") or ""
    description = row.get("description") or row.get("beschreibung")

    return PropertyListing(
        source="csv_import",
        external_id=str(row.get("external_id") or uuid.uuid4().hex[:12]),
        title=str(title).strip(),
        city=str(city).strip(),
        postal_code=normalize_text(postal_code),
        address=normalize_text(address),
        price_eur=sanitize_purchase_price(parse_number(price_eur)),
        living_area_sqm=sanitize_area(parse_number(living_area_sqm)),
        plot_area_sqm=sanitize_area(parse_number(plot_area_sqm)),
        rooms=sanitize_rooms(parse_number(rooms)),
        year_built=parse_int(year_built),
        property_type=normalize_text(property_type),
        house_subtype=normalize_text(house_subtype),
        condition=normalize_text(condition),
        heating_type=normalize_text(heating_type),
        energy_source=normalize_text(energy_source),
        energy_class=normalize_text(energy_class),
        has_cellar=normalize_bool(has_cellar),
        has_garage=normalize_bool(has_garage),
        has_parking_space=normalize_bool(has_parking_space),
        additional_costs_eur=parse_number(additional_costs_eur),
        url=str(url).strip(),
        description=normalize_text(description),
    )


def import_properties_from_dataframe(df: pd.DataFrame) -> list[PropertyListing]:
    listings: list[PropertyListing] = []

    for _, row in df.iterrows():
        listing = map_csv_row(row.to_dict())

        if listing.title and listing.city and listing.price_eur > 0:
            listings.append(listing)

    return listings


def import_properties_from_html(uploaded_file) -> list[PropertyListing]:
    html = extract_raw_html(uploaded_file)
    text = extract_text_from_html(uploaded_file)

    parser = choose_parser(text=text, html=html, file_name=uploaded_file.name)

    parser_fields = {}
    source_name = "html_import"

    if parser is not None:
        parser_fields = parser.extract_fields(
            text=text,
            html=html,
            file_name=uploaded_file.name,
        )
        source_name = parser_fields.get("source", {}).get("value", source_name)

    generic_fields = build_generic_field_map(text=text, file_name=uploaded_file.name, source_name="html")
    jsonld_fields = extract_json_ld_fields_from_html(html)

    merged_fields = merge_field_maps(generic_fields, jsonld_fields, parser_fields)

    listing = build_listing_from_field_map(
        merged_fields=merged_fields,
        source=source_name,
        fallback_title=uploaded_file.name.rsplit(".", 1)[0],
        text=text,
    )

    return [listing]


def import_properties_from_pdf(uploaded_file) -> list[PropertyListing]:
    text = extract_text_from_pdf(uploaded_file)

    parser = choose_parser(text=text, html=None, file_name=uploaded_file.name)

    parser_fields = {}
    source_name = "pdf_import"

    if parser is not None:
        parser_fields = parser.extract_fields(
            text=text,
            html=None,
            file_name=uploaded_file.name,
        )
        source_name = parser_fields.get("source", {}).get("value", source_name)

    generic_fields = build_generic_field_map(text=text, file_name=uploaded_file.name, source_name="pdf")

    merged_fields = merge_field_maps(generic_fields, parser_fields)

    listing = build_listing_from_field_map(
        merged_fields=merged_fields,
        source=source_name,
        fallback_title=uploaded_file.name.rsplit(".", 1)[0],
        text=text,
    )

    return [listing]


def import_properties_from_uploaded_file(uploaded_file) -> list[PropertyListing]:
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        return import_properties_from_dataframe(df)

    if file_name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
        return import_properties_from_dataframe(df)

    if file_name.endswith(".html") or file_name.endswith(".htm"):
        return import_properties_from_html(uploaded_file)

    if file_name.endswith(".pdf"):
        return import_properties_from_pdf(uploaded_file)

    raise ValueError("Only CSV, XLSX, HTML, HTM, and PDF files are supported.")