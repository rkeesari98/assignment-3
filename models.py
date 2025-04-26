from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel


class User(BaseModel):
    Username: str
    Display_Name: Optional[str]
    Followers:List[Dict] = Optional
    Following:List[Dict] = Optional
    Email: str
    Profile_Pic: Optional[str]
    About: Optional[str]
    Id: UUID
    
class Post:
    Id: UUID


class UserProfileUpdateInput(BaseModel):
    username: str
    profile_name: str
    bio: Optional[str]
    profile_pic_url:Optional[str]