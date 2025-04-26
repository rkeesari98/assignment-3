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
from models import User, UserProfileUpdateInput
from user_service import UserService


app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()


app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/",response_class=HTMLResponse)
def root(request:Request):
    try:
        newly_created_user = UserService.add_user_to_firestore(request)
        print(newly_created_user)
        user:User = UserService.validate_session_and_fetch_user(request)
        if user :
            if user.Username == 'Assignment - 3':
                newly_created_user = True
            return templates.TemplateResponse(
            "home.html",
            {"request":request,"user":user,"newly_created_user":newly_created_user}
        )
        raise Exception("Invalid Login")
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    
@app.get("/login",response_class=HTMLResponse)
def root(request:Request):
    try:
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    

@app.post('/update/user',response_class=JSONResponse)
def update_user(request:Request,user_profile_input:UserProfileUpdateInput):
    try:
        print('hit')
        logged_in_user = UserService.validate_session_and_fetch_user(request)
        if logged_in_user:
            UserService.update_user(logged_in_user,user_profile_input)
            return JSONResponse(
                status_code=200,
                content={
                    "status": True,
                    "message": "User profile updated successfully."
                }
            )
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": False,
                "error": str(e)
            }
        )