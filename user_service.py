import datetime
from uuid import UUID, uuid4
import uuid
from google.auth.transport import requests
import google.oauth2.id_token
from fastapi import Request
from google.cloud import firestore
from pydantic import Json
import starlette.status as status

from models import Comment, PostSend, User, UserProfileUpdateInput


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
            raise Exception(str(error))
        

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
            raise Exception(str(err))

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
                "Profile_Name": profile_name.lower()
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

            # Fetch profile user once outside loop
            user_result = firestore_db.collection("User").where("Username", "==", profile_username).limit(1).stream()
            user_docs = list(user_result)
            user_info = user_docs[0].to_dict() if user_docs else {}

            for doc in post_docs:
                post_data = doc.to_dict()

                # Convert UUID to string
                post_data["Id"] = str(post_data.get("Id", ""))
                post_data["Date"] = post_data.get("Date")

                post_instance = PostSend(**post_data)
                post_instance.User_Pic = user_info.get("Profile_Pic", "default_user.jpeg")

                # Convert date to isoformat if it's a datetime object
                if isinstance(post_instance.Date, datetime.datetime):

                    post_instance.Date = post_instance.Date.isoformat()

                # Fetch comments for post
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
            # Normalize the search term
            normalized_term = search_term.lower()
            search_range_end = normalized_term + u'\uf8ff'

            # Reference the user collection and apply the range query on Profile_Name
            user_collection = firestore_db.collection('User')
            matching_users = user_collection \
                .where("Profile_Name", ">=", normalized_term) \
                .where("Profile_Name", "<=", search_range_end) \
                .stream()

            results = []

            # Prepare a set of usernames the current user is already following
            followed_usernames = set(
                entry.get("Username") for entry in user.Following
            ) if user.Following else set()

            for doc in matching_users:
                user_data = doc.to_dict()
                candidate_username = user_data.get("Username", "")

                # Skip if the user is the one making the request
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
            # Fetch the user to unfollow from Firestore
            target_snapshot = next(
                firestore_db.collection("User")
                .where("Username", "==", target_username)
                .stream(),
                None
            )

            if not target_snapshot:
                raise Exception("The specified user does not exist.")

            target_user = User(**target_snapshot.to_dict())

            # Filter out the target user from the current user's following list
            current_user.Following = [
                entry for entry in current_user.Following 
                if entry.get("Username") != target_username
            ]

            # Filter out the current user from the target user's followers list
            target_user.Followers = [
                entry for entry in target_user.Followers 
                if entry.get("Username") != current_user.Username
            ]

            # Commit updates to Firestore
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
