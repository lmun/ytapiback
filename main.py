from typing import List, Optional, Dict
from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio
from fastapi.middleware.cors import CORSMiddleware
import httpx
from config import YOUTUBE_KEY,MONGODB_URL



app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.yt


class ChannelModel(BaseModel):
    id: str
    snippet: Dict
    contentDetails: Dict
    statistics: Optional[Dict] = {}
    status: Optional[Dict] = {}
    brandingSettings: Optional[Dict] = {}


class VideoModel(BaseModel):
    id: str
    snippet: Dict
    contentDetails: Dict
    status: Dict
    statistics: Optional[Dict]


@app.get("/")
async def root():
    lista_canales = await db["canales"].distinct("id", {"activo": True})
    return lista_canales


@app.get("/canales/all", tags=["canales"], response_model=List[ChannelModel])
async def get_all_channels():
    return await db["canales"].find({"activo": True}).to_list(None)


@app.get(
    "/canales/{channel_id}",
    tags=["canales"],
    response_description="Get a single cannel",
    response_model=ChannelModel,
)
async def get_channel_info(channel_id: str):
    return await db["canales"].find_one({"id": channel_id})


@app.get(
    "/canales/{channel_id}/videos",
    tags=["canales", "videos"],
    response_model=List[VideoModel],
)
async def get_channel_videos(channel_id: str):
    return (
        await db["videos"]
        .find({"snippet.channelId": channel_id, "descargado": True})
        .to_list(None)
    )

@app.get(
    "/canales/{channel_id}/youtube",
    tags=["videos"],
    response_model=List[VideoModel],
)
async def get_channel_videos(channel_id: str):
    clientParams = {
        'key': YOUTUBE_KEY,
        'part': 'snippet,contentDetails,status',
        'playlistId': 'UU'+channel_id[2:],
        'maxResults': 50,
    }
    publicVideos = []
    async with httpx.AsyncClient(params=clientParams) as client:
        reqParams = {}
        while True:
            resp =await client.get('https://www.googleapis.com/youtube/v3/playlistItems',params=reqParams)
            objResp = resp.json()
            try:
                publicVideos.extend(objResp['items'])
            except:
                print(clientParams)
                print(reqParams)
                print(objResp)
            if not objResp.get('nextPageToken', False):
                break
            reqParams['pageToken'] = objResp['nextPageToken']
    return publicVideos

@app.get(
    "/canales/{channel_id}/missing",
    tags=["canales", "videos"],
    response_model=List[VideoModel],
)
async def get_channel_videos(channel_id: str):
    return (
        await db["videos"]
        .find({"snippet.channelId": channel_id, "descargado": {"$ne":True}})
        .to_list(None)
    )