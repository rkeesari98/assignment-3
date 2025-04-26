from fastapi import Request, UploadFile
from google.cloud import firestore,storage

import local_constants
class FileService:


    

    @staticmethod
    async def upload_file(request: Request,file_name:UploadFile):

        try:
            content_type = file_name.content_type
            allowed_types = ["image/jpeg", "image/png"]
            if content_type not in allowed_types:
                raise Exception("please upload only jpeg or png files")
            await FileService.addFile(file_name)
        except Exception as e:
            print("in service")
            print(e)
            raise Exception(str(e))
        

    @staticmethod
    async def addFile(file)->None:
        try:
            storage_client = storage.Client(project=local_constants.PROJECT_NAME)
            bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
            blob = storage.Blob(file.filename, bucket)
            blob.upload_from_file(file.file)
        except Exception as e:
            raise Exception(e)
        

        
