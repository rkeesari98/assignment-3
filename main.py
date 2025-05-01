from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import FastAPI, File, HTTPException, Request,Form, Depends, Response, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from pydantic import ValidationError
import starlette.status as status
from fastapi.responses import RedirectResponse
from comment_service import CommentService
from file_service import FileService
from models import CommentInput, PostInput, User, UserProfileUpdateInput
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
            data = UserService.get_posts(user)
            print(user)
            return templates.TemplateResponse(
            "home.html",
            {"request":request,"user":user,"newly_created_user":newly_created_user,"posts":data}
        )
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    except Exception as e:
        print('chikki')
        print(e)
        return templates.TemplateResponse(
            "login.html",
            {"request":request,"user":None}
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
    

@app.get("/profile/{username}",response_class=HTMLResponse)
def profile(request:Request,username:str):
    try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
        if username == 'self':
            data = UserService.get_all_posts(user,user.Username)
            print(data)
        else:
            data = UserService.get_all_posts(user,username)
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "posts": data['posts'],
                "is_own_profile": data['is_own_profile'],
                "user": user,
                "profile": data['profile'],
                "profile_username": data['profile_username'],
                "profile_name": data['profile_username'],
                "bio": data['bio'],
                "profile_pic_url":data['profile']['Profile_Pic_Url'],
                "is_following": data['is_following']
            }
        )
    except Exception as e:
        print('exception bro')
        print(e)


@app.get('/images/{file_name}',response_class=Response)
async def get_image(request:Request,file_name:str):
    print(f"file name it {file_name}")
    try:
        logged_in_user = UserService.validate_session_and_fetch_user(request)
        if logged_in_user:
            if file_name.startswith("file_name="):
                file_name = file_name[10:]
                return await FileService.download_file(file_name)
            return await FileService.download_file(file_name)
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    

@app.post("/follow/{follow_user_username}",response_class=JSONResponse)
def follow_user(request:Request,follow_user_username:str):
    try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
        UserService.follow_user(user,follow_user_username)
        return { "success": True, "message": "User followed successfully" }
    except Exception as e:
        return { "success": False, "message": str(e) }
    

@app.delete("/follow/{follow_user_username}",response_class=JSONResponse)
def un_follow_user(request:Request,follow_user_username:str):
    try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
        UserService.unfollow_user(user,follow_user_username)
        return { "success": True, "message": "User followed successfully" }
    except Exception as e:
        return { "success": False, "message": str(e) }
    

@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request):
    try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
        return templates.TemplateResponse("search_users.html", {
        "request": request,
        "mode": "search",
        "users": [],
        "current_user": user,
        "search_placeholder": "Search for users..."
    })
    except Exception as e:
        print(e)
        return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
    

@app.get("/api/search")
async def api_search(request:Request,query: str):
   try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return templates.TemplateResponse(
            "login.html",
            {"request":request}
        )
        users = UserService.search_users(user,query)
        print(users)
        return {"users": users}
   except Exception as e:
       return {"users":None}
   


@app.get("/profile/{username}/followers", response_class=JSONResponse)
def get_followers(request: Request, username: str):
    try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        followers_data = UserService.get_followers(user, username)
        print(followers_data)
        return JSONResponse(followers_data)
    except Exception as e:
        print(e)
        return JSONResponse({"error": str(e)}, status_code=500)
    



@app.get("/profile/{username}/following", response_class=JSONResponse)
def get_following(request: Request, username: str):
    try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        following_data = UserService.get_following(user, username)
        return JSONResponse(following_data)
    except Exception as e:
        print(e)
        return JSONResponse({"error": str(e)}, status_code=500)
    


@app.get('/posts/{post_id}/comments',response_class=JSONResponse)
def get_comments(request:Request,post_id):
    print("hit atleasst")
    try:
        user = UserService.validate_session_and_fetch_user(request)
        if user is None:
            return templates.TemplateResponse(
                "login.html",
                {"request":request,"user":None}
            )
        comments = CommentService.get_comments(post_id)
        return {"comments":comments}
    except Exception as e:
        return {"status": False, "message": f"Failed to fetch comment: {str(e)}"}
    


@app.post("/posts/{post_id}/comments", response_class=JSONResponse)
def post_comment(request: Request, post_id: UUID, comment_input: CommentInput):
    try:
        current_user = UserService.validate_session_and_fetch_user(request)
        if not current_user:
            return templates.TemplateResponse("main.html", {
                "request": request,
                "user": None
            })

        CommentService.create_comment(current_user, post_id, comment_input)

        return JSONResponse({
            "success": True,
            "comment": {
                "username": current_user.Username,
                "text": comment_input.text,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        })

    except Exception as error:
        
        print("[API] Comment posting error:", error)
        return JSONResponse({
            "success": False,
            "message": f"Unable to add comment: {str(error)}"
        })



@app.get('/post/{post_id}',response_class=HTMLResponse)
def get_post_by_id(request:Request,post_id:str):
    try:
        current_user = UserService.validate_session_and_fetch_user(request)
        if not current_user:
            return templates.TemplateResponse("login.html", {
                "request": request,
            })
        data = PostService.get_post(current_user, post_id)
        print(data)
        return templates.TemplateResponse(
            "post_detail.html", {
                "request": request,
                "post": {
                    "Id": data['Id'],
                    "Username": data["Username"],
                    "User_Pic": data["User_Pic"],
                    "Image_ref": data["Image_ref"],
                    "Caption": data["Caption"],
                    "Date": data["Date"],
                    "Comments": data['Comments']
                },
                "user":current_user
            })
    except Exception as e:
        print(e)
        raise Exception(e)