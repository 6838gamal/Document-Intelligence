from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="DocIQ Admin Panel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/js", StaticFiles(directory="js"), name="js")


@app.get("/")
async def root():
    return FileResponse("login.html")


@app.get("/login")
async def login():
    return FileResponse("login.html")


@app.get("/dashboard")
async def dashboard():
    return FileResponse("index.html")


@app.get("/config.js")
async def config():
    return FileResponse("config.js")
