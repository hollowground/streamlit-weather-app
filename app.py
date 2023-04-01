import streamlit as st
import json
import pandas as pd
import plotly.express as px
import requests
import os
import time


with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if not os.path.exists("locations.json"):
    with open("locations.json", "w") as file:
        data = []
        json.dump(data, file)


def get_locations_list():
    with open("locations.json", "r") as file:
        locations_list = json.load(file)
    return locations_list


locations_list = get_locations_list()


if "locations_list" not in st.session_state:
    st.session_state.locations_list = get_locations_list()


def city_selector():
    selected_city = ""
    locations_list = st.session_state.locations_list
    while True:
        results = ["", "Add new location"]
        for item in locations_list:
            if f"{item['city']}, {item['state']}" not in results:
                results.append(f"{item['city']}, {item['state']}")
            results.sort()

        return results


if "city_list" not in st.session_state:
    st.session_state.city_list = city_selector()


def city_select_droplist(city, state):
    st.session_state.city_list.append(f"{city}, {state}")




def get_lon_lat(city, state):
    for item in locations_list:
        if item["city"] == city and item["state"] == state:
            lon = item["lon"]
            lat = item["lat"]
    return [lat, lon]


weather_list = []
weather_dict = {}


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
        return f"Error: {str(e)}"
    weather_points_json = weather_points_json.json()

    forecast_url = weather_points_json["properties"]["forecast"]
    forecast_json = requests.get(forecast_url)
    try:
        forecast_json.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return f"Error: {str(e)}"
    forecast_json = forecast_json.json()
    forecast_days = forecast_json["properties"]["periods"]
    
    for metric in forecast_days:
        weather_list.append(metric["temperature"])
        temp = {metric["name"].capitalize(): metric["temperature"]}
        weather_dict.update(temp)
    df = pd.DataFrame(list(weather_dict.items()), columns=['Day', 'Temperature'])
    df.set_index('Day', inplace=True)
    #st.line_chart(df)

    fig = px.line(
        df,
        y = "Temperature"
        
    )
    fig.update_layout(
        title =  dict(text="7 Day Forecast", font=dict(size=25), y=0.9, x=0.5, xanchor="auto", yanchor="top")
    )
    col1, col2 = st.columns(2)

    first_key, first_value = next(iter(weather_dict.items()))
    iter_items = iter(weather_dict.items())
    next(iter_items)
    second_key, second_value = next(iter_items) 

    col1.metric(first_key, value=f"{str(first_value)} °F")
    col2.metric(second_key, value=f"{str(second_value)} °F")
    st.plotly_chart(fig, theme="streamlit")        

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
            + "°F" #day["temperatureUnit"]
            + " "
            + day["detailedForecast"]
        )


def add_location():
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
                with open("locations.json", "w") as file:
                    file.write(json.dumps(locations_list, indent=2))
                city_select_droplist(city, state)
                st.experimental_rerun()         
            except requests.exceptions.HTTPError as e:
                return f"Error: {str(e)}"

                
                



def drop_list():
    return st.selectbox("Select or Add Your City:", city_selector())


def main():
    st.title("7 Day Weather Forecast :sunglasses:")

    start_time = time.time()
    response = drop_list()
    if response == "Add new location":
        add_location()
        #get_weather(add_loc_city, add_loc_state)
    else:
        while response not in ["Add new location", ""]:
            user_choice = response.split(",", 1)[0]

            for item in locations_list:
                if item["city"] == user_choice:
                    city = item["city"]
                    state = item["state"]

            get_weather(city, state)
            break

    end_time = time.time()
    st.markdown(f"Total time to run: {str(end_time - start_time)}")


if __name__ == "__main__":
    main()
