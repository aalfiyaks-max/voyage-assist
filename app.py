from flask import Flask, render_template, request, jsonify
import requests
import random

app = Flask(__name__)

# YOUR REAL API KEYS (already added)
GEOAPIFY_KEY = "2b80aa516b454887bb3816f37e26e3cf"
WEATHER_KEY = "d04cc341df07bbb1f59a836d909bec58"
UNSPLASH_KEY = "m7Zwrf7etJSlKaHX-d6nG6L3wr6X6sF0d3I7W_t6TdM"


@app.route("/")
def home():
    return render_template("index.html")


# ================= SEARCH =================

@app.route("/search", methods=["POST"])
def search():

    city = request.json.get("city", "")
    budget = request.json.get("budget", "medium")

    # Budget radius
    if budget == "low":
        radius = 5000
    elif budget == "medium":
        radius = 15000
    else:
        radius = 30000


    # GET COORDINATES
    geo_url = f"https://api.geoapify.com/v1/geocode/search?text={city}&limit=1&apiKey={GEOAPIFY_KEY}"
    geo = requests.get(geo_url).json()

    if not geo.get("features"):
        return jsonify({"error": "City not found"})

    lat = geo["features"][0]["properties"]["lat"]
    lon = geo["features"][0]["properties"]["lon"]


    # GET IMAGES
    img_url = f"https://api.unsplash.com/search/photos?query={city}&per_page=30&client_id={UNSPLASH_KEY}"
    img_data = requests.get(img_url).json()

    images = []

    for img in img_data.get("results", []):
        images.append(img["urls"]["small"])

    if not images:
        images.append(
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"
        )


    # FETCH FUNCTION
    def fetch(category):

        url = (
            f"https://api.geoapify.com/v2/places?"
            f"categories={category}"
            f"&filter=circle:{lon},{lat},{radius}"
            f"&bias=proximity:{lon},{lat}"
            f"&limit=8"
            f"&apiKey={GEOAPIFY_KEY}"
        )

        data = requests.get(url).json()

        results = []

        for place in data.get("features", []):

            prop = place["properties"]

            if not prop.get("name"):
                continue

            results.append({

                "name": prop["name"],
                "address": prop.get("formatted", ""),
                "lat": prop["lat"],
                "lon": prop["lon"],
                "image": random.choice(images)

            })

        return results


    places = fetch("tourism.attraction,tourism.sights")
    hotels = fetch("accommodation.hotel")
    restaurants = fetch("catering.restaurant")


    # WEATHER
    weather_url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
    )

    weather = requests.get(weather_url).json()

    temp = "N/A"
    desc = "Unavailable"
    humidity = "N/A"
    wind = "N/A"
    icon = ""

    if "main" in weather:

        temp = weather["main"]["temp"]
        humidity = weather["main"]["humidity"]
        desc = weather["weather"][0]["description"]
        wind = weather["wind"]["speed"]
        icon = weather["weather"][0]["icon"]


    return jsonify({

        "places": places,
        "hotels": hotels,
        "restaurants": restaurants,

        "lat": lat,
        "lon": lon,

        "temp": temp,
        "desc": desc,
        "humidity": humidity,
        "wind": wind,
        "icon": icon

    })


# ================= AI TRIP PLANNER =================

@app.route("/plan_trip", methods=["POST"])
def plan_trip():

    city = request.json.get("city", "")
    days = int(request.json.get("days", 3))

    geo_url = f"https://api.geoapify.com/v1/geocode/search?text={city}&limit=1&apiKey={GEOAPIFY_KEY}"
    geo = requests.get(geo_url).json()

    lat = geo["features"][0]["properties"]["lat"]
    lon = geo["features"][0]["properties"]["lon"]

    url = (
        f"https://api.geoapify.com/v2/places?"
        f"categories=tourism.attraction"
        f"&filter=circle:{lon},{lat},20000"
        f"&limit=15"
        f"&apiKey={GEOAPIFY_KEY}"
    )

    data = requests.get(url).json()

    places = []

    for place in data.get("features", []):
        name = place["properties"].get("name")
        if name:
            places.append(name)


    itinerary = []

    per_day = max(1, len(places)//days)

    index = 0

    for d in range(days):

        itinerary.append({

            "day": d+1,
            "places": places[index:index+per_day]

        })

        index += per_day


    return jsonify({

        "city": city,
        "plan": itinerary

    })


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

