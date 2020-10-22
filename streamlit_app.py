import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk

from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import string
from wordcloud import WordCloud
import json


import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import business_weekday_plot

# [TODO] put a divider in between each viz

st.set_option('deprecation.showPyplotGlobalUse', False)

st.title("What are some opportunities to present useful information for users researching restaurants on Yelp?")

st.markdown("The following data visualizations help a Yelp product team explore different factors that influence \
    a diner's restaurant research journey: Restaurant characteristics (such as location, peak hours), and reviews \
    from Yelp community.")

st.markdown("Analysis done by: Seungmyung Lee (seungmyl) and Eileen Wang (eileenwa)")

# @st.cache  

# Loading data, use partially selected portions for review and user. 

business_df = pd.read_csv("./yelp_dataset/business_filtered.csv")
review_df = pd.concat([pd.read_csv("./yelp_dataset/review_filtered-1.csv"), pd.read_csv("./yelp_dataset/review_filtered-2.csv")])
checkin = pd.concat([pd.read_csv("./yelp_dataset/checkin_filtered-1.csv"),pd.read_csv("./yelp_dataset/checkin_filtered-2.csv")])


st.header("Part 1: Restaurant Characteristics")
st.markdown("The information that falls in this category describes the operational side of restaurants and the kind of food they serve. When users start their research journey, they could be presented with a large quantity of options in a city. Considering different restaurant characteristics is a necessary step users take to narrow down on options and not feel overwhelmed. Below two questions explores a few restaurant characteristics")
st.markdown("----------------------------------------------------------------------")


## Visualization 1: What type of cuisines are we likely to find in this city?
st.markdown("Visualization 1: What type of cuisines are we likely to find in this city?")

cities = list(business_df.groupby(["city"]).count().sort_values(by="categories", ascending=False).head(10).index)

city = st.selectbox("Choose your favorite city", cities)

city_masked = business_df[lambda x: x["city"]==city][lambda x: x["categories"].str.contains("Restaurant", na=False)]

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
print(mcolors.TABLEAU_COLORS)
ax1.pie(unique_categories, labels=unique_categories.index, autopct='%1.1f%%', startangle=90, colors=mcolors.TABLEAU_COLORS)
ax1.axis('equal')  

st.pyplot()

st.markdown("----------------------------------------------------------------------")

# Visualization 2

st.markdown("Visualization 2: Peak hours at a restaurant on selected weekday.")
cities = list(business_df.groupby(["city"]).count().sort_values(by="categories", ascending=False).head(10).index)

city = st.selectbox("Choose your favorite city to explore.", cities)

city_masked = business_df[lambda x: x["city"]==city][lambda x: x["categories"].str.contains("Restaurant", na=False)]

# Select type of cuisine 

cuisine = st.selectbox(
    'Select your favorite food',
    ('Anything', 'Mexican', 'Korean', 'Chinese', 'Pizza', 'American', 'Dessert', 'Salad', 'Burgers', 'Indian'))

attribute_list = ("delivery", "take-out", "parking", "vegetarian", "vegan", "WiFi")

city_cuisine_masked = city_masked
if cuisine != "Anything":
    city_cuisine_masked = city_masked[city_masked["categories"].str.contains(cuisine, na=True)]


checkin["count"] = checkin["date"].apply(lambda x: len(x.split(", ")))

checkin_masked_business_ids = checkin[lambda x: x["count"]>1000]["business_id"]

# Select the restaurant


restaurant = st.selectbox(
    'Select your restaurant',
    city_cuisine_masked[lambda x: x["business_id"].isin(checkin_masked_business_ids)]["name"].to_list())


if restaurant != None:

    business_id = city_cuisine_masked[city_cuisine_masked["name"]==restaurant]["business_id"].values[0]

    checkin_parsed = business_weekday_plot.dateParser(checkin, business_id)


    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    weekday = st.selectbox("Select a weekday.", weekdays)
    checkin_df = business_weekday_plot.getCheckinByHour(checkin_parsed, weekday, business_id)

    st.markdown("Checkin counts by hour for day: "+weekday)
    st.bar_chart(checkin_df)
else:
    st.markdown("Sorry, there are no "+ cuisine +" restaurants in city "+ city + ". Please choose a different cuisine.")

st.markdown("----------------------------------------------------------------------")


st.header("Part 2: Looking at Reviews from Yelp Community")

st.markdown("----------------------------------------------------------------------")


st.markdown("Visualization 3: What word(s) are most frequently used words to describe different cuisine types?")

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

st.markdown("----------------------------------------------------------------------")

st.markdown("Visualization 4: How has user appreciation for “cool”, “useful”, and “funny” reviews changed over the years?")

# Visualization 4: How engaging are top reviewers for diners looking to research restaurants?
# I could not get time data for users => changed to reviews


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

streamgraph = alt.Chart(pivoted).mark_area().encode(
    alt.X('date:T',
        axis=alt.Axis(format='%Y', domain=False, tickSize=0)
    ),
    alt.Y('votes:Q', stack='normalize', axis=None),
    alt.Color('type:N',
        scale=alt.Scale(scheme='tableau10')
    )
).interactive()

st.altair_chart(streamgraph, use_container_width=True)


st.markdown("----------------------------------------------------------------------")

st.markdown("Visualization 5: Is there a relationship between adjectives users vote on and the star rating given to a restaurant?")
# Is there a relationship between how “funny”,“cool”, “useful”, etc. people find reviewers’ comments and the star ratings reviewers give a restaurant?


selected_businesses = business_df[business_df["categories"].str.contains("Pizza", na=True)]["business_id"].unique()

review_business_masked = review_df[lambda x: x["business_id"].isin(selected_businesses)]

review_business_masked["vote_total"] = review_business_masked["useful"] + review_business_masked["funny"] + review_business_masked["cool"]



vote_range = st.slider("Range of Vote Counts", 0, 80, (0,80))

vote_range = list(range(vote_range[0], vote_range[1]+1))

review_votes_stars = review_business_masked[lambda x: x["vote_total"]>10][["useful", "funny", "cool", "stars"]][lambda x: x["useful"].isin(vote_range)][lambda x: x["funny"].isin(vote_range)][lambda x: x["cool"].isin(vote_range)]


base_list = list()
colors = {"useful": "green", "cool": "blue", "funny": "red"}

base = alt.Chart(review_votes_stars).encode(
    y='stars:Q',
)

base.mark_point(color=colors["useful"]).encode(x="useful:Q"),

base.mark_point(color=colors["cool"]).encode(x="cool:Q"),

base.mark_point(color=colors["funny"]).encode(x="funny:Q"),

