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