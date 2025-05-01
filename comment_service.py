from uuid import UUID
import uuid
from google.cloud import firestore,storage
from google.auth.transport import requests

from models import Comment, CommentInput, User



firestore_db = firestore.Client()
firebase_request_adapter = requests.Request()
class CommentService:

    def change_date(timestamp):
        if timestamp is None:
            return None
            
        if hasattr(timestamp, 'year'):
            return timestamp
        
        try:
            return timestamp.datetime
        except AttributeError:
            try:
                return timestamp.ToDatetime()
            except AttributeError:
                try:
                    import datetime
                    return datetime.datetime.fromtimestamp(timestamp)
                except (TypeError, ValueError):
                    print(f"Could not convert timestamp: {type(timestamp)}")
                    return None


    @staticmethod
    def get_comments(post_id:str):
        try:
            comments_data = firestore_db.collection('Comment').where('PostId', '==', post_id).order_by("Date", direction=firestore.Query.DESCENDING).stream()
            
            comments = []
            for doc in comments_data:
                data = doc.to_dict()
                timestamp = CommentService.change_date(data.get('Date'))
                comment = {
                    "text":data['Text'],
                    "username":data['Username'],
                    "timestamp": timestamp.isoformat() if timestamp else None 
                }
                comments.append(comment)
            
            return comments

        except Exception as e:
            print("in service")
            print(e)
            raise Exception(str(e))
        
    
    @staticmethod
    def create_comment(user: User, post_id: UUID, comment_input: CommentInput) -> None:
        try:
            comment_text = comment_input.text.strip()

            if not comment_text:
                raise ValueError("Comment text cannot be empty.")
            if len(comment_text) > 200:
                raise ValueError("Comment  exceeds 200 characters.")

            new_comment = Comment(
                Id=str(uuid.uuid4()),
                PostId=str(post_id),
                Username=user.Username,
                Text=comment_text,
                Date=None   
            )

            comment_data = new_comment.dict()
            comment_data['Id'] = str(comment_data['Id'])
            comment_data['PostId'] = str(comment_data['PostId'])
            comment_data["Date"] = firestore.SERVER_TIMESTAMP

            firestore_db.collection("Comment").add(comment_data)

        except Exception as err:
            print("[Service] Error while creating comment:", err)
            raise Exception(str(err))