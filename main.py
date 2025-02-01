from typing import Union

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from mock import MOCK_SEARCH_BUS_STOP_RESPONSE
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import aiohttp
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/nearby-bus-stops")
async def get_nearby_bus_stops(latitude: float | None = None, longitude: float | None = None, radius: int | None = 500, type: str | None = "bus_stop"):
    if latitude is None or longitude is None:
        return {"error": "Latitude and longitude are required"}
    try:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={type}&key={GOOGLE_API_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return {"error": f"API request failed with status {response.status}"}
                data = await response.json()
                return data
    except aiohttp.ClientError as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@app.get("/bus-stops")
async def get_bus_stops(busStopName: str | None = None, latitude: float | None = None, longitude: float | None = None, radius: int | None = 500, type: str | None = "bus_stop"):
    print(f"busStopName: {busStopName}")
    return MOCK_SEARCH_BUS_STOP_RESPONSE

