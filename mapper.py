import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk

import business_weekday_plot

st.title("Let's analyze some Yelp Restaurant Data 🍽📊.")

@st.cache  

# add caching so we load the data only once
def load_data(json_file):
    return pd.read_json(json_file, lines=True)

df = load_data(json_file = "../yelp_dataset/yelp_academic_dataset_business.json")

masked = df[lambda x: x["city"]=="Pittsburgh"][lambda x: x["categories"].str.contains("Restaurant", na=False)]


st.write(df.head(100))

cuisine = st.selectbox(
    'Select your favorite food',
    ('Anything', 'Mexican', 'Japanese', 'Chinese', 'Pizza', 'Noodles', 'Dessert'))

display = ("delivery", "take-out", "parking", "vegetarian", "vegan", "WiFi")

options = list(range(len(display)))

attributes = st.multiselect("attributes", options, format_func=lambda x: display[x])

if cuisine != "Anything":
    masked = masked[masked["categories"].str.contains(cuisine, na=True)]

def attributeFinder(value_dict, attribute):
    try:
        if value_dict.get(attribute,False) not in ["No", "no", False]:
            return True
    except:
        return False
    return False

for value in attributes:
    masked = masked[masked["attributes"].apply(lambda x: attributeFinder(x, display[value]))]

st.write(masked)

# Adding code so we can have map default to the center of the data
midpoint = (np.average(masked['latitude']), np.average(masked['longitude']))

layer = pdk.Layer(
    'ScatterplotLayer',
    data=masked,
    get_position='[longitude, latitude]',
    get_color='[200, 30, 0, 160]',
    get_radius=100,
    picakble=True,
    wireframe=True,

)

view_state = pdk.ViewState(
    latitude=midpoint[0],
    longitude=midpoint[1],
    zoom=10,
)

st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=view_state,
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=masked,
            get_position='[longitude, latitude]',
            get_color='[200, 30, 0, 160]',
            get_radius=100,
            pickable=True,
        )
    ],
    tooltip={
        "html": "<b>address:</b> {address}"
        "<br/> <b>name:</b> {name}"
        " <br/> <b>stars:</b> {stars} ",
        "style": {"color": "white"},
    },
))

restaurant = st.selectbox(
    'Select your restaurant',
    masked["name"].to_list())

business_id = masked[masked["name"]==restaurant]["business_id"].values[0]

checkin = load_data(json_file = "../yelp_dataset/yelp_academic_dataset_checkin.json")
checkin_parsed = business_weekday_plot.dateParser(checkin, business_id)

weekday = "Monday"
checkin_df = business_weekday_plot.getCheckinByHour(checkin_parsed, weekday, business_id)

st.write(checkin_df)


st.markdown("Checkin counts by hour for day: "+weekday)
st.bar_chart(checkin_df)
