from flask import Flask, render_template, request
import requests
import json
from keys import ACCUWEATHER_API_KEY

app = Flask(__name__)

ACCU_BASE = "http://dataservice.accuweather.com"
ACCU_SEARCH_URL = f"{ACCU_BASE}/locations/v1/cities/search"
ACCU_FORECAST_URL = f"{ACCU_BASE}/forecasts/v1/daily/5day/"
OPEN_METEO_AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def get_location_data(city_name):
    params = {'apikey': ACCUWEATHER_API_KEY, 'q': city_name}
    try:
        response = requests.get(ACCU_SEARCH_URL, params=params)
        data = response.json()
        if data and len(data) > 0:
            result = data[0]
            key = result.get('Key')
            name = result.get('LocalizedName') + ", " + result.get('AdministrativeArea', {}).get('ID')
            lat = result.get('GeoPosition', {}).get('Latitude')
            lon = result.get('GeoPosition', {}).get('Longitude')
            return key, lat, lon, name
        return None, None, None, None
    except:
        return None, None, None, None


def get_weather_forecast(location_key):
    url = f"{ACCU_FORECAST_URL}{location_key}"
    params = {'apikey': ACCUWEATHER_API_KEY, 'details': 'true', 'metric': 'false'}
    try:
        return requests.get(url, params=params).json()
    except:
        return None


def get_pollen_forecast(lat, lon):
    params = {
        'latitude': lat, 'longitude': lon,
        'daily': 'grass_pollen_sum,ragweed_pollen_sum',
        'timezone': 'auto', 'forecast_days': 5
    }
    try:
        return requests.get(OPEN_METEO_AIR_URL, params=params).json()
    except:
        return None


def analyze_data(weather_data, pollen_data):
    results = []
    daily_weather = weather_data.get('DailyForecasts', [])

    om_daily = pollen_data.get('daily', {})
    grass_pollen = om_daily.get('grass_pollen_sum', [])
    ragweed_pollen = om_daily.get('ragweed_pollen_sum', [])

    for i in range(len(daily_weather)):
        w_day = daily_weather[i]
        date_str = w_day['Date'].split('T')[0]
        rain_prob = w_day['Day'].get('PrecipitationProbability', 0)

        total_pollen = 0
        if i < len(grass_pollen) and grass_pollen[i] is not None:
            total_pollen += grass_pollen[i]
        if i < len(ragweed_pollen) and ragweed_pollen[i] is not None:
            total_pollen += ragweed_pollen[i]

        if total_pollen > 50:
            pollen_risk = "High"
        elif total_pollen > 5:
            pollen_risk = "Moderate"
        else:
            pollen_risk = "Low"

        is_good = (rain_prob < 30) and (pollen_risk != "High")

        results.append({
            'date': date_str,
            'rain_pct': rain_prob,
            'pollen': f"{pollen_risk} ({total_pollen:.1f} grains)",
            'recommendation': "Good to Wash" if is_good else "Wait"
        })
    return results


def find_best_wash_day(forecasts):
    if not forecasts or len(forecasts) < 2:
        return None

    future_days = forecasts[1:]

    for i in range(len(future_days) - 2):
        if (future_days[i]['recommendation'] == "Good to Wash" and
                future_days[i + 1]['recommendation'] == "Good to Wash" and
                future_days[i + 2]['recommendation'] == "Good to Wash"):
            return future_days[i]['date'], True

    for i in range(len(future_days) - 1):
        if (future_days[i]['recommendation'] == "Good to Wash" and
                future_days[i + 1]['recommendation'] == "Good to Wash"):
            return future_days[i]['date'], True
    for day in future_days:
        if day['recommendation'] == "Good to Wash":
            return day['date'], False

    return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city_input = request.form.get("city")
        loc_key, lat, lon, city_name = get_location_data(city_input)

        if not loc_key:
            return render_template("wisewash_index.html", error="City not found.")

        weather_resp = get_weather_forecast(loc_key)
        pollen_resp = get_pollen_forecast(lat, lon)

        if not weather_resp:
            return render_template("wisewash_index.html", error="Error retrieving Weather data.")
        if not pollen_resp: pollen_resp = {}

        forecast_results = analyze_data(weather_resp, pollen_resp)

        verdict = "NO"
        best_day = None
        is_streak = False

        if forecast_results and forecast_results[0]['recommendation'] == "Good to Wash":
            verdict = "YES"
            days_to_check = min(3, len(forecast_results))
            for i in range(days_to_check):
                if forecast_results[i]['rain_pct'] >= 60:
                    verdict = "NO"
                    break

        if verdict == "NO":
            result = find_best_wash_day(forecast_results)
            if result:
                best_day, is_streak = result

        return render_template("wisewash_results.html",
                               city=city_name,
                               verdict=verdict,
                               best_day=best_day,
                               is_streak=is_streak,
                               forecasts=forecast_results)

    return render_template("wisewash_index.html")

if __name__ == "__main__":
    app.run(debug=True)