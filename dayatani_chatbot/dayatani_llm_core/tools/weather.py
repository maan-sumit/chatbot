import requests
import json
import os
from langchain.tools import StructuredTool
from collections import defaultdict
import json
from dayatani_llm_core.constant import (
    WEATHER_LAT_LON_DESC,
    WEATHER_PLACE_DESC,
)


def get_api_response(latitude, longitude, place, type):
    api_key = os.environ["OPENWEATHERMAP_API_KEY"]
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"appid": api_key, "units": "metric"}

    # customize request based on place name or cordinate
    if type == "CORDINATE":
        params["lat"] = latitude
        params["lon"] = longitude
    elif type == "PLACE":
        params["q"] = place

    response = requests.get(base_url, params=params)
    data = response.json()
    return data


def get_average(sum, total):
    return round(sum / total, 2)


def parse_weather_data(data):
    if data == None:
        return {'message':'something went wrong'}
    elif data['cod'] != '200':
        return json.dumps(data)
    
    weather_info = defaultdict(lambda: defaultdict(list))
    for item in data["list"]:
        date = item["dt_txt"].split()[0]
        time = item["dt_txt"].split()[1]
        weather = item["weather"][0]
        main = item["main"]
        wind = item["wind"]
        clouds = item["clouds"]["all"]

        weather_info[date]["status"].append(
            {
                "time": time,
                "status": weather["description"],
                "temperature": main["temp"],
            }
        )

        weather_info[date]["wind_speed"].append(wind["speed"])
        weather_info[date]["humidity"].append(main["humidity"])
        weather_info[date]["temp"].append(main["temp"])
        weather_info[date]["cloud_cover"].append(clouds)

    parsed_weather_info = {}
    for date, info in weather_info.items():
        avg_wind_speed = get_average(sum(info["wind_speed"]), len(info["wind_speed"]))
        avg_humidity = get_average(sum(info["humidity"]), len(info["humidity"]))
        avg_temp = get_average(sum(info["temp"]), len(info["temp"]))
        avg_cloud_cover = get_average(
            sum(info["cloud_cover"]), len(info["cloud_cover"])
        )

        parsed_weather_info[date] = {
            "avg_wind_speed": avg_wind_speed,
            "avg_humidity": avg_humidity,
            "avg_temp": avg_temp,
            "avg_cloud_cover": avg_cloud_cover,
            "status": info["status"],
        }

    city_info = data["city"]
    return json.dumps(
        {
            "city": {
                "id": city_info["id"],
                "name": city_info["name"],
                "coordinates": city_info["coord"],
                "country": city_info["country"],
                "population": city_info["population"],
                "timezone": city_info["timezone"],
                "sunrise": city_info["sunrise"],
                "sunset": city_info["sunset"],
            },
            "weather": parsed_weather_info,
        }
    )


def get_weather(latitude: int, longitude: int) -> str:
    data = get_api_response(
        latitude=latitude, longitude=longitude, place=None, type="CORDINATE"
    )
    weather_info = parse_weather_data(data)
    return weather_info


def get_weather_by_location_name(place):
    data = get_api_response(latitude=None, longitude=None, place=place, type="PLACE")
    weather_info = parse_weather_data(data)
    return weather_info


def weather_search_by_lat_lon(latitude: float, longitude: float) -> str:
    return get_weather(latitude=latitude, longitude=longitude)


def weather_search_by_place(place_name: str) -> str:
    return get_weather_by_location_name(place=place_name)


weather_search_by_lat_lon_tool = StructuredTool.from_function(
    weather_search_by_lat_lon, description=f"""{WEATHER_LAT_LON_DESC}"""
)
weather_search_by_place_tool = StructuredTool.from_function(
    weather_search_by_place, description=f"""{WEATHER_PLACE_DESC}"""
)
