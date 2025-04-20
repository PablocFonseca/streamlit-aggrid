import random
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware

import datetime as dt

# Seed for reproducibility
random.seed(42)

# Define a starting day for the date generation
start_day = dt.date(1980, 1, 1)  # Example: January 1, 2025


# Generate a fixed list of names and ages
def generate_random_data(start, count):
    with open("weather_stations.txt") as f:
        cities = [line.strip() for line in f.readlines()]  # Strip newline characters

    num_cities = len(cities)

    # Precompute the data for the requested range
    data = []
    for i in range(start, start + count):
        city_index = i % num_cities  # Use modular arithmetic to avoid cycling
        city = cities[city_index]
        date = (start_day + dt.timedelta(days=i // num_cities)).isoformat()
        temperature = random.normalvariate(30, 10)  # Generate temperature
        data.append(
            dict(
                row=i,
                date=date,
                city=city,
                temperature=temperature,
            )
        )
    return data


def get_data(start, count):
    # Use a fixed random seed for reproducibility
    random.seed(42 + start)  # Adjust seed based on start to ensure determinism
    return generate_random_data(start, count)


async def get_records(request):
    """
    Returns a slice of the data list based on the start index and count.
    """
    start = int(request.query_params.get("start", 0))
    count = int(request.query_params.get("count", 100))
    return JSONResponse(get_data(start, count))


app = Starlette(
    routes=[
        Route("/records/", get_records),
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# uvicorn simpleServer:app --host 0.0.0.0 --port 8080 --reload
