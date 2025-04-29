from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel


class User(BaseModel):
    Username: str
    Display_Name: Optional[str]
    Followers:List[Dict] = Optional
    Following:List[Dict] = Optional
    Email: str
    Profile_Pic_Url: Optional[str]
    Bio: Optional[str]
    Id: UUID
    
class Post(BaseModel):
    Id:UUID
    Username:str
    Quote:str
    Date:Optional[datetime] = None
    Image:str


class UserProfileUpdateInput(BaseModel):
    username: str
    profile_name: str
    bio: Optional[str]
    profile_pic_url:Optional[str]


class PostInput(BaseModel):
    image_ref:str
    caption:str



class Comment(BaseModel):
    PostId:UUID
    Text:str
    Id:UUID
    Username:str
    Date:Optional[datetime] = None


class PostSend(BaseModel):
    Id:UUID
    Username:str
    Quote:str
    Date:Optional[datetime] = None
    Image:str
    Comments: List[Comment] = None
    User_Pic:Optional[str] = None



class PostResponse(BaseModel):
    Id:UUID
    Username:str
    Quote:str
    Date:Optional[datetime] = None
    Image:str
    Comments: List[Comment] = None
    User_Pic:Optional[str] = None



class CommentInput(BaseModel):
    text:str