import openmeteo_requests
from openmeteo_sdk.Variable import Variable
import requests_cache
from flask import Flask, request, render_template
from geopy.geocoders import Nominatim

app = Flask(__name__)

def get_weather_data(place):
    # Initialize geolocator to get latitude and longitude from place name
    loc = Nominatim(user_agent="WeatherApp")
    getLoc = loc.geocode(place)
    
    if not getLoc:
        return {"error": f"Could not find location: {place}"}

    # Prepare Open Meteo API request
    openmeteo = openmeteo_requests.Client()
    params = {
        "latitude": getLoc.latitude,
        "longitude": getLoc.longitude,
        "hourly": ["temperature_2m", "precipitation", "wind_speed_10m"],
        "current": ["temperature_2m", "relative_humidity_2m"]
    }

    # Get weather data from Open Meteo API
    responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
    response = responses[0]

    # Extracting weather data
    current = response.Current()
    current_variables = list(map(lambda i: current.Variables(i), range(0, current.VariablesLength())))
    
    current_temperature_2m = next(filter(lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2, current_variables))
    current_relative_humidity_2m = next(filter(lambda x: x.Variable() == Variable.relative_humidity and x.Altitude() == 2, current_variables))

    # Prepare result data
    result = {
        "place": place,
        "latitude": getLoc.latitude,
        "longitude": getLoc.longitude,
        "current_time": current.Time(),
        "current_temperature_2m": current_temperature_2m.Value(),
        "current_relative_humidity_2m": current_relative_humidity_2m.Value(),
        "coordinates": f"{getLoc.latitude}°N, {getLoc.longitude}°E",
        "elevation": response.Elevation(),
        "timezone": response.Timezone(),
        "timezone_abbreviation": response.TimezoneAbbreviation(),
        "utc_offset_seconds": response.UtcOffsetSeconds()
    }
    
    return result

@app.route("/", methods=["GET", "POST"])
def index():
    output = None
    if request.method == "POST":
        place = request.form.get("place")
        if place:
            output = get_weather_data(place)
        else:
            output = {"error": "Please enter a valid place."}
    
    return render_template('index.html', output=output)

if __name__ == "__main__":
    app.run(debug=True)
