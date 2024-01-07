import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import json
import os
import time

CSS_FILE_PATH = "css/styles.css"
LOCATIONS_FILE_PATH = "data/locations.json"


@st.cache_data
def load_styles():
    """Load the custom css styles for the app"""
    with open(CSS_FILE_PATH) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def check_locations_file_exists():
    """Check if the locations file exists, if not create one"""
    if not os.path.exists(LOCATIONS_FILE_PATH):
        with open(LOCATIONS_FILE_PATH, "w") as file:
            data = []
            json.dump(data, file)


def get_locations_list():
    """Load the locations file for selecting the different weather locations"""
    with open(LOCATIONS_FILE_PATH, "r") as file:
        locations_list = json.load(file)
    return locations_list


def city_selector():
    """Will return the City, State from the locations to be used in the drop list"""
    locations_list = st.session_state.locations_list
    while True:
        results = ["", "Add new location"]
        for item in locations_list:
            if f"{item['city']}, {item['state']}" not in results:
                results.append(f"{item['city']}, {item['state']}")
            results.sort()

        return results


def city_select_droplist(city, state):
    """Will append City, State to the session state"""
    st.session_state.city_list.append(f"{city}, {state}")


def get_lon_lat(city, state, locations_list):
    """Will return the Long and Lat for the City, State that is passed from the locations list"""
    for item in locations_list:
        if item["city"] == city and item["state"] == state:
            lon = item["lon"]
            lat = item["lat"]
    return [lat, lon]


def fetch_weather_data(lat, lon):
    """Fetch weather data from the API based on latitude and longitude."""
    weather_gov_points_url = f"https://api.weather.gov/points/{lat},{lon}"
    try:
        response = requests.get(weather_gov_points_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Error fetching weather data: {str(e)}")
        return None


def fetch_forecast_data(forecast_url):
    """Fetch forecast data from the API."""
    try:
        response = requests.get(forecast_url)
        response.raise_for_status()
        return response.json()["properties"]["periods"]
    except requests.exceptions.HTTPError as e:
        st.error(f"Error fetching forecast data: {str(e)}")
        return None


def process_weather_data(forecast_days):
    """Process the raw forecast data and return a DataFrame."""
    weather_dict = {
        day["name"].capitalize(): day["temperature"] for day in forecast_days
    }
    df = pd.DataFrame(list(weather_dict.items()), columns=["Day", "Temperature"])
    df.set_index("Day", inplace=True)
    return df


def display_weather_metrics(weather_dict):
    """Display weather metrics using Streamlit."""
    col1, col2 = st.columns(2)

    first_key, first_value = next(iter(weather_dict.items()))
    iter_items = iter(weather_dict.items())
    next(iter_items)
    second_key, second_value = next(iter_items)

    col1.metric(first_key, value=f"{str(first_value)} °F")
    col2.metric(second_key, value=f"{str(second_value)} °F")


def display_weather_chart(df):
    """Display the weather chart using Plotly Express."""
    fig = px.line(df, y="Temperature", text="Temperature")
    fig.update_traces(textposition="middle right")
    fig.update_layout(
        title=dict(
            text="7 Day Forecast",
            font=dict(size=25),
            y=0.95,
            x=0.5,
            xanchor="auto",
            yanchor="top",
        )
    )
    st.plotly_chart(fig, theme="streamlit")


def display_detailed_forecast(forecast_days, city, state):
    """Display detailed forecast information."""
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
            + "°F"  # day["temperatureUnit"]
            + " "
            + day["detailedForecast"]
        )


def get_weather(city, state, locations_list):
    """Get weather forecast based on the City, State from the locations list."""
    geo_coordinates = get_lon_lat(city, state, locations_list)
    geo_lat_coordinate, geo_lon_coordinate = geo_coordinates

    weather_data = fetch_weather_data(geo_lat_coordinate, geo_lon_coordinate)
    if weather_data is None:
        return

    forecast_url = weather_data["properties"]["forecast"]
    forecast_days = fetch_forecast_data(forecast_url)
    if forecast_days is None:
        return

    weather_dict = {
        day["name"].capitalize(): day["temperature"] for day in forecast_days
    }
    df = process_weather_data(forecast_days)

    display_weather_metrics(weather_dict)
    display_weather_chart(df)
    display_detailed_forecast(forecast_days, city, state)


def add_location():
    """Will add new City, State locations to the locations list and update the session state."""
    locations_list = get_locations_list()
    with st.sidebar.form(key="new_location_form", clear_on_submit=True):
        city = st.text_input("Enter in the city:", "City ...")
        state = st.text_input(
            "Enter in the two character state code:", "State Code ex. NY ..."
        )
        responses = {"city": city, "state": state}

        geo_json = {}
        geo_coding_url = (
            f"https://nominatim.openstreetmap.org/search?q={city}%20{state}&format=json"
        )
        if add_location_button := st.form_submit_button(label="Add Location"):
            try:
                geo_json = requests.get(geo_coding_url)
                geo_json.raise_for_status()
                geo_json = geo_json.json()
                geo_lon_coordinate = geo_json[0]["lon"]
                geo_lat_coordinate = geo_json[0]["lat"]

                responses.update(
                    {"lon": str(geo_lon_coordinate), "lat": str(geo_lat_coordinate)}
                )
                locations_list.append(responses)
                st.session_state.locations_list.append(responses)
                with open("data/locations.json", "w") as file:
                    file.write(json.dumps(locations_list, indent=2))
                city_select_droplist(city, state)
                st.experimental_rerun()
            except requests.exceptions.HTTPError as e:
                return f"Error: {str(e)}"


def drop_list():
    """Will display the City, State drop list for the application"""
    return st.selectbox("Select or Add Your City:", city_selector())


def main(locations_list):
    """The main function to add new locations and return the weather based on the City, State selected."""
    st.title("7 Day Weather Forecast :sunglasses:")

    start_time = time.time()
    response = drop_list()
    if response == "Add new location":
        add_location()
    else:
        while response not in ["Add new location", ""]:
            user_choice = response.split(",", 1)[0]

            for item in locations_list:
                if item["city"] == user_choice:
                    city = item["city"]
                    state = item["state"]

            get_weather(city, state, locations_list)
            break

    end_time = time.time()
    st.markdown(f"Total time to run: {str(end_time - start_time)}")
