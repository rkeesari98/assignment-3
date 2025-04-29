import datetime
from models import Post, PostInput, User

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
class PostService:

    @staticmethod
    def post_create(user:User,post_data:PostInput):
        try:
            if len(post_data.caption) > 500:
                raise ValueError("Caption exceeds 500 characters.")

            new_post_id = uuid.uuid4()
            timestamp = datetime.datetime.utcnow().isoformat()

            post_record = Post(
                Id=new_post_id,
                Username=user.Username,
                Quote=post_data.caption,
                Date=timestamp,
                Image=post_data.image_ref
            )

            post_dict = post_record.dict()
            post_dict["Id"] = str(post_record.Id)

            firestore_db.collection("Post").add(post_dict)
            return post_record

        except Exception as exc:
            print("[ Failed to create post:", exc)
            raise Exception(str(exc))
        
    

    @staticmethod
    def get_post(user: User, post_id: UUID):
        try:
            post_query = firestore_db.collection("Post").where("Id", "==", post_id).get()
            if not post_query:
                raise Exception("Post not found")

            post = post_query[0].to_dict()
            post['Id'] = str(post['Id'])

            # Format the date if it's a datetime object
            if isinstance(post.get('Date'), datetime.datetime):
                post['Date'] = post['Date'].isoformat()

            # Attempt to get user's profile picture
            user_query = firestore_db.collection('User').where('Id', '==', post['Username']).limit(1).get()
            if user_query:
                user_data = user_query[0].to_dict()
                profile_pic_url = user_data.get('Profile_Pic_Url', "default_user.jpeg")
            else:
                profile_pic_url = "default_user.jpeg"

            # Fetch associated comments
            comment_query = firestore_db.collection('Comment').where('PostId', '==', post['Id']).stream()
            comment_list = []
            for comment in comment_query:
                data = comment.to_dict()
                data['Id'] = str(data['Id'])
                data['PostId'] = str(data['PostId'])

                if isinstance(data.get('Date'), datetime.datetime):
                    data['Date'] = data['Date'].isoformat()
                comment_list.append(data)

            # Combine all the details into a final dictionary
            result = {
                "Id": post['Id'],
                "Username": post['Username'],
                "User_Pic": profile_pic_url,
                "Image_ref": post['Image'],
                "Caption": post['Quote'],
                "Date": post['Date'],
                "Comments": comment_list
            }

            return result

        except Exception as error:
            print(f"An error occurred in get_post: {str(error)}")
            raise Exception(str(error))


    