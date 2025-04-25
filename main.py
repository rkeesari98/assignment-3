from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request,Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from pydantic import ValidationError
import starlette.status as status
from fastapi.responses import RedirectResponse


app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()


app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/",response_class=HTMLResponse)
def root(request:Request):
    try:
        return JSONResponse({
            "demo":"demo"
        })
    except Exception as e:
        pass