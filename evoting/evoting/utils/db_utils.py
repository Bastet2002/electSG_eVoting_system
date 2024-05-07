from pymongo import MongoClient
from django.conf import settings

def get_db_handle():
    db_client = MongoClient(
        host=settings.MONGO_DATABASE['host'],
        port=settings.MONGO_DATABASE['port'],
        username=settings.MONGO_DATABASE['username'],
        password=settings.MONGO_DATABASE['password']
    )
    db_handle = db_client[settings.MONGO_DATABASE['name']]
    return db_handle

def close_db_handle(db_client):
    db_client.close()
