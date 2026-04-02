import json
import re

from bs4 import BeautifulSoup

from sources.base import ListingParser


def _search_patterns(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def _field(value: str | None, confidence: float, origin: str) -> dict | None:
    if value is None or str(value).strip() == "":
        return None
    return {
        "value": value.strip(),
        "confidence": confidence,
        "origin": origin,
    }


def _extract_json_ld_fields(html: str) -> dict:
    result: dict[str, dict] = {}

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

            graph = data.get("@graph")
            if not isinstance(graph, list):
                continue

            for item in graph:
                if not isinstance(item, dict):
                    continue
                if item.get("@type") != "RealEstateListing":
                    continue

                if item.get("name") and "title" not in result:
                    result["title"] = _field(
                        str(item["name"]),
                        0.99,
                        "immoscout_jsonld_name",
                    )

                if item.get("url") and "url" not in result:
                    result["url"] = _field(
                        str(item["url"]),
                        0.98,
                        "immoscout_jsonld_url",
                    )

                offers = item.get("offers")
                if isinstance(offers, dict):
                    price = offers.get("price")
                    if price and "price_eur" not in result:
                        result["price_eur"] = _field(
                            str(price),
                            1.00,
                            "immoscout_jsonld_price",
                        )

            if result:
                return result
    except Exception:
        pass

    return result


def _extract_js_fields(html: str) -> dict:
    result: dict[str, dict] = {}

    patterns = {
        "price_eur": [
            (r'purchasePrice\s*:\s*"(\d+)"', 0.98, "immoscout_js_purchase_price"),
            (r'propertyPrice\s*:\s*"(\d+)"', 0.97, "immoscout_js_property_price"),
            (r'obj_purchasePrice"\s*:\s*"(\d+)"', 0.96, "immoscout_tracking_purchase_price"),
        ],
        "year_built": [
            (r'obj_yearConstructed"\s*:\s*"(\d{4})"', 0.92, "immoscout_tracking_year_built"),
        ],
        "energy_class": [
            (r'obj_energyEfficiencyClass"\s*:\s*"([A-H][+]*)"', 0.92, "immoscout_tracking_energy_class"),
        ],
        "living_area_sqm": [
            (r'obj_livingSpace"\s*:\s*"([\d\.]+)"', 0.92, "immoscout_tracking_living_area"),
            (r'squareMeters"\s*:\s*([\d\.]+)', 0.90, "immoscout_js_square_meters"),
        ],
        "plot_area_sqm": [
            (r'obj_lotArea"\s*:\s*"([\d\.]+)"', 0.90, "immoscout_tracking_plot_area"),
        ],
        "rooms": [
            (r'obj_noRooms"\s*:\s*"([\d\.]+)"', 0.92, "immoscout_tracking_rooms"),
            (r'numberOfRooms"\s*:\s*([\d\.]+)', 0.90, "immoscout_js_rooms"),
        ],
        "postal_code": [
            (r'zip"\s*:\s*"(\d{5})"', 0.92, "immoscout_js_zip"),
            (r'obj_zipCode"\s*:\s*"(\d{5})"', 0.92, "immoscout_tracking_zip"),
        ],
        "city": [
            (r'city"\s*:\s*"([^"]+)"', 0.88, "immoscout_js_city"),
        ],
        "condition": [
            (r'obj_condition"\s*:\s*"([^"]+)"', 0.88, "immoscout_tracking_condition"),
        ],
        "heating_type": [
            (r'obj_heatingType"\s*:\s*"([^"]+)"', 0.88, "immoscout_tracking_heating_type"),
        ],
        "energy_source": [
            (r'obj_firingTypes"\s*:\s*"([^"]+)"', 0.88, "immoscout_tracking_energy_source"),
        ],
    }

    for field_name, field_patterns in patterns.items():
        for pattern, confidence, origin in field_patterns:
            match = re.search(pattern, html, flags=re.IGNORECASE)
            if match:
                result[field_name] = _field(match.group(1), confidence, origin)
                break

    return result


class ImmoScoutSavedParser(ListingParser):
    def can_handle(self, text: str, html: str | None = None, file_name: str | None = None) -> bool:
        haystack = f"{text}\n{html or ''}".lower()

        indicators = [
            "immobilienscout24",
            "immoscout",
            "scout-id",
            "realestatelisting",
            "purchaseprice",
        ]

        return sum(indicator in haystack for indicator in indicators) >= 2

    def extract_fields(self, text: str, html: str | None = None, file_name: str | None = None) -> dict:
        fields: dict[str, dict] = {
            "source": {
                "value": "immoscout_saved",
                "confidence": 1.0,
                "origin": "parser",
            }
        }

        if html:
            jsonld_fields = _extract_json_ld_fields(html)
            for key, value in jsonld_fields.items():
                fields[key] = value

            js_fields = _extract_js_fields(html)
            for key, value in js_fields.items():
                if key not in fields:
                    fields[key] = value

        if "title" not in fields:
            title = self._extract_title(text)
            if title:
                fields["title"] = _field(title, 0.70, "immoscout_first_line")

        if "living_area_sqm" not in fields:
            living_area = _search_patterns(
                text,
                [
                    r"Wohnfläche\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:m²|qm|sqm)",
                ],
            )
            if living_area:
                fields["living_area_sqm"] = _field(
                    living_area,
                    0.82,
                    "immoscout_text_living_area",
                )

        if "plot_area_sqm" not in fields:
            plot_area = _search_patterns(
                text,
                [
                    r"(?:Grundstück|Grundstücksfläche)\s*[:\-]?\s*([\d\.\,\s]+)\s*(?:m²|qm|sqm)",
                ],
            )
            if plot_area:
                fields["plot_area_sqm"] = _field(
                    plot_area,
                    0.80,
                    "immoscout_text_plot_area",
                )

        if "rooms" not in fields:
            rooms = _search_patterns(
                text,
                [
                    r"Zimmer\s*[:\-]?\s*([\d\.\,\s]+)",
                    r"([\d\.\,\s]+)\s*Zi\.",
                ],
            )
            if rooms:
                fields["rooms"] = _field(
                    rooms,
                    0.80,
                    "immoscout_text_rooms",
                )

        if "year_built" not in fields:
            year_built = _search_patterns(
                text,
                [
                    r"Baujahr\s*[:\-]?\s*(\d{4})",
                ],
            )
            if year_built:
                fields["year_built"] = _field(
                    year_built,
                    0.80,
                    "immoscout_text_year_built",
                )

        if "condition" not in fields:
            condition = _search_patterns(
                text,
                [
                    r"Objektzustand\s*[:\-]?\s*([^\n\r]+)",
                ],
            )
            if condition:
                fields["condition"] = _field(
                    condition,
                    0.78,
                    "immoscout_text_condition",
                )

        if "heating_type" not in fields:
            heating_type = _search_patterns(
                text,
                [
                    r"Heizungsart\s*[:\-]?\s*([^\n\r]+)",
                ],
            )
            if heating_type:
                fields["heating_type"] = _field(
                    heating_type,
                    0.78,
                    "immoscout_text_heating_type",
                )

        if "energy_source" not in fields:
            energy_source = _search_patterns(
                text,
                [
                    r"Wesentliche Energieträger\s*[:\-]?\s*([^\n\r]+)",
                    r"Wesentlicher Energieträger\s*[:\-]?\s*([^\n\r]+)",
                ],
            )
            if energy_source:
                fields["energy_source"] = _field(
                    energy_source,
                    0.78,
                    "immoscout_text_energy_source",
                )

        if "energy_class" not in fields:
            energy_class = _search_patterns(
                text,
                [
                    r"Energieeffizienzklasse\s*[:\-]?\s*([A-H][+]*)",
                ],
            )
            if energy_class:
                fields["energy_class"] = _field(
                    energy_class,
                    0.80,
                    "immoscout_text_energy_class",
                )

        if "postal_code" not in fields or "city" not in fields:
            postal_code, city = self._extract_postal_code_and_city(text)

            if postal_code and "postal_code" not in fields:
                fields["postal_code"] = _field(
                    postal_code,
                    0.75,
                    "immoscout_text_postal_city",
                )

            if city and "city" not in fields:
                fields["city"] = _field(
                    city,
                    0.75,
                    "immoscout_text_postal_city",
                )

        return fields

    def _extract_title(self, text: str) -> str | None:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            first_line = lines[0]
            if len(first_line) >= 8:
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