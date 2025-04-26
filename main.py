from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, HTTPException, Request,Form, Depends, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from pydantic import ValidationError
import starlette.status as status
from fastapi.responses import RedirectResponse
from file_service import FileService
from models import PostInput, User, UserProfileUpdateInput
from post_service import PostService
from user_service import UserService
import datetime

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
    

@app.get('/post/create',response_class=HTMLResponse)
def post_create(request:Request):
    try:
        user = UserService.validate_session_and_fetch_user(request)
        logged_in_user = UserService.validate_session_and_fetch_user(request)
        if logged_in_user:
            return templates.TemplateResponse(
            "post_creation.html",
            {"request":request}
        )
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    

@app.post('/upload-file',response_class=JSONResponse)
async def upload_file(request:Request,file_name: UploadFile = File(...)):
    try:
        print(file_name)
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
        await FileService.upload_file(request,file_name)
        return JSONResponse(content={"status": True, "filename": file_name.filename}) 
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500,content={"error": str(e)})
    
@app.post('/post')
def post_create(request:Request,post_input:PostInput):
    try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return JSONResponse(
                status_code=401,
                content={"status": False, "error": "Authentication required"}
            )
        post = PostService.post_create(user,post_input)
        post_json = post.dict()
        post_json['Id'] = str(post_json['Id'])
        if isinstance(post_json['Date'], datetime.datetime):
            post_json['Date'] = post_json['Date'].isoformat()
        return JSONResponse(content={"status": True, "post": post_json}) 
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={"status": False, "error": str(e)}
        )