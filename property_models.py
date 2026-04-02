from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class PropertyListing:
    source: str
    external_id: str
    title: str
    city: str
    postal_code: Optional[str]
    address: Optional[str]
    price_eur: float
    living_area_sqm: Optional[float]
    plot_area_sqm: Optional[float]
    rooms: Optional[float]
    year_built: Optional[int]
    property_type: Optional[str]
    house_subtype: Optional[str] = None
    condition: Optional[str] = None
    heating_type: Optional[str] = None
    energy_source: Optional[str] = None
    energy_class: Optional[str] = None
    has_cellar: Optional[bool] = None
    has_garage: Optional[bool] = None
    has_parking_space: Optional[bool] = None
    additional_costs_eur: Optional[float] = None
    url: str = ""
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "PropertyListing":
        return PropertyListing(
            source=data.get("source", "unknown"),
            external_id=str(data.get("external_id", "")),
            title=data.get("title", ""),
            city=data.get("city", ""),
            postal_code=data.get("postal_code"),
            address=data.get("address"),
            price_eur=float(data.get("price_eur", 0.0)),
            living_area_sqm=(
                float(data["living_area_sqm"])
                if data.get("living_area_sqm") not in (None, "")
                else None
            ),
            plot_area_sqm=(
                float(data["plot_area_sqm"])
                if data.get("plot_area_sqm") not in (None, "")
                else None
            ),
            rooms=(
                float(data["rooms"])
                if data.get("rooms") not in (None, "")
                else None
            ),
            year_built=(
                int(data["year_built"])
                if data.get("year_built") not in (None, "")
                else None
            ),
            property_type=data.get("property_type"),
            house_subtype=data.get("house_subtype"),
            condition=data.get("condition"),
            heating_type=data.get("heating_type"),
            energy_source=data.get("energy_source"),
            energy_class=data.get("energy_class"),
            has_cellar=data.get("has_cellar"),
            has_garage=data.get("has_garage"),
            has_parking_space=data.get("has_parking_space"),
            additional_costs_eur=(
                float(data["additional_costs_eur"])
                if data.get("additional_costs_eur") not in (None, "")
                else None
            ),
            url=data.get("url", ""),
            description=data.get("description"),
        )