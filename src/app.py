import streamlit as st
from utils.helpers import (
    load_styles,
    check_locations_file_exists,
    city_selector,
    get_locations_list,
    main,
)


if __name__ == "__main__":
    load_styles()
    check_locations_file_exists()
    locations_list = get_locations_list()
    if "locations_list" not in st.session_state:
        st.session_state.locations_list = get_locations_list()
    if "city_list" not in st.session_state:
        st.session_state.city_list = city_selector()
    main(locations_list)
