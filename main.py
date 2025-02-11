from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi_utils.tasks import repeat_every
import aiohttp
import os
import ssl

from mock import MOCK_SEARCH_BUS_STOP_RESPONSE

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加載 .env 檔案
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TDX_CLIENT_ID = os.getenv("TDX_CLIENT_ID")
TDX_CLIENT_SECRET = os.getenv("TDX_CLIENT_SECRET")
api_domain = f"https://tdx.transportdata.tw/api"

# 先定義一個預設值
access_token = None
access_token_expires_in = 3600  # 預設一小時

async def get_access_token():
    url = f"https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": TDX_CLIENT_ID,
        "client_secret": TDX_CLIENT_SECRET
    }
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        async with session.post(url, headers=headers, data=data, ssl=ssl_context) as response:
            data = await response.json()
            return data

# 在應用啟動時獲取 access_token
@app.on_event("startup")
async def startup_event():
    access_token_data = await get_access_token()
    global access_token
    global access_token_expires_in
    access_token = access_token_data.get('access_token')
    access_token_expires_in = access_token_data.get('expires_in')

@app.on_event("startup")
@repeat_every(seconds = access_token_expires_in)
async def refresh_access_token():
    global access_token
    global access_token_expires_in
    access_token_data = await get_access_token()
    access_token = access_token_data.get('access_token')
    access_token_expires_in = access_token_data.get('expires_in')

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
        # url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={type}&key={GOOGLE_API_KEY}"
        # url = f"{api_domain}/advanced/v2/Bus/Station/NearBy?%24top=30&%24spatialFilter=nearby%2825.047675%2C%20121.517055%2C%20100%29&%24format=JSON"
        url = f"{api_domain}/advanced/v2/Bus/Stop/NearBy?$spatialFilter=nearby({latitude},{longitude},{radius})&$format=JSON"
        print(f"url: {url}")
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            async with session.get(url, headers={"Authorization": f"Bearer {access_token}"}) as response:
                if response.status != 200:
                    return {"error": f"API request failed with status {response.status}"}
                data = await response.json()
                print(f"nearby-bus-stops: {data}")
                return data
    except aiohttp.ClientError as e:
        print(f"Network error: {str(e)}")
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

@app.get("/bus-stops")
async def get_bus_stops(busStopName: str | None = None, latitude: float | None = None, longitude: float | None = None, radius: int | None = 500, type: str | None = "bus_stop"):
    print(f"busStopName: {busStopName}")
    return MOCK_SEARCH_BUS_STOP_RESPONSE

