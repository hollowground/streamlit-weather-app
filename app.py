import streamlit as st
from pprint import pprint
import json
import random
import requests
import time


# @st.cache
def get_locations_list():
    with open("locations.json", "r") as file:
        locations_list = json.load(file)
    return locations_list


locations_list = get_locations_list()


if "locations_list" not in st.session_state:
    st.session_state.locations_list = get_locations_list()
# st.write(st.session_state.locations_list)


def city_selector():
    while True:
        results = []
        selected_city = ""
        results.append("")
        results.append("Add new location")
        locations_list = st.session_state.locations_list  # get_locations_list()
        for item in locations_list:
            if f"{item['city']}, {item['state']}" not in results:
                results.append(f"{item['city']}, {item['state']}")
            results.sort()

        return results


if "city_list" not in st.session_state:
    st.session_state.city_list = city_selector()
# st.write(st.session_state.city_list)


# response = st.selectbox("Select your city:", city_selector(), key="city_state")


def city_select_droplist(city, state):
    st.session_state.city_list.append(f"{city}, {state}")
    # st.session_state[city] = state


def add_location():
    with st.sidebar.form(key="new_location_form", clear_on_submit=True):
        address = st.text_input("Enter in the street address:", "Address ...")
        city = st.text_input("Enter in the city:", "City ...")
        state = st.text_input(
            "Enter in the two character state code:", "State Code ex. NY ..."
        )
        zip = st.text_input("Enter in the zip code:", "Zip Code ...")
        add_location_button = st.form_submit_button(label="Add Location")

    responses = {"address": address, "city": city, "state": state, "zip": zip}

    geo_json = {}
    geo_coding_url = f"https://geocoding.geo.census.gov/geocoder/locations/address?street={address}&city={city}&state={state}&benchmark=2020&format=json"
    geo_json = requests.get(geo_coding_url)

    try:
        geo_json.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return "Error: " + str(e)
    geo_json = geo_json.json()
    geo_lon_coordinate = geo_json["result"]["addressMatches"][0]["coordinates"]["x"]
    geo_lat_coordinate = geo_json["result"]["addressMatches"][0]["coordinates"]["y"]

    responses.update({"lon": str(geo_lon_coordinate), "lat": str(geo_lat_coordinate)})
    # locations_list = get_locations_list()
    locations_list.append(responses)
    st.session_state.locations_list.append(responses)
    with open("locations.json", "w") as file:
        file.write(json.dumps(locations_list, indent=2))
    city_select_droplist(city, state)
    st.experimental_rerun()
    # return f"{city}"


def get_lon_lat(city, state):
    coordinates = []
    # locations_list = get_locations_list()
    for item in locations_list:
        if item["city"] == city and item["state"] == state:
            lon = item["lon"]
            lat = item["lat"]
    coordinates.append(lat)
    coordinates.append(lon)
    return coordinates


def get_weather(city, state):

    geo_coordinates = get_lon_lat(city, state)
    geo_lat_coordinate = geo_coordinates[0]
    geo_lon_coordinate = geo_coordinates[1]
    weather_gov_points_url = (
        f"https://api.weather.gov/points/{geo_lat_coordinate},{geo_lon_coordinate}"
    )
    weather_points_json = requests.get(weather_gov_points_url)

    try:
        weather_points_json.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return "Error: " + str(e)
    weather_points_json = weather_points_json.json()

    forecast_url = weather_points_json["properties"]["forecast"]
    # forecast_hourly_url = weather_points_json["properties"]["forecastHourly"]

    forecast_json = requests.get(forecast_url)
    try:
        forecast_json.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return "Error: " + str(e)
    forecast_json = forecast_json.json()

    #  This section will be used for the hourly forecast
    # forecast_hourly_json = requests.get(forecast_hourly_url)
    # try:
    #    forecast_hourly_json.raise_for_status()
    # except requests.exceptions.HTTPError as e:
    #    return "Error: " + str(e)
    # forecast_hourly_json = forecast_hourly_json.json()

    forecast_days = forecast_json["properties"]["periods"]

    for day in forecast_days:
        st.markdown(
            ":palm_tree: "
            + day["name"].capitalize()
            + " in "
            + city
            + ", "
            + state
            + " "
            + str(day["temperature"])
            + " "
            + day["temperatureUnit"]
            + " "
            + day["detailedForecast"]
        )


def drop_list():
    return st.selectbox("Select your city:", city_selector())


def main():
    st.title("7 Day Weather Forecast")

    start_time = time.time()
    # locations_list = get_locations_list()

    response = drop_list()
    if response == "Add new location":
        # user_choice = add_location()
        add_location()
        # response = drop_list(random.randint(1, 100))
        # st.experimental_rerun()
    else:
        while response != "Add new location" and response != "":
            user_choice = response.split(",", 1)[0]

            for item in locations_list:
                if item["city"] == user_choice:
                    address = item["address"]
                    city = item["city"]
                    state = item["state"]
                    zip = item["zip"]

            get_weather(city, state)
            break

    end_time = time.time()
    st.markdown("Total time to run: " + str(end_time - start_time))


if __name__ == "__main__":
    main()
