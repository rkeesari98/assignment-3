import datetime
from typing import Dict, List
from uuid import UUID, uuid4
import uuid
from google.auth.transport import requests
import google.oauth2.id_token
from fastapi import Request
from google.cloud import firestore
from pydantic import Json
import starlette.status as status

from models import Comment, Post, PostResponse, PostSend, User, UserProfileUpdateInput


firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

class UserService:


    @staticmethod
    def add_user_to_firestore(req: Request) -> bool:
        session_token = req.cookies.get("token")
        if not session_token:
            return None

        try:
            decoded_token = google.oauth2.id_token.verify_firebase_token(session_token, firebase_request_adapter)
            if not decoded_token:
                return None

            user_email = decoded_token.get("email")
            if not user_email:
                return None

            user_collection = firestore_db.collection("User")
            matched_users = user_collection.where("Email", "==", user_email).limit(1).stream()

            user_exists = any(matched_users)
            if not user_exists:
                new_user_id = str(uuid.uuid4())
                user_data = {
                    "Id": new_user_id,
                    "Email": user_email,
                    "Username": "Assignment - 3",
                    "Followers": [],
                    "Following": [],
                    "About": "This is my me by default",

                }
                user_collection.document(new_user_id).set(user_data)
                return True

            return False

        except Exception as error:
            print("error in user creation logic")
            print(str(error))
            
        

    @staticmethod
    def validate_session_and_fetch_user(req: Request) -> User:
        auth_cookie = req.cookies.get("token")
        if not auth_cookie:
            return None

        try:
            verified_claims = google.oauth2.id_token.verify_firebase_token(auth_cookie, firebase_request_adapter)
            if not verified_claims:
                return None

            user_email = verified_claims.get("email")
            if not user_email:
                return None

            user_query = firestore_db.collection("User").where("Email", "==", user_email).limit(1)
            user_snapshot = next(user_query.stream(), None)

            if user_snapshot is None:
                raise Exception("No user record matches the provided email.")

            user_data = user_snapshot.to_dict()
            return User(**user_data)

        except Exception as err:
            print(f"Service Failed to fetch : {str(err)}")

    @staticmethod
    def update_user(user: User, profile_data: UserProfileUpdateInput):
        try:
            username = profile_data.username.strip()
            profile_name = profile_data.profile_name.strip()

            if not username or not profile_name:
                raise Exception("Both username and profile name are required.")

            if len(username) < 6 or len(profile_name) < 6:
                raise Exception("Username and profile name must be at least 6 characters long.")
            
            if username=='Assignment - 3':
                raise Exception('Thats the reserved keyword please try uisng different one')

            user_query = firestore_db.collection('User').where('Username', '==', username).get()
            if user_query:
                raise Exception("This username is already in use. Please choose a different one.")

            update_fields = {
                "Username": username.lower(),
                "Profile_Name": profile_name.lower(),
                "Bio": profile_data.bio
            }

            update_fields["Bio"] = profile_data.bio if profile_data.bio is not None else ""
            update_fields["Profile_Pic_Url"] = profile_data.profile_pic_url or "default_user.jpeg"

            firestore_db.collection('User').document(str(user.Id)).update(update_fields)

        except Exception as error:
            print("Error occurred while updating user profile:")
            print(str(error))
            raise Exception(str(error))


    @staticmethod
    def get_all_posts(current_user: User, profile_username: str):
        try:
            post_docs = firestore_db.collection("Post") \
                .where("Username", "==", profile_username) \
                .order_by("Date", direction=firestore.Query.DESCENDING) \
                .stream()

            post_list = []

            user_result = firestore_db.collection("User").where("Username", "==", profile_username).limit(1).stream()
            user_docs = list(user_result)
            user_info = user_docs[0].to_dict() if user_docs else {}

            for doc in post_docs:
                post_data = doc.to_dict()

                post_data["Id"] = str(post_data.get("Id", ""))
                post_data["Date"] = post_data.get("Date")

                post_instance = PostSend(**post_data)
                post_instance.User_Pic = user_info.get("Profile_Pic", "default_user.jpeg")

                if isinstance(post_instance.Date, datetime.datetime):

                    post_instance.Date = post_instance.Date.isoformat()

                comment_query = firestore_db.collection("Comment").where("PostId", "==", str(post_instance.Id)).stream()
                post_instance.Comments = [Comment(**c.to_dict()) for c in comment_query]

                post_list.append(post_instance)
            if not user_info:
                raise Exception("Profile not found.")

            is_following = any(
                entry.get("Username") == profile_username
                for entry in getattr(current_user, "Following", [])
            )

            return {
                "profile": user_info,
                "profile_username": profile_username,
                "profile_name": user_info.get("Display_Name", profile_username),
                "bio": user_info.get("About", ""),
                "profile_pic_url": user_info.get("Profile_Pic", "default_user.jpeg"),
                "is_following": is_following,
                "is_own_profile": current_user.Username == profile_username,
                "posts": post_list,
            }

        except Exception as error:
            print("[UserService] Error in get_all_posts:", error)
            raise Exception(str(error))

    @staticmethod
    def follow_user(user: User, target_username: str) -> Json:
        try:
            target_snapshot = next(
                firestore_db.collection("User").where("Username", "==", target_username).stream(),
                None
            )
            if not target_snapshot:
                raise Exception("The user you are trying to follow does not exist.")

            target_user = User(**target_snapshot.to_dict())

            already_following = any(
                entry.get("Username") == target_username 
                for entry in user.Following
            )
            if already_following:
                raise Exception("You are already following this user.")

            timestamp = datetime.datetime.now().isoformat()
            user.Following.append({"Username": target_username, "Date": timestamp})
            target_user.Followers.append({"Username": user.Username, "Date": timestamp})

            firestore_db.collection("User").document(str(user.Id)).update({
                "Following": user.Following
            })
            firestore_db.collection("User").document(str(target_user.Id)).update({
                "Followers": target_user.Followers
            })

            return {"message": "success"}
        except Exception as error:
            print(f"Error during follow: {error}")
            raise Exception(str(error))


    @staticmethod
    def search_users(user: User, search_term: str):
        try:
            normalized_term = search_term.lower()
            search_range_end = normalized_term + u'\uf8ff'

            user_collection = firestore_db.collection('User')
            matching_users = user_collection \
                .where("Profile_Name", ">=", normalized_term) \
                .where("Profile_Name", "<=", search_range_end) \
                .stream()

            results = []

            followed_usernames = set(
                entry.get("Username") for entry in user.Following
            ) if user.Following else set()

            for doc in matching_users:
                user_data = doc.to_dict()
                candidate_username = user_data.get("Username", "")

                if candidate_username == user.Username:
                    continue

                results.append({
                    "Username": candidate_username,
                    "Profile_Name": user_data.get("Profile_Name", ""),
                    "Bio": user_data.get("Bio", ""),
                    "profile_pic_url": user_data.get("Profile_Pic_Url", "default_user.jpeg"),
                    "is_following": candidate_username in followed_usernames
                })

            return results
        except Exception as err:
            print("Error occurred during user search:", err)
            raise Exception(str(err))



    @staticmethod
    def unfollow_user(current_user: User, target_username: str) -> Json:
        try:
            target_snapshot = next(
                firestore_db.collection("User")
                .where("Username", "==", target_username)
                .stream(),
                None
            )

            if not target_snapshot:
                raise Exception("The specified user does not exist.")

            target_user = User(**target_snapshot.to_dict())

            current_user.Following = [
                entry for entry in current_user.Following 
                if entry.get("Username") != target_username
            ]

            target_user.Followers = [
                entry for entry in target_user.Followers 
                if entry.get("Username") != current_user.Username
            ]

            firestore_db.collection("User").document(str(current_user.Id)).update({
                "Following": current_user.Following
            })

            firestore_db.collection("User").document(str(target_user.Id)).update({
                "Followers": target_user.Followers
            })

            return {"message": "success"}

        except Exception as error:
            print(f"Error while unfollowing: {error}")
            raise Exception(str(error))


    @staticmethod
    def get_followers(current_user: User, profile_username: str):
        try:
            user_result = firestore_db.collection("User").where("Username", "==", profile_username).limit(1).stream()
            user_docs = list(user_result)
            
            if not user_docs:
                raise Exception("User not found")
            
            user_info = user_docs[0].to_dict()
            followers_list = user_info.get("Followers", [])
            
            followers_list.sort(key=lambda x: x.get("Date", 0), reverse=True)
            
            followers_data = []
            for follower in followers_list:
                follower_username = follower.get("Username", "")
                
                follower_doc = next(firestore_db.collection("User").where("Username", "==", follower_username).limit(1).stream(), None)
                if follower_doc:
                    follower_info = follower_doc.to_dict()
                    
                    is_following = any(
                        entry.get("Username") == follower_username
                        for entry in getattr(current_user, "Following", [])
                    )
                    
                    followers_data.append({
                        "username": follower_username,
                        "profile_name": follower_info.get("Profile_Name", follower_username),
                        "profile_pic": follower_info.get("Profile_Pic_Url", "default_user.jpeg"),
                        "is_following": is_following,
                        "timestamp": follower.get("Date", 0)
                    })
            
            return {"followers": followers_data}
        except Exception as error:
            print("[UserService] Error in get_followers:", error)
            raise Exception(str(error))

    @staticmethod
    def get_following(current_user: User, profile_username: str):
        try:

            user_result = firestore_db.collection("User").where("Username", "==", profile_username).limit(1).stream()
            user_docs = list(user_result)
            
            if not user_docs:
                raise Exception("User not found")
            
            user_info = user_docs[0].to_dict()
            following_list = user_info.get("Following", [])
            
            following_list.sort(key=lambda x: x.get("Date", 0), reverse=True)
            
            following_data = []
            for following in following_list:
                following_username = following.get("Username", "")
                
                following_doc = next(firestore_db.collection("User").where("Username", "==", following_username).limit(1).stream(), None)
                if following_doc:
                    following_info = following_doc.to_dict()
                    
                    following_data.append({
                        "username": following_username,
                        "profile_name": following_info.get("Profile_Name", following_username),
                        "profile_pic": following_info.get("Profile_Pic_Url", "default_user.jpeg"),
                         "timestamp": following.get("Date", 0)
                    })
            
            return {"following": following_data}
        except Exception as error:
            print("[UserService] Error in get_following:", error)
            raise Exception(str(error))
        
    

    @staticmethod
    def get_posts(user: User) -> List[Post]:
        try:
            user_snapshot = next(
                firestore_db.collection("User").where("Email", "==", user.Email).stream(), 
                None
            )

            if not user_snapshot:
                raise Exception("User not found.")

            user_data = User(**user_snapshot.to_dict())

            relevant_usernames = [user_data.Username] + [
                entry.get("Username") for entry in user_data.Following or []
            ]

            post_docs = firestore_db.collection("Post") \
                .where("Username", "in", relevant_usernames) \
                .order_by("Date", direction=firestore.Query.DESCENDING) \
                .limit(50) \
                .stream()

            posts = []

            for doc in post_docs:
                post_data = doc.to_dict()
                post = PostResponse(**post_data)

                post.Id = str(post.Id)

                user_profile = firestore_db.collection("User").where("Username", "==", post.Username).limit(1).get()
                if user_profile:
                    post.User_Pic = user_profile[0].to_dict().get("Profile_Pic_Url", "default_user.jpeg")
                else:
                    post.User_Pic = "default_user.jpeg"

                if isinstance(post.Date, datetime.datetime):
                    post.Date = post.Date.isoformat()

                comment_stream = firestore_db.collection("Comment").where("PostId", "==", post.Id).stream()
                post.Comments = [Comment(**c.to_dict()) for c in comment_stream]

                posts.append(post)

            return posts

        except Exception as error:
            print(f"[UserService] Error in get_posts: {error}")
            raise Exception(str(error))
