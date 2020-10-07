import pandas as pd
import datetime

input_json_checkin = "../yelp_dataset/yelp_academic_dataset_checkin.json"
businessid= "--9e1ONYQuAa-CB_Rrw7Tw"

def load(input_json):
    return pd.read_json(input_json, lines = True)

def dateParser(df, businessid):
    df_parsed = pd.DataFrame(checkin.loc[df['business_id']==businessid].date.iloc[0].split(", "), columns=["date"])
    df_parsed["date"] = pd.to_datetime(df_parsed["date"])

    df_parsed["weekday"] = df_parsed["date"].dt.day_name()
    df_parsed["hour"] = df_parsed["date"].dt.hour

    return df_parsed

def getCheckinByHour(df, weekday, businessid):
    return df[df["weekday"]==weekday].groupby("hour").count()["date"]


checkin = load(input_json_checkin)
checkin_parsed = dateParser(checkin, businessid)

getCheckinByHour(checkin_parsed, "Monday", businessid)

