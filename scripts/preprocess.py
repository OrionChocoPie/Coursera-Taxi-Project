import numpy as np
import pandas as pd

from scipy.stats import binned_statistic_2d

regions = pd.read_csv("regions.csv", sep=";")
longitude_bins = (regions["west"].append(regions["east"])).unique()
latitude_bins = (regions["south"].append(regions["north"])).unique()


def preprocessing(date):
    df = pd.read_csv("yellow_tripdata_" + date + ".csv")  # '2016-05'

    # Перевод строки во временные данные
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["trip_distance"] = df["trip_distance"].astype(float)

    # Фильтрация
    df = df[(df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.seconds > 0]
    df = df[df["passenger_count"] > 0]
    df = df[df["trip_distance"] > 0]
    df = df[
        (-74.25559 <= df["pickup_longitude"])
        & (df["pickup_longitude"] <= -73.70001)
        & (40.49612 <= df["pickup_latitude"])
        & (df["pickup_latitude"] <= 40.91553)
    ]

    # Посчитаем номера регионов
    new_regions = binned_statistic_2d(
        df["pickup_longitude"],
        df["pickup_latitude"],
        df["pickup_longitude"],
        bins=[longitude_bins, latitude_bins],
        statistic="count",
        expand_binnumbers=True,
    )

    # Полученные номера регионов присвоим поездкам
    df["region"] = (new_regions.binnumber[0] - 1) * 50 + new_regions.binnumber[1]

    # Удаляем минуты и секунды из времени начала поездки
    df["tpep_pickup_datetime"] = df["tpep_pickup_datetime"].dt.floor("H")

    # Агрегируем данные по часам и регионам
    time_region = pd.crosstab(df["tpep_pickup_datetime"], df["region"])
    # заполняем нулями регионы, в которых нету данных
    for i in range(1, 2501):
        if i not in time_region.columns:
            time_region[i] = 0
    time_region = time_region[sorted(time_region.columns)]

    time_region.to_csv("time_region_" + date + ".csv")


from os import listdir
from os.path import isfile, join
import re

files = [
    f for f in listdir(".") if isfile(join(".", f)) and f.startswith("yellow_tripdata")
]

preprocessing("2016-07")
# for file in files:
#     date = re.split('_|\.', file)[-2]
#     preprocessing(date)