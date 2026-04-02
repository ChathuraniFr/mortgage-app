import streamlit as st

from property_models import PropertyListing


PROPERTY_STATE_KEY = "saved_properties"


def initialize_property_storage() -> None:
    if PROPERTY_STATE_KEY not in st.session_state:
        st.session_state[PROPERTY_STATE_KEY] = []


def get_saved_properties() -> list[PropertyListing]:
    initialize_property_storage()
    return st.session_state[PROPERTY_STATE_KEY]


def save_property(listing: PropertyListing) -> None:
    initialize_property_storage()

    existing_ids = {item.external_id for item in st.session_state[PROPERTY_STATE_KEY]}
    if listing.external_id not in existing_ids:
        st.session_state[PROPERTY_STATE_KEY].append(listing)


def save_many_properties(listings: list[PropertyListing]) -> int:
    initialize_property_storage()

    count_before = len(st.session_state[PROPERTY_STATE_KEY])

    for listing in listings:
        save_property(listing)

    count_after = len(st.session_state[PROPERTY_STATE_KEY])
    return count_after - count_before


def remove_property(external_id: str) -> None:
    initialize_property_storage()

    st.session_state[PROPERTY_STATE_KEY] = [
        item
        for item in st.session_state[PROPERTY_STATE_KEY]
        if item.external_id != external_id
    ]


def clear_properties() -> None:
    st.session_state[PROPERTY_STATE_KEY] = []