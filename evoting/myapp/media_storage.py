from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
import os

def select_storage():
    if os.environ.get('USE_S3') == 'TRUE':
        return S3Boto3Storage(
            access_key=settings.STORAGES['default']['OPTIONS']['AWS_ACCESS_KEY_ID'],
            secret_key=settings.STORAGES['default']['OPTIONS']['AWS_SECRET_ACCESS_KEY'],
            bucket_name=settings.STORAGES['default']['OPTIONS']['AWS_STORAGE_BUCKET_NAME'],
            region_name=settings.AWS_S3_REGION_NAME,
            file_overwrite=settings.STORAGES['default']['OPTIONS']['AWS_S3_FILE_OVERWRITE'],
            location=settings.STORAGES['default']['OPTIONS']['AWS_LOCATION'],
            querystring_expire=settings.STORAGES['default']['OPTIONS']['AWS_QUERYSTRING_EXPIRE'],
            object_parameters=settings.AWS_S3_OBJECT_PARAMETERS
        )
    return default_storage