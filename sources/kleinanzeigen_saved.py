import re

from sources.base import ListingParser


def _search_patterns(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def _parse_number(value: str) -> float | None:
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


def _is_forbidden_price_context(text: str, start: int, end: int) -> bool:
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
        r"preis pro m²",
        r"preis pro qm",
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


def _extract_price_from_text(text: str) -> str | None:
    labeled_patterns = [
        r"(?:Kaufpreis|Preis)\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:€|EUR)",
        r"(?:Kaufpreis|Preis)\s*[:\-]?\s*(?:€|EUR)\s*([\d\.\,\s]+)",
        r"Festpreis\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:€|EUR)",
        r"VB\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:€|EUR)",
    ]

    for pattern in labeled_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = _parse_number(match.group(1))
            if value is None:
                continue
            if value < 20000:
                continue
            if _is_forbidden_price_context(text, match.start(), match.end()):
                continue
            return match.group(1).strip()

    generic_pattern = r"([\d\.\,\s]+)\s*(?:€|EUR)"
    for match in re.finditer(generic_pattern, text, flags=re.IGNORECASE):
        value = _parse_number(match.group(1))
        if value is None:
            continue
        if value < 20000:
            continue
        if _is_forbidden_price_context(text, match.start(), match.end()):
            continue
        return match.group(1).strip()

    return None


class KleinanzeigenSavedParser(ListingParser):
    def can_handle(self, text: str, html: str | None = None, file_name: str | None = None) -> bool:
        haystack = f"{text}\n{html or ''}".lower()

        indicators = [
            "kleinanzeigen",
            "anzeige",
            "nachricht schreiben",
            "privater anbieter",
            "gewerblicher anbieter",
            "immobilien",
        ]

        return sum(indicator in haystack for indicator in indicators) >= 2

    def extract_fields(self, text: str, html: str | None = None, file_name: str | None = None) -> dict:
        fields = {
            "source": "kleinanzeigen_saved",
            "title": self._extract_title(text),
            "price_eur": _extract_price_from_text(text),
            "living_area_sqm": _search_patterns(
                text,
                [
                    r"(?:Wohnfläche|Wohnflaeche)\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:m²|qm|sqm)",
                ],
            ),
            "plot_area_sqm": _search_patterns(
                text,
                [
                    r"(?:Grundstück|Grundstueck|Grundstücksfläche)\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:m²|qm|sqm)",
                ],
            ),
            "rooms": _search_patterns(
                text,
                [
                    r"Zimmer\s*[:\-]?\s*([\d\.\,\s]+)",
                ],
            ),
            "year_built": _search_patterns(
                text,
                [
                    r"Baujahr\s*[:\-]?\s*(\d{4})",
                ],
            ),
            "property_type": _search_patterns(
                text,
                [
                    r"Objektart\s*[:\-]?\s*([^\n\r]+)",
                    r"Art\s*[:\-]?\s*([^\n\r]+)",
                ],
            ),
            "condition": _search_patterns(
                text,
                [
                    r"Objektzustand\s*[:\-]?\s*([^\n\r]+)",
                ],
            ),
            "heating_type": _search_patterns(
                text,
                [
                    r"Heizungsart\s*[:\-]?\s*([^\n\r]+)",
                ],
            ),
            "energy_source": _search_patterns(
                text,
                [
                    r"Wesentliche Energieträger\s*[:\-]?\s*([^\n\r]+)",
                ],
            ),
            "energy_class": _search_patterns(
                text,
                [
                    r"Energieeffizienzklasse\s*[:\-]?\s*([A-H][+]*)",
                ],
            ),
            "address": _search_patterns(
                text,
                [
                    r"Adresse\s*[:\-]?\s*([^\n\r]+)",
                ],
            ),
        }

        postal_code, city = self._extract_postal_code_and_city(text)
        if postal_code:
            fields["postal_code"] = postal_code
        if city:
            fields["city"] = city

        return fields

    def _extract_title(self, text: str) -> str | None:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            first_line = lines[0]
            if len(first_line) >= 5:
                return first_line
        return None

    def _extract_postal_code_and_city(self, text: str) -> tuple[str | None, str | None]:
        match = re.search(r"\b(\d{5})\s+([A-Za-zÄÖÜäöüß\-\s]+)", text)
        if match:
            postal_code = match.group(1).strip()
            city = match.group(2).strip()
            city = re.split(r"[\n,|]", city)[0].strip()
            return postal_code, city
        return None, None