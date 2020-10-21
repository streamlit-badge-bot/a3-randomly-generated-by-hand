import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk
import matplotlib.pyplot as plt
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import string
from wordcloud import WordCloud
import json

import business_weekday_plot

st.set_option('deprecation.showPyplotGlobalUse', False)

st.title("Let's analyze some Yelp Restaurant Data 🍽📊.")

@st.cache  

# add caching so we load the data only once
def load_data(json_file):
    return pd.read_json(json_file, lines=True)


# Loading data, use partially selected portions for review and user. 

business_df = load_data(json_file = "../yelp_dataset/yelp_academic_dataset_business.json")
review_df = pd.read_csv("../yelp_dataset/review_pit_restaurant.csv").drop("Unnamed: 0", axis=1)
checkin = load_data(json_file = "../yelp_dataset/yelp_academic_dataset_checkin.json")
user_df = pd.read_csv("../yelp_dataset/user_top_500k.csv").drop("Unnamed: 0", axis=1)


# masked = business_df[lambda x: x["city"]=="Pittsburgh"][lambda x: x["categories"].str.contains("Restaurant", na=False)]

# Select the city you want to explore.

cities = business_df.groupby(["city"]).count()[lambda x: x["categories"]>1000].index


city = st.selectbox("Choose your favorite city", cities)

city_masked = business_df[lambda x: x["city"]==city][lambda x: x["categories"].str.contains("Restaurant", na=False)]

# Select type of cuisine 

cuisine = st.selectbox(
    'Select your favorite food',
    ('Anything', 'Mexican', 'Korean', 'Chinese', 'Pizza', 'American', 'Dessert', 'Salad', 'Burgers', 'Indian'))

attribute_list = ("delivery", "take-out", "parking", "vegetarian", "vegan", "WiFi")

city_cuisine_masked = city_masked
if cuisine != "Anything":
    city_cuisine_masked = city_masked[city_masked["categories"].str.contains(cuisine, na=True)]

# Select Business attributes

options = list(range(len(attribute_list)))

attributes = st.multiselect("attributes", options, format_func=lambda x: attribute_list[x])

def attributeFinder(value_dict, attribute):
    try:
        if value_dict.get(attribute,False) not in ["No", "no", False]:
            return True
    except:
        return False
    return False

city_cuisine_attribute_masked = city_cuisine_masked
for value in attributes:
    city_cuisine_attribute_masked = city_cuisine_attribute_masked[city_masked["attributes"].apply(lambda x: attributeFinder(x, attribute_list[value]))]

# Plot the map

# Adding code so we can have map default to the center of the data
midpoint = (np.average(city_masked['latitude']), np.average(city_masked['longitude']))

layer = pdk.Layer(
    'ScatterplotLayer',
    data=city_cuisine_attribute_masked,
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
    layers=[ layer
    ],
    tooltip={
        "html": "<b>address:</b> {address}"
        "<br/> <b>name:</b> {name}"
        " <br/> <b>stars:</b> {stars} ",
        "style": {"color": "white"},
    },
))

# Select the restaurant

restaurant = st.selectbox(
    'Select your restaurant',
    city_cuisine_attribute_masked["name"].to_list())

business_id = city_cuisine_attribute_masked[city_cuisine_attribute_masked["name"]==restaurant]["business_id"].values[0]

checkin_parsed = business_weekday_plot.dateParser(checkin, business_id)

weekday = "Monday"
checkin_df = business_weekday_plot.getCheckinByHour(checkin_parsed, weekday, business_id)

st.markdown("Checkin counts by hour for day: "+weekday)
st.bar_chart(checkin_df)

## Visualization 2: What type of cuisines are we likely to find in this city?

unique_categories = dict()

stop_words = ["Food", "Grocery", "Restaurants", "Nightlife"]

def findUniqueCategory(row):
    values = row.split(", ")
    for i in values: 
        if i not in stop_words:
            unique_categories[i] = unique_categories.get(i, 0)+1

city_masked["categories"].apply(lambda x: findUniqueCategory(x))

#Only return top 10 categories
unique_categories = pd.Series(pd.Series(unique_categories)).sort_values(ascending=False).head(10)

fig1, ax1 = plt.subplots()
ax1.pie(unique_categories, labels=unique_categories.index, autopct='%1.1f%%', startangle=90)
ax1.axis('equal')  

st.pyplot()


# Visualization 3: What word(s) are most frequently used to describe different cuisine types?


# Select type of cuisine 

unique_categories = dict()
pit_business_df = business_df[lambda x: x["city"]=="Pittsburgh"][lambda x: x["categories"].str.contains("Restaurant", na=False)]

tokens = dict()

tknzr = TweetTokenizer()

common_keywords = ["good", "place", "food", "restaurant", "service", "like", "also", "one", "menu", "get", 
"would", "...", "order", "ordered", "time", "really", "us", "go", "i've", "i'm", "before", "well", "back"
"try", "great", "little", "got", "nice", "even", "could", "came", "much"]


def tokenizer_wrapper(row):
    stop = stopwords.words('english') + list(string.punctuation) + common_keywords
    tmp = [i for i in tknzr.tokenize(row.lower()) if i not in stop]
    for word in tmp:
        tokens[word] = tokens.get(word, 0) + 1

categories = ['Mexican', 'Korean', 'Chinese', 'Pizza', 'American', 'Dessert', 'Salad', 'Burgers', 'Indian']

review_cuisine = st.selectbox(
    'Select your favorite food for reviews analysis',
    ["Choose One"] + categories)


if review_cuisine != 'Choose One':
    pit_business_df = pit_business_df[pit_business_df["categories"].str.contains(review_cuisine, na=True)]


    if st.checkbox("Show Review Wordcloud of cuisine type: " + review_cuisine):

        # Tokenize the review text, Will only work on Pittsburgh
        # For the sake of computation time, I only took the reviews with at least 10 vote counts

        # COMMENT: Would be better to use TF-IDF to actually extract category-specific keywords, but for simplicity, we manually created common words to remove

        pit_cuisine_business_df = pit_business_df[pit_business_df["categories"].str.contains(review_cuisine, na=True)]

        selected_businesses = pit_cuisine_business_df["business_id"].unique()

        review_business_masked = review_df[lambda x: x["business_id"].isin(selected_businesses)]

        review_business_masked["vote_total"] = review_business_masked["useful"] + review_business_masked["funny"] + review_business_masked["cool"]

        review_business_masked = review_business_masked[lambda x: x["vote_total"]>10]

        review_business_masked["text"].apply(lambda x: tokenizer_wrapper(x))

        tokens = pd.Series(tokens).sort_values(ascending=False).head(50)

        wc = WordCloud().fit_words(tokens)

        st.image(wc.to_array())



# Visualization 4: How engaging are top reviewers for diners looking to research restaurants?
# I could not get time data for users => changed to reviews

# st.write(user_df.head())

review_df["date"] = pd.to_datetime(review_df["date"])[lambda x: x.dt.year >= 2010].dt.date

review_df = review_df.sort_values(by="date")

review_votes_by_date = review_df.groupby(["date"]).sum()[["useful", "funny", "cool"]].reset_index()

review_voted_dict = list()

def helper(row):
    for votetype in ["useful", "funny", "cool"]:
        tmp = dict()
        tmp["type"] = votetype
        tmp["votes"] = row[votetype]
        tmp["date"] = row["date"]
        review_voted_dict.append(tmp)

review_votes_by_date.apply(lambda x: helper(x), axis=1)

pivoted = pd.DataFrame(review_voted_dict)

st.write(pivoted)

streamgraph = alt.Chart(pivoted).mark_area().encode(
    alt.X('date:T',
        axis=alt.Axis(format='%Y', domain=False, tickSize=0)
    ),
    alt.Y('votes:Q', stack='normalize', axis=None),
    alt.Color('type:N',
        scale=alt.Scale(scheme='category20b')
    )
).interactive()

st.altair_chart(streamgraph, use_container_width=True)


# Is there a relationship between how “funny”,“cool”, “useful”, etc. people find reviewers’ comments and the star ratings reviewers give a restaurant?


pit_cuisine_business_df = pit_business_df[pit_business_df["categories"].str.contains("Pizza", na=True)]

selected_businesses = pit_cuisine_business_df["business_id"].unique()

review_business_masked = review_df[lambda x: x["business_id"].isin(selected_businesses)]

review_business_masked["vote_total"] = review_business_masked["useful"] + review_business_masked["funny"] + review_business_masked["cool"]


star_range=st.slider("Range of stars", 0, 5, (0,5))

star_range = list(range(star_range[0], star_range[1]+1))

review_votes_stars = review_business_masked[lambda x: x["vote_total"]>10][["useful", "funny", "cool", "stars"]][lambda x: x["stars"].isin(star_range)]

votetypes = ("useful", "funny", "cool")

# options = list(range(len(votetypes)))

types_chosen = st.multiselect("Choose vote types",  votetypes, votetypes)

base = alt.Chart(review_votes_stars).mark_point(filled=True).encode(y='stars')

st.write(review_votes_stars)

colors = {"useful": "green", "cool": "blue", "funny": "red"}

#fix later

alt.layer(
    base.mark_point(color=colors["useful"]).encode(x="useful"),
    base.mark_point(color=colors["cool"]).encode(x="cool"),
    base.mark_point(color=colors["funny"]).encode(x="funny")
)

base
