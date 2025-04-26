from uuid import UUID, uuid4
import uuid
from google.auth.transport import requests
import google.oauth2.id_token
from fastapi import Request
from google.cloud import firestore
import starlette.status as status

from models import User, UserProfileUpdateInput


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

            