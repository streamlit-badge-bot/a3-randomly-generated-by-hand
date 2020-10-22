import pandas as pd
import datetime


def load(input_json):
    return pd.read_json(input_json, lines = True)

def dateParser(df, businessid):
    df_parsed = pd.DataFrame(df.loc[df['business_id']==businessid].date.iloc[0].split(", "), columns=["date"])
    df_parsed["date"] = pd.to_datetime(df_parsed["date"])

    df_parsed["weekday"] = df_parsed["date"].dt.day_name()
    df_parsed["hour"] = df_parsed["date"].dt.hour

    return df_parsed

def getCheckinByHour(df, weekday, businessid):
    return df[df["weekday"]==weekday].groupby("hour").count()["date"]
